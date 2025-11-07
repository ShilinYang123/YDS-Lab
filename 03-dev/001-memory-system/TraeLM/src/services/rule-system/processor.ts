/**
 * 规则处理器
 * 提供高级规则处理功能，包括规则链、条件组合、动态规则生成等
 */

import { EventEmitter } from 'events';
import { Rule, RuleAction, SystemEvent } from '../../types/base';
import { RuleEngine, RuleContext, RuleExecutionResult } from './engine';

export class RuleProcessor extends EventEmitter {
  private engine: RuleEngine;
  private ruleChains: Map<string, RuleChain> = new Map();
  private conditionalRules: Map<string, ConditionalRule> = new Map();
  private dynamicRules: Map<string, DynamicRuleGenerator> = new Map();

  constructor(engine: RuleEngine) {
    super();
    this.engine = engine;
    this.setupEngineListeners();
  }

  /**
   * 设置引擎监听器
   */
  private setupEngineListeners(): void {
    this.engine.on('ruleExecuted', (data) => {
      this.handleRuleExecuted(data);
    });

    this.engine.on('executionError', (data) => {
      this.handleExecutionError(data);
    });
  }

  /**
   * 创建规则链
   */
  createRuleChain(chainId: string, rules: string[], options: RuleChainOptions = {}): RuleChain {
    const chain: RuleChain = {
      id: chainId,
      rules,
      options: {
        stopOnFailure: options.stopOnFailure ?? true,
        parallel: options.parallel ?? false,
        timeout: options.timeout ?? 30000,
        retryCount: options.retryCount ?? 0,
        ...options
      },
      status: 'idle',
      createdAt: new Date()
    };

    this.ruleChains.set(chainId, chain);
    this.emit('chainCreated', chain);
    return chain;
  }

  /**
   * 执行规则链
   */
  async executeRuleChain(
    chainId: string,
    event: SystemEvent,
    context: RuleContext = {}
  ): Promise<RuleChainResult> {
    const chain = this.ruleChains.get(chainId);
    if (!chain) {
      throw new Error(`Rule chain ${chainId} not found`);
    }

    chain.status = 'running';
    chain.lastExecuted = new Date();

    const result: RuleChainResult = {
      chainId,
      success: true,
      results: [],
      startTime: new Date(),
      endTime: new Date(),
      totalExecutionTime: 0
    };

    try {
      if (chain.options.parallel) {
        result.results = await this.executeRulesParallel(chain.rules, event, context, chain.options);
      } else {
        result.results = await this.executeRulesSequential(chain.rules, event, context, chain.options);
      }

      result.success = result.results.every(r => r.success);
      chain.status = result.success ? 'completed' : 'failed';
    } catch (error) {
      result.success = false;
      result.error = error instanceof Error ? error.message : String(error);
      chain.status = 'failed';
    }

    result.endTime = new Date();
    result.totalExecutionTime = result.endTime.getTime() - result.startTime.getTime();

    this.emit('chainExecuted', { chain, result });
    return result;
  }

  /**
   * 并行执行规则
   */
  private async executeRulesParallel(
    ruleIds: string[],
    event: SystemEvent,
    context: RuleContext,
    options: RuleChainOptions
  ): Promise<RuleExecutionResult[]> {
    const promises = ruleIds.map(async (ruleId) => {
      const rule = this.engine.getRule(ruleId);
      if (!rule) {
        throw new Error(`Rule ${ruleId} not found`);
      }

      return this.executeRuleWithRetry(rule, event, context, options.retryCount || 0);
    });

    if (options.timeout) {
      const timeoutPromise = new Promise<never>((_, reject) => {
        setTimeout(() => reject(new Error('Rule chain execution timeout')), options.timeout);
      });

      return Promise.race([Promise.all(promises), timeoutPromise]);
    }

    return Promise.all(promises);
  }

  /**
   * 顺序执行规则
   */
  private async executeRulesSequential(
    ruleIds: string[],
    event: SystemEvent,
    context: RuleContext,
    options: RuleChainOptions
  ): Promise<RuleExecutionResult[]> {
    const results: RuleExecutionResult[] = [];

    for (const ruleId of ruleIds) {
      const rule = this.engine.getRule(ruleId);
      if (!rule) {
        throw new Error(`Rule ${ruleId} not found`);
      }

      try {
        const result = await this.executeRuleWithRetry(rule, event, context, options.retryCount || 0);
        results.push(result);

        if (!result.success && options.stopOnFailure) {
          break;
        }
      } catch (error) {
        if (options.stopOnFailure) {
          throw error;
        }
        
        results.push({
          ruleId,
          success: false,
          error: error instanceof Error ? error.message : String(error),
          timestamp: new Date()
        });
      }
    }

    return results;
  }

  /**
   * 带重试的规则执行
   */
  private async executeRuleWithRetry(
    rule: Rule,
    event: SystemEvent,
    context: RuleContext,
    retryCount: number
  ): Promise<RuleExecutionResult> {
    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= retryCount; attempt++) {
      try {
        const results = await this.engine.processEvent(event, context);
        const ruleResult = results.find(r => r.ruleId === rule.id);
        
        if (ruleResult && ruleResult.success) {
          return ruleResult;
        }
        
        if (ruleResult) {
          lastError = new Error(ruleResult.error || 'Rule execution failed');
        }
      } catch (error) {
        lastError = error instanceof Error ? error : new Error(String(error));
      }

      if (attempt < retryCount) {
        await this.delay(Math.pow(2, attempt) * 1000); // 指数退避
      }
    }

    throw lastError || new Error('Rule execution failed after retries');
  }

  /**
   * 创建条件规则
   */
  createConditionalRule(
    ruleId: string,
    conditions: ConditionalRuleCondition[],
    options: ConditionalRuleOptions = {}
  ): ConditionalRule {
    const conditionalRule: ConditionalRule = {
      id: ruleId,
      conditions,
      options: {
        evaluationMode: options.evaluationMode || 'all',
        priority: options.priority || 0,
        ...options
      },
      createdAt: new Date()
    };

    this.conditionalRules.set(ruleId, conditionalRule);
    this.emit('conditionalRuleCreated', conditionalRule);
    return conditionalRule;
  }

  /**
   * 评估条件规则
   */
  async evaluateConditionalRule(
    ruleId: string,
    event: SystemEvent,
    context: RuleContext
  ): Promise<ConditionalRuleResult> {
    const conditionalRule = this.conditionalRules.get(ruleId);
    if (!conditionalRule) {
      throw new Error(`Conditional rule ${ruleId} not found`);
    }

    const result: ConditionalRuleResult = {
      ruleId,
      success: false,
      matchedConditions: [],
      executedActions: [],
      timestamp: new Date()
    };

    try {
      const evaluationResults = await Promise.all(
        conditionalRule.conditions.map(condition => 
          this.evaluateConditionalRuleCondition(condition, event, context)
        )
      );

      const matchedConditions = evaluationResults.filter(r => r.matched);
      result.matchedConditions = matchedConditions;

      let shouldExecute = false;
      switch (conditionalRule.options.evaluationMode) {
        case 'all':
          shouldExecute = matchedConditions.length === conditionalRule.conditions.length;
          break;
        case 'any':
          shouldExecute = matchedConditions.length > 0;
          break;
        case 'none':
          shouldExecute = matchedConditions.length === 0;
          break;
        case 'majority':
          shouldExecute = matchedConditions.length > conditionalRule.conditions.length / 2;
          break;
      }

      if (shouldExecute) {
        // 执行匹配条件的动作
        for (const matchedCondition of matchedConditions) {
          if (matchedCondition.condition.actions) {
            for (const action of matchedCondition.condition.actions) {
              const actionResult = await this.executeConditionalAction(action, event, context);
              result.executedActions.push(actionResult);
            }
          }
        }
        result.success = true;
      }
    } catch (error) {
      result.error = error instanceof Error ? error.message : String(error);
    }

    this.emit('conditionalRuleEvaluated', result);
    return result;
  }

  /**
   * 评估条件规则的单个条件
   */
  private async evaluateConditionalRuleCondition(
    condition: ConditionalRuleCondition,
    event: SystemEvent,
    context: RuleContext
  ): Promise<ConditionalRuleConditionResult> {
    try {
      let matched = false;

      if (condition.ruleId) {
        // 基于规则ID的条件
        const rule = this.engine.getRule(condition.ruleId);
        if (rule) {
          const results = await this.engine.processEvent(event, context);
          const ruleResult = results.find(r => r.ruleId === condition.ruleId);
          matched = ruleResult?.success || false;
        }
      } else if (condition.expression) {
        // 基于表达式的条件
        matched = await this.evaluateExpression(condition.expression, event, context);
      } else if (condition.customEvaluator) {
        // 自定义评估器
        matched = await condition.customEvaluator(event, context);
      }

      return {
        condition,
        matched,
        timestamp: new Date()
      };
    } catch (error) {
      return {
        condition,
        matched: false,
        error: error instanceof Error ? error.message : String(error),
        timestamp: new Date()
      };
    }
  }

  /**
   * 执行条件动作
   */
  private async executeConditionalAction(
    action: RuleAction,
    _event: SystemEvent,
    _context: RuleContext
  ): Promise<any> {
    // 这里可以复用规则引擎的动作执行逻辑
    // 或者实现特定的条件动作执行逻辑
    return { type: action.type, executed: true, timestamp: new Date() };
  }

  /**
   * 创建动态规则生成器
   */
  createDynamicRuleGenerator(
    generatorId: string,
    generator: DynamicRuleGeneratorFunction,
    options: DynamicRuleGeneratorOptions = {}
  ): DynamicRuleGenerator {
    const dynamicGenerator: DynamicRuleGenerator = {
      id: generatorId,
      generator,
      options: {
        maxRules: options.maxRules || 100,
        ttl: options.ttl || 3600000, // 1小时
        autoCleanup: options.autoCleanup ?? true,
        ...options
      },
      generatedRules: new Map(),
      createdAt: new Date()
    };

    this.dynamicRules.set(generatorId, dynamicGenerator);
    this.emit('dynamicGeneratorCreated', dynamicGenerator);

    // 设置自动清理
    if (dynamicGenerator.options.autoCleanup) {
      this.setupDynamicRuleCleanup(dynamicGenerator);
    }

    return dynamicGenerator;
  }

  /**
   * 生成动态规则
   */
  async generateDynamicRules(
    generatorId: string,
    event: SystemEvent,
    context: RuleContext
  ): Promise<Rule[]> {
    const generator = this.dynamicRules.get(generatorId);
    if (!generator) {
      throw new Error(`Dynamic rule generator ${generatorId} not found`);
    }

    try {
      const rules = await generator.generator(event, context);
      const validRules: Rule[] = [];

      for (const rule of rules) {
        // 检查规则数量限制
        if (generator.options.maxRules && generator.generatedRules.size >= generator.options.maxRules) {
          break;
        }

        // 添加TTL信息
        const ruleWithTTL: GeneratedRule = {
          rule,
          generatedAt: new Date(),
          expiresAt: new Date(Date.now() + (generator.options.ttl || 86400000)) // 默认24小时
        };

        generator.generatedRules.set(rule.id, ruleWithTTL);
        this.engine.addRule(rule);
        validRules.push(rule);
      }

      this.emit('dynamicRulesGenerated', { generatorId, rules: validRules });
      return validRules;
    } catch (error) {
      this.emit('dynamicGenerationError', { generatorId, error });
      throw error;
    }
  }

  /**
   * 设置动态规则清理
   */
  private setupDynamicRuleCleanup(generator: DynamicRuleGenerator): void {
    const cleanupInterval = setInterval(() => {
      const now = new Date();
      const expiredRules: string[] = [];

      for (const [ruleId, generatedRule] of generator.generatedRules) {
        if (generatedRule.expiresAt <= now) {
          expiredRules.push(ruleId);
        }
      }

      for (const ruleId of expiredRules) {
        generator.generatedRules.delete(ruleId);
        this.engine.removeRule(ruleId);
      }

      if (expiredRules.length > 0) {
        this.emit('dynamicRulesExpired', { generatorId: generator.id, expiredRules });
      }
    }, 60000); // 每分钟检查一次

    // 存储清理间隔ID以便后续清理
    (generator as any).cleanupInterval = cleanupInterval;
  }

  /**
   * 表达式评估
   */
  private async evaluateExpression(
    expression: string,
    event: SystemEvent,
    context: RuleContext
  ): Promise<boolean> {
    // 简单的表达式评估器
    // 在实际应用中，可以使用更强大的表达式引擎
    try {
      const safeExpression = expression
        .replace(/event\./g, 'event.')
        .replace(/context\./g, 'context.');

      // 创建安全的评估环境
      const evalContext = { event, context };
      const func = new Function('event', 'context', `return ${safeExpression}`);
      return Boolean(func(evalContext.event, evalContext.context));
    } catch (error) {
      console.warn(`Expression evaluation failed: ${expression}`, error);
      return false;
    }
  }

  /**
   * 处理规则执行完成
   */
  private handleRuleExecuted(data: any): void {
    // 可以在这里添加规则执行后的处理逻辑
    this.emit('ruleProcessed', data);
  }

  /**
   * 处理规则执行错误
   */
  private handleExecutionError(data: any): void {
    // 可以在这里添加错误处理逻辑
    this.emit('ruleProcessingError', data);
  }

  /**
   * 延迟函数
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * 获取处理器统计信息
   */
  getStats(): RuleProcessorStats {
    return {
      ruleChains: this.ruleChains.size,
      conditionalRules: this.conditionalRules.size,
      dynamicGenerators: this.dynamicRules.size,
      totalGeneratedRules: Array.from(this.dynamicRules.values())
        .reduce((sum, gen) => sum + gen.generatedRules.size, 0)
    };
  }

  /**
   * 清理资源
   */
  cleanup(): void {
    // 清理动态规则生成器的定时器
    for (const generator of this.dynamicRules.values()) {
      if ((generator as any).cleanupInterval) {
        clearInterval((generator as any).cleanupInterval);
      }
    }

    this.ruleChains.clear();
    this.conditionalRules.clear();
    this.dynamicRules.clear();
  }
}

// 接口定义
export interface RuleChain {
  id: string;
  rules: string[];
  options: RuleChainOptions;
  status: 'idle' | 'running' | 'completed' | 'failed';
  createdAt: Date;
  lastExecuted?: Date;
}

export interface RuleChainOptions {
  stopOnFailure?: boolean;
  parallel?: boolean;
  timeout?: number;
  retryCount?: number;
}

export interface RuleChainResult {
  chainId: string;
  success: boolean;
  results: RuleExecutionResult[];
  error?: string;
  startTime: Date;
  endTime: Date;
  totalExecutionTime: number;
}

export interface ConditionalRule {
  id: string;
  conditions: ConditionalRuleCondition[];
  options: ConditionalRuleOptions;
  createdAt: Date;
}

export interface ConditionalRuleCondition {
  ruleId?: string;
  expression?: string;
  customEvaluator?: (event: SystemEvent, context: RuleContext) => Promise<boolean>;
  actions?: RuleAction[];
}

export interface ConditionalRuleOptions {
  evaluationMode?: 'all' | 'any' | 'none' | 'majority';
  priority?: number;
}

export interface ConditionalRuleResult {
  ruleId: string;
  success: boolean;
  matchedConditions: ConditionalRuleConditionResult[];
  executedActions: any[];
  error?: string;
  timestamp: Date;
}

export interface ConditionalRuleConditionResult {
  condition: ConditionalRuleCondition;
  matched: boolean;
  error?: string;
  timestamp: Date;
}

export interface DynamicRuleGenerator {
  id: string;
  generator: DynamicRuleGeneratorFunction;
  options: DynamicRuleGeneratorOptions;
  generatedRules: Map<string, GeneratedRule>;
  createdAt: Date;
}

export interface DynamicRuleGeneratorOptions {
  maxRules?: number;
  ttl?: number;
  autoCleanup?: boolean;
}

export interface GeneratedRule {
  rule: Rule;
  generatedAt: Date;
  expiresAt: Date;
}

export type DynamicRuleGeneratorFunction = (
  event: SystemEvent,
  context: RuleContext
) => Promise<Rule[]>;

export interface RuleProcessorStats {
  ruleChains: number;
  conditionalRules: number;
  dynamicGenerators: number;
  totalGeneratedRules: number;
}