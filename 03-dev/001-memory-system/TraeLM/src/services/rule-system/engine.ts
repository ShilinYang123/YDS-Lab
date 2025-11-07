/**
 * 规则引擎
 * 负责规则的执行、匹配和管理
 */

import { EventEmitter } from 'events';
import { Rule, RuleCondition, RuleAction, RuleCategory, SystemEvent, ActionType, EventSeverity, ConditionOperator } from '../../types/base';

export class RuleEngine extends EventEmitter {
  private rules: Map<string, Rule> = new Map();
  private executionHistory: RuleExecution[] = [];
  private isRunning = false;
  private maxHistorySize = 1000;

  constructor() {
    super();
  }

  /**
   * 启动规则引擎
   */
  start(): void {
    if (this.isRunning) {
      return;
    }

    this.isRunning = true;
    this.emit('started');
  }

  /**
   * 停止规则引擎
   */
  stop(): void {
    if (!this.isRunning) {
      return;
    }

    this.isRunning = false;
    this.emit('stopped');
  }

  /**
   * 添加规则
   */
  addRule(rule: Rule): void {
    this.rules.set(rule.id, rule);
    this.emit('ruleAdded', rule);
  }

  /**
   * 移除规则
   */
  removeRule(ruleId: string): boolean {
    const removed = this.rules.delete(ruleId);
    if (removed) {
      this.emit('ruleRemoved', ruleId);
    }
    return removed;
  }

  /**
   * 更新规则
   */
  updateRule(rule: Rule): void {
    if (this.rules.has(rule.id)) {
      this.rules.set(rule.id, rule);
      this.emit('ruleUpdated', rule);
    } else {
      throw new Error(`Rule with id ${rule.id} not found`);
    }
  }

  /**
   * 获取规则
   */
  getRule(ruleId: string): Rule | undefined {
    return this.rules.get(ruleId);
  }

  /**
   * 获取所有规则
   */
  getAllRules(): Rule[] {
    return Array.from(this.rules.values());
  }

  /**
   * 获取指定类别的规则
   */
  getRulesByCategory(category: RuleCategory): Rule[] {
    return Array.from(this.rules.values()).filter(rule => rule.category === category);
  }

  /**
   * 获取活跃规则
   */
  getActiveRules(): Rule[] {
    return Array.from(this.rules.values()).filter(rule => rule.isActive);
  }

  /**
   * 执行规则匹配和处理
   */
  async processEvent(event: SystemEvent, context: RuleContext = {}): Promise<RuleExecutionResult[]> {
    if (!this.isRunning) {
      throw new Error('Rule engine is not running');
    }

    const results: RuleExecutionResult[] = [];
    const activeRules = this.getActiveRules();

    // 按优先级排序规则
    const sortedRules = activeRules.sort((a, b) => b.priority - a.priority);

    for (const rule of sortedRules) {
      try {
        const matches = await this.evaluateConditions(rule.conditions, event, context);
        
        if (matches) {
          const result = await this.executeActions(rule, event, context);
          results.push(result);

          // 记录执行历史
          this.recordExecution({
            ruleId: rule.id,
            event,
            context,
            result,
            timestamp: new Date()
          });

          // 如果规则设置为一次性执行，则禁用它
          if (rule.metadata?.['executeOnce']) {
            rule.isActive = false;
            this.updateRule(rule);
          }
        }
      } catch (error) {
        const errorResult: RuleExecutionResult = {
          ruleId: rule.id,
          success: false,
          error: error instanceof Error ? error.message : String(error),
          timestamp: new Date()
        };
        
        results.push(errorResult);
        this.emit('executionError', { rule, error, event, context });
      }
    }

    return results;
  }

  /**
   * 评估规则条件
   */
  private async evaluateConditions(
    conditions: RuleCondition[],
    event: SystemEvent,
    context: RuleContext
  ): Promise<boolean> {
    if (conditions.length === 0) {
      return true;
    }

    for (const condition of conditions) {
      const result = await this.evaluateCondition(condition, event, context);
      if (!result) {
        return false;
      }
    }

    return true;
  }

  /**
   * 评估单个条件
   */
  private async evaluateCondition(
    condition: RuleCondition,
    event: SystemEvent,
    context: RuleContext
  ): Promise<boolean> {
    const { field, operator, value } = condition;
    
    // 获取字段值
    const fieldValue = this.getFieldValue(field, event, context);

    switch (operator) {
      case ConditionOperator.EQUALS:
        return fieldValue === value;
      
      case ConditionOperator.NOT_EQUALS:
        return fieldValue !== value;
      
      case ConditionOperator.CONTAINS:
        return typeof fieldValue === 'string' && fieldValue.includes(String(value));
      
      case ConditionOperator.NOT_CONTAINS:
        return typeof fieldValue === 'string' && !fieldValue.includes(String(value));
      
      case ConditionOperator.STARTS_WITH:
        return typeof fieldValue === 'string' && fieldValue.startsWith(String(value));
      
      case ConditionOperator.ENDS_WITH:
        return typeof fieldValue === 'string' && fieldValue.endsWith(String(value));
      
      case ConditionOperator.GREATER_THAN:
        return Number(fieldValue) > Number(value);
      
      case ConditionOperator.LESS_THAN:
        return Number(fieldValue) < Number(value);
      
      case ConditionOperator.GREATER_EQUAL:
        return Number(fieldValue) >= Number(value);
      
      case ConditionOperator.LESS_EQUAL:
        return Number(fieldValue) <= Number(value);
      
      case ConditionOperator.IN:
        return Array.isArray(value) && value.includes(fieldValue);
      
      case ConditionOperator.NOT_IN:
        return Array.isArray(value) && !value.includes(fieldValue);
      
      case ConditionOperator.REGEX:
      case ConditionOperator.REGEX_MATCH:
        const regex = new RegExp(String(value));
        return regex.test(String(fieldValue));
      
      case ConditionOperator.EXISTS:
        return fieldValue !== undefined && fieldValue !== null;
      
      case ConditionOperator.NOT_EXISTS:
        return fieldValue === undefined || fieldValue === null;
      
      default:
        throw new Error(`Unknown operator: ${operator}`);
    }
  }

  /**
   * 获取字段值
   */
  private getFieldValue(field: string, event: SystemEvent, context: RuleContext): any {
    // 支持点号分隔的嵌套字段访问
    const parts = field.split('.');
    let value: any;

    // 首先尝试从事件中获取
    if (parts[0] === 'event') {
      value = event;
      for (let i = 1; i < parts.length; i++) {
        const part = parts[i];
        if (value && typeof value === 'object' && part && part in value) {
          value = (value as any)[part];
        } else {
          value = undefined;
          break;
        }
      }
    }
    // 然后尝试从上下文中获取
    else if (parts[0] === 'context') {
      value = context;
      for (let i = 1; i < parts.length; i++) {
        const part = parts[i];
        if (value && typeof value === 'object' && part && part in value) {
          value = (value as any)[part];
        } else {
          value = undefined;
          break;
        }
      }
    }
    // 直接从事件中获取
    else {
      value = event;
      for (const part of parts) {
        if (value && typeof value === 'object' && part && part in value) {
          value = (value as any)[part];
        } else {
          value = undefined;
          break;
        }
      }
    }

    return value;
  }

  /**
   * 执行规则动作
   */
  private async executeActions(
    rule: Rule,
    event: SystemEvent,
    context: RuleContext
  ): Promise<RuleExecutionResult> {
    const result: RuleExecutionResult = {
      ruleId: rule.id,
      success: true,
      actions: [],
      timestamp: new Date()
    };

    for (const action of rule.actions) {
      try {
        const actionResult = await this.executeAction(action, event, context);
        result.actions!.push(actionResult);

        // 如果某个动作执行失败，则标记整条规则执行为失败
        if (!actionResult.success) {
          result.success = false;
          result.error = actionResult.error ?? `Action ${action.type} failed`;
          // 一旦发生失败，停止后续动作执行
          break;
        }
      } catch (error) {
        result.success = false;
        result.error = error instanceof Error ? error.message : String(error);
        break;
      }
    }

    this.emit('ruleExecuted', { rule, result, event, context });
    return result;
  }

  /**
   * 执行单个动作
   */
  private async executeAction(
    action: RuleAction,
    event: SystemEvent,
    context: RuleContext
  ): Promise<ActionExecutionResult> {
    const startTime = Date.now();

    try {
      let result: any;

      switch (action.type) {
        case ActionType.LOG:
          result = this.executeLogAction(action, event, context);
          break;
        
        case ActionType.NOTIFY:
          result = await this.executeEmitEventAction(action, event, context);
          break;
        
        case ActionType.MODIFY:
          result = this.executeUpdateContextAction(action, event, context);
          break;
        
        case ActionType.ENHANCE:
          result = await this.executeCallFunctionAction(action, event, context);
          break;
        
        case ActionType.STORE_MEMORY:
          result = this.executeSetVariableAction(action, event, context);
          break;
        
        case ActionType.BLOCK:
          result = this.executeIncrementCounterAction(action, event, context);
          break;
        
        default:
          throw new Error(`Unknown action type: ${action.type}`);
      }

      return {
        type: action.type,
        success: true,
        result,
        executionTime: Date.now() - startTime
      };
    } catch (error) {
      return {
        type: action.type,
        success: false,
        error: error instanceof Error ? error.message : String(error),
        executionTime: Date.now() - startTime
      };
    }
  }

  /**
   * 执行日志动作
   */
  private executeLogAction(action: RuleAction, event: SystemEvent, context: RuleContext): void {
    const message = this.interpolateString(action.parameters['message'] || '', event, context);
    const level = action.parameters['level'] || 'info';
    
    // 使用类型断言确保level是有效的console方法
    const consoleMethod = console[level as 'log' | 'info' | 'warn' | 'error'];
    if (typeof consoleMethod === 'function') {
      consoleMethod(message);
    } else {
      console.log(message);
    }
  }

  /**
   * 执行发送事件动作
   */
  private async executeEmitEventAction(
    action: RuleAction,
    event: SystemEvent,
    context: RuleContext
  ): Promise<void> {
    const eventType = action.parameters['eventType'];
    const eventData = action.parameters['data'] || {};
    
    const newEvent: SystemEvent = {
      id: `generated_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      type: eventType,
      data: this.interpolateObject(eventData, event, context),
      timestamp: new Date(),
      source: 'rule_engine',
      severity: action.parameters['severity'] || EventSeverity.MEDIUM
    };

    this.emit('eventGenerated', newEvent);
  }

  /**
   * 执行更新上下文动作
   */
  private executeUpdateContextAction(
    action: RuleAction,
    _event: SystemEvent,
    context: RuleContext
  ): void {
    const updates = action.parameters['updates'] || {};
    
    for (const [key, value] of Object.entries(updates)) {
      context[key] = this.interpolateValue(value, _event, context);
    }
  }

  /**
   * 执行调用函数动作
   */
  private async executeCallFunctionAction(
    action: RuleAction,
    _event: SystemEvent,
    context: RuleContext
  ): Promise<any> {
    const functionName = action.parameters['function'];
    const args = action.parameters['arguments'] || [];
    
    // 这里可以扩展为支持插件系统
    if (typeof context[functionName] === 'function') {
      return await context[functionName](...args);
    }
    
    throw new Error(`Function ${functionName} not found in context`);
  }

  /**
   * 执行设置变量动作
   */
  private executeSetVariableAction(
    action: RuleAction,
    event: SystemEvent,
    context: RuleContext
  ): void {
    const variable = action.parameters['variable'];
    const value = this.interpolateValue(action.parameters['value'], event, context);
    
    context[variable] = value;
  }

  /**
   * 执行计数器递增动作
   */
  private executeIncrementCounterAction(
    action: RuleAction,
    _event: SystemEvent,
    context: RuleContext
  ): number {
    const counter = action.parameters['counter'];
    const increment = action.parameters['increment'] || 1;
    
    context[counter] = (context[counter] || 0) + increment;
    return context[counter];
  }

  /**
   * 字符串插值
   */
  private interpolateString(template: string, event: SystemEvent, context: RuleContext): string {
    return template.replace(/\{\{([^}]+)\}\}/g, (_match, field) => {
      const value = this.getFieldValue(field.trim(), event, context);
      return String(value || '');
    });
  }

  /**
   * 对象插值
   */
  private interpolateObject(obj: any, event: SystemEvent, context: RuleContext): any {
    if (typeof obj === 'string') {
      return this.interpolateString(obj, event, context);
    }
    
    if (Array.isArray(obj)) {
      return obj.map(item => this.interpolateObject(item, event, context));
    }
    
    if (typeof obj === 'object' && obj !== null) {
      const result: any = {};
      for (const [key, value] of Object.entries(obj)) {
        result[key] = this.interpolateObject(value, event, context);
      }
      return result;
    }
    
    return obj;
  }

  /**
   * 值插值
   */
  private interpolateValue(value: any, event: SystemEvent, context: RuleContext): any {
    if (typeof value === 'string' && value.startsWith('{{') && value.endsWith('}}')) {
      const field = value.slice(2, -2).trim();
      return this.getFieldValue(field, event, context);
    }
    
    return this.interpolateObject(value, event, context);
  }

  /**
   * 记录执行历史
   */
  private recordExecution(execution: RuleExecution): void {
    this.executionHistory.push(execution);
    
    // 限制历史记录大小
    if (this.executionHistory.length > this.maxHistorySize) {
      this.executionHistory.shift();
    }
  }

  /**
   * 获取执行历史
   */
  getExecutionHistory(limit?: number): RuleExecution[] {
    const history = [...this.executionHistory].reverse();
    return limit ? history.slice(0, limit) : history;
  }

  /**
   * 获取规则统计信息
   */
  getStats(): RuleEngineStats {
    const totalRules = this.rules.size;
    const activeRules = this.getActiveRules().length;
    const executionCount = this.executionHistory.length;
    
    const categoryStats: Record<string, number> = {};
    for (const rule of Array.from(this.rules.values())) {
      categoryStats[rule.category] = (categoryStats[rule.category] || 0) + 1;
    }

    return {
      totalRules,
      activeRules,
      executionCount,
      categoryStats,
      isRunning: this.isRunning
    };
  }

  /**
   * 清空执行历史
   */
  clearHistory(): void {
    this.executionHistory = [];
    this.emit('historyCleaned');
  }
}

// 接口定义
export interface RuleContext {
  [key: string]: any;
}

export interface RuleExecutionResult {
  ruleId: string;
  success: boolean;
  actions?: ActionExecutionResult[];
  error?: string;
  timestamp: Date;
}

export interface ActionExecutionResult {
  type: string;
  success: boolean;
  result?: any;
  error?: string;
  executionTime: number;
}

export interface RuleExecution {
  ruleId: string;
  event: SystemEvent;
  context: RuleContext;
  result: RuleExecutionResult;
  timestamp: Date;
}

export interface RuleEngineStats {
  totalRules: number;
  activeRules: number;
  executionCount: number;
  categoryStats: Record<string, number>;
  isRunning: boolean;
}