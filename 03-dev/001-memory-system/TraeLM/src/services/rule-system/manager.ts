/**
 * 规则管理器
 * 统一管理规则系统的所有组件
 */

import { EventEmitter } from 'events';
import { Rule, SystemEvent, RuleCategory } from '../../types/base';
import { ConfigurationManager } from '../../config/manager';
import { RuleEngine, RuleContext, RuleExecutionResult } from './engine';
import { RuleProcessor, RuleChain, ConditionalRule, DynamicRuleGenerator } from './processor';

export class RuleManager extends EventEmitter {
  private engine: RuleEngine;
  private processor: RuleProcessor;
  private configManager: ConfigurationManager;
  private isInitialized = false;
  private eventQueue: QueuedEvent[] = [];
  private processingQueue = false;

  constructor(configManager: ConfigurationManager) {
    super();
    this.configManager = configManager;
    this.engine = new RuleEngine();
    this.processor = new RuleProcessor(this.engine);
    this.setupEventListeners();
  }

  /**
   * 初始化规则管理器
   */
  async initialize(): Promise<void> {
    try {
      // 启动规则引擎
      this.engine.start();

      // 加载配置中的规则
      const rules = this.configManager.getRules();
      for (const rule of rules) {
        this.engine.addRule(rule);
      }

      this.isInitialized = true;
      this.emit('initialized');

      // 开始处理队列中的事件
      this.startEventProcessing();
    } catch (error) {
      this.emit('initializationError', error);
      throw error;
    }
  }

  /**
   * 设置事件监听器
   */
  private setupEventListeners(): void {
    // 引擎事件
    this.engine.on('ruleExecuted', (data) => {
      this.emit('ruleExecuted', data);
    });

    this.engine.on('executionError', (data) => {
      this.emit('executionError', data);
    });

    // 处理器事件
    this.processor.on('chainExecuted', (data) => {
      this.emit('chainExecuted', data);
    });

    this.processor.on('conditionalRuleEvaluated', (data) => {
      this.emit('conditionalRuleEvaluated', data);
    });

    this.processor.on('dynamicRulesGenerated', (data) => {
      this.emit('dynamicRulesGenerated', data);
    });

    // 配置管理器事件
    this.configManager.on('ruleAdded', (rule) => {
      this.engine.addRule(rule);
      this.emit('ruleAdded', rule);
    });

    this.configManager.on('ruleUpdated', (rule) => {
      this.engine.updateRule(rule);
      this.emit('ruleUpdated', rule);
    });

    this.configManager.on('ruleRemoved', (rule) => {
      this.engine.removeRule(rule.id);
      this.emit('ruleRemoved', rule);
    });
  }

  /**
   * 处理系统事件
   */
  async processEvent(event: SystemEvent, context: RuleContext = {}): Promise<RuleExecutionResult[]> {
    if (!this.isInitialized) {
      // 如果未初始化，将事件加入队列
      this.eventQueue.push({ event, context, timestamp: new Date() });
      return [];
    }

    try {
      // 增强上下文
      const enhancedContext = await this.enhanceContext(context, event);

      // 执行规则
      const results = await this.engine.processEvent(event, enhancedContext);

      // 处理结果
      await this.processResults(results, event, enhancedContext);

      return results;
    } catch (error) {
      this.emit('eventProcessingError', { event, context, error });
      throw error;
    }
  }

  /**
   * 增强规则上下文
   */
  private async enhanceContext(context: RuleContext, event: SystemEvent): Promise<RuleContext> {
    const enhanced = { ...context };

    // 添加系统信息
    enhanced['system'] = {
      timestamp: new Date(),
      eventId: event.id,
      eventType: event.type,
      source: event.source
    };

    // 添加配置信息
    enhanced['config'] = this.configManager.getSystemConfig();

    // 添加统计信息
    enhanced['stats'] = {
      engine: this.engine.getStats(),
      processor: this.processor.getStats()
    };

    return enhanced;
  }

  /**
   * 处理执行结果
   */
  private async processResults(
    results: RuleExecutionResult[],
    event: SystemEvent,
    context: RuleContext
  ): Promise<void> {
    for (const result of results) {
      if (result.success) {
        this.emit('ruleSucceeded', { result, event, context });
      } else {
        this.emit('ruleFailed', { result, event, context });
      }
    }

    // 检查是否需要触发条件规则
    await this.checkConditionalRules(event, context, results);

    // 检查动态规则生成
    await this.checkDynamicRuleGeneration(event, context);
  }

  /**
   * 检查条件规则
   */
  private async checkConditionalRules(
    _event: SystemEvent,
    _context: RuleContext,
    _results: RuleExecutionResult[]
  ): Promise<void> {
    // 这里可以实现基于执行结果的条件规则触发逻辑
    // 例如：如果某些规则失败，触发特定的条件规则
  }

  /**
   * 检查动态规则生成
   */
  private async checkDynamicRuleGeneration(
    _event: SystemEvent,
    _context: RuleContext
  ): Promise<void> {
    // 这里可以实现基于执行结果的动态规则生成逻辑
    // 例如：根据事件模式动态生成新规则
  }

  /**
   * 开始事件处理
   */
  private async startEventProcessing(): Promise<void> {
    if (this.processingQueue || this.eventQueue.length === 0) {
      return;
    }

    this.processingQueue = true;

    while (this.eventQueue.length > 0) {
      const queuedEvent = this.eventQueue.shift();
      if (queuedEvent) {
        try {
          await this.processEvent(queuedEvent.event, queuedEvent.context);
        } catch (error) {
          this.emit('queuedEventError', { queuedEvent, error });
        }
      }
    }

    this.processingQueue = false;
  }

  /**
   * 添加规则
   */
  async addRule(rule: Rule): Promise<void> {
    await this.configManager.addRule(rule);
  }

  /**
   * 更新规则
   */
  async updateRule(ruleId: string, updates: Partial<Rule>): Promise<void> {
    await this.configManager.updateRule(ruleId, updates);
  }

  /**
   * 删除规则
   */
  async removeRule(ruleId: string): Promise<void> {
    await this.configManager.removeRule(ruleId);
  }

  /**
   * 启用规则
   */
  async enableRule(ruleId: string): Promise<void> {
    await this.configManager.enableRule(ruleId);
  }

  /**
   * 禁用规则
   */
  async disableRule(ruleId: string): Promise<void> {
    await this.configManager.disableRule(ruleId);
  }

  /**
   * 获取规则
   */
  getRule(ruleId: string): Rule | undefined {
    return this.engine.getRule(ruleId);
  }

  /**
   * 获取所有规则
   */
  getAllRules(): Rule[] {
    return this.engine.getAllRules();
  }

  /**
   * 获取指定类别的规则
   */
  getRulesByCategory(category: RuleCategory): Rule[] {
    return this.engine.getRulesByCategory(category);
  }

  /**
   * 获取活跃规则
   */
  getActiveRules(): Rule[] {
    return this.engine.getActiveRules();
  }

  /**
   * 创建规则链
   */
  createRuleChain(chainId: string, rules: string[], options?: any): RuleChain {
    return this.processor.createRuleChain(chainId, rules, options);
  }

  /**
   * 执行规则链
   */
  async executeRuleChain(chainId: string, event: SystemEvent, context?: RuleContext): Promise<any> {
    return this.processor.executeRuleChain(chainId, event, context);
  }

  /**
   * 创建条件规则
   */
  createConditionalRule(ruleId: string, conditions: any[], options?: any): ConditionalRule {
    return this.processor.createConditionalRule(ruleId, conditions, options);
  }

  /**
   * 评估条件规则
   */
  async evaluateConditionalRule(ruleId: string, event: SystemEvent, context?: RuleContext): Promise<any> {
    return this.processor.evaluateConditionalRule(ruleId, event, context || {} as RuleContext);
  }

  /**
   * 创建动态规则生成器
   */
  createDynamicRuleGenerator(generatorId: string, generator: any, options?: any): DynamicRuleGenerator {
    return this.processor.createDynamicRuleGenerator(generatorId, generator, options);
  }

  /**
   * 生成动态规则
   */
  async generateDynamicRules(generatorId: string, event: SystemEvent, context?: RuleContext): Promise<Rule[]> {
    return this.processor.generateDynamicRules(generatorId, event, context || {} as RuleContext);
  }

  /**
   * 获取执行历史
   */
  getExecutionHistory(limit?: number): any[] {
    const history = this.engine.getExecutionHistory(limit);
    // 为了便于测试与统计，提供顶层 success 与 executionTime 聚合字段
    return history.map((h) => {
      const success = h.result?.success ?? false;
      const executionTime = Array.isArray(h.result?.actions)
        ? h.result!.actions!.reduce((sum, a) => sum + (a.executionTime ?? 0), 0)
        : 0;
      return {
        ...h,
        success,
        executionTime,
      };
    });
  }

  /**
   * 获取统计信息
   */
  getStats(): RuleManagerStats {
    return {
      engine: this.engine.getStats(),
      processor: this.processor.getStats(),
      queuedEvents: this.eventQueue.length,
      isInitialized: this.isInitialized,
      isProcessingQueue: this.processingQueue
    };
  }

  /**
   * 清空执行历史
   */
  clearHistory(): void {
    this.engine.clearHistory();
  }

  /**
   * 重置规则管理器
   */
  async reset(): Promise<void> {
    this.engine.stop();
    this.processor.cleanup();
    this.eventQueue = [];
    this.processingQueue = false;
    this.isInitialized = false;
    
    await this.initialize();
  }

  /**
   * 关闭规则管理器
   */
  async shutdown(): Promise<void> {
    this.engine.stop();
    this.processor.cleanup();
    this.eventQueue = [];
    this.isInitialized = false;
    this.emit('shutdown');
  }

  /**
   * 销毁规则管理器
   */
  async destroy(): Promise<void> {
    await this.shutdown();
    this.removeAllListeners();
  }

  /**
   * 导出规则配置
   */
  async exportRules(): Promise<ExportedRulesData> {
    const rules = this.getAllRules();
    const stats = this.getStats();
    
    return {
      rules: rules.map(rule => ({
        ...rule,
        createdAt: rule.createdAt.toISOString(),
        updatedAt: rule.updatedAt.toISOString()
      })),
      stats,
      exportedAt: new Date().toISOString(),
      version: '1.0.0'
    };
  }

  /**
   * 导入规则配置
   */
  async importRules(data: ExportedRulesData): Promise<void> {
    for (const ruleData of data.rules) {
      const rule: Rule = {
        ...ruleData,
        createdAt: new Date(ruleData.createdAt),
        updatedAt: new Date(ruleData.updatedAt)
      };
      
      await this.addRule(rule);
    }
    
    this.emit('rulesImported', { count: data.rules.length });
  }

  /**
   * 验证规则配置
   */
  validateRule(rule: Rule): ValidationResult {
    // 基本验证
    if (!rule.id || !rule.name || !rule.category) {
      return {
        isValid: false,
        errors: ['Rule must have id, name, and category']
      };
    }

    if (!Array.isArray(rule.conditions) || !Array.isArray(rule.actions)) {
      return {
        isValid: false,
        errors: ['Rule must have conditions and actions arrays']
      };
    }

    if (rule.actions.length === 0) {
      return {
        isValid: false,
        errors: ['Rule must have at least one action']
      };
    }

    return { isValid: true, errors: [] };
  }
}

// 接口定义
export interface QueuedEvent {
  event: SystemEvent;
  context: RuleContext;
  timestamp: Date;
}

export interface RuleManagerStats {
  engine: any;
  processor: any;
  queuedEvents: number;
  isInitialized: boolean;
  isProcessingQueue: boolean;
}

export interface ExportedRulesData {
  rules: any[];
  stats: RuleManagerStats;
  exportedAt: string;
  version: string;
}

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
}