import { EventEmitter } from 'events';
import { Rule, RuleCategory, RuleCondition, ConditionOperator, RuleAction, ActionType, SystemEvent, EventSeverity, Memory, MemoryType, MemoryContext } from '../../types/base';
export class RuleEngine extends EventEmitter {
  private rules: Map<string, Rule> = new Map();
  private executionHistory: RuleExecution[] = [];
  private isRunning = false;
  private maxHistorySize = 1000;

  constructor() {
    super();
  }

  /**
   * 鍚姩瑙勫垯寮曟搸
   */
  start(): void {
    if (this.isRunning) {
      return;
    }

    this.isRunning = true;
    this.emit('started');
  }

  /**
   * 鍋滄瑙勫垯寮曟搸
   */
  stop(): void {
    if (!this.isRunning) {
      return;
    }

    this.isRunning = false;
    this.emit('stopped');
  }

  /**
   * 娣诲姞瑙勫垯
   */
  addRule(rule: Rule): void {
    this.rules.set(rule.id, rule);
    this.emit('ruleAdded', rule);
  }

  /**
   * 绉婚櫎瑙勫垯
   */
  removeRule(ruleId: string): boolean {
    const removed = this.rules.delete(ruleId);
    if (removed) {
      this.emit('ruleRemoved', ruleId);
    }
    return removed;
  }

  /**
   * 鏇存柊瑙勫垯
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
   * 鑾峰彇瑙勫垯
   */
  getRule(ruleId: string): Rule | undefined {
    return this.rules.get(ruleId);
  }

  /**
   * 鑾峰彇鎵€鏈夎鍒?
   */
  getAllRules(): Rule[] {
    return Array.from(this.rules.values());
  }

  /**
   * 鑾峰彇鎸囧畾绫诲埆鐨勮鍒?
   */
  getRulesByCategory(category: RuleCategory): Rule[] {
    return Array.from(this.rules.values()).filter(rule => rule.category === category);
  }

  /**
   * 鑾峰彇娲昏穬瑙勫垯
   */
  getActiveRules(): Rule[] {
    return Array.from(this.rules.values()).filter(rule => rule.isActive);
  }

  /**
   * 鎵ц瑙勫垯鍖归厤鍜屽鐞?
   */
  async processEvent(event: SystemEvent, context: RuleContext = {}): Promise<RuleExecutionResult[]> {
    if (!this.isRunning) {
      throw new Error('Rule engine is not running');
    }

    const results: RuleExecutionResult[] = [];
    const activeRules = this.getActiveRules();

    // 鎸変紭鍏堢骇鎺掑簭瑙勫垯
    const sortedRules = activeRules.sort((a, b) => b.priority - a.priority);

    for (const rule of sortedRules) {
      try {
        const matches = await this.evaluateConditions(rule.conditions, event, context);
        
        if (matches) {
          const result = await this.executeActions(rule, event, context);
          results.push(result);

          // 璁板綍鎵ц鍘嗗彶
          this.recordExecution({
            ruleId: rule.id,
            event,
            context,
            result,
            timestamp: new Date()
          });

          // 濡傛灉瑙勫垯璁剧疆涓轰竴娆℃€ф墽琛岋紝鍒欑鐢ㄥ畠
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
   * 璇勪及瑙勫垯鏉′欢
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
   * 璇勪及鍗曚釜鏉′欢
   */
  private async evaluateCondition(
    condition: RuleCondition,
    event: SystemEvent,
    context: RuleContext
  ): Promise<boolean> {
    const { field, operator, value } = condition;
    
    // 鑾峰彇瀛楁鍊?
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
   * 鑾峰彇瀛楁鍊?
   */
  private getFieldValue(field: string, event: SystemEvent, context: RuleContext): any {
    // 鏀寔鐐瑰彿鍒嗛殧鐨勫祵濂楀瓧娈佃闂?
    const parts = field.split('.');
    let value: any;

    // 棣栧厛灏濊瘯浠庝簨浠朵腑鑾峰彇
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
    // 鐒跺悗灏濊瘯浠庝笂涓嬫枃涓幏鍙?
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
    // 鐩存帴浠庝簨浠朵腑鑾峰彇
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
   * 鎵ц瑙勫垯鍔ㄤ綔
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

        // 濡傛灉鏌愪釜鍔ㄤ綔鎵ц澶辫触锛屽垯鏍囪鏁存潯瑙勫垯鎵ц涓哄け璐?
        if (!actionResult.success) {
          result.success = false;
          result.error = actionResult.error ?? `Action ${action.type} failed`;
          // 涓€鏃﹀彂鐢熷け璐ワ紝鍋滄鍚庣画鍔ㄤ綔鎵ц
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
   * 鎵ц鍗曚釜鍔ㄤ綔
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
   * 鎵ц鏃ュ織鍔ㄤ綔
   */
  private executeLogAction(action: RuleAction, event: SystemEvent, context: RuleContext): void {
    const message = this.interpolateString(action.parameters['message'] || '', event, context);
    const level = action.parameters['level'] || 'info';
    
    // 浣跨敤绫诲瀷鏂█纭繚level鏄湁鏁堢殑console鏂规硶
    const consoleMethod = console[level as 'log' | 'info' | 'warn' | 'error'];
    if (typeof consoleMethod === 'function') {
      consoleMethod(message);
    } else {
      console.log(message);
    }
  }

  /**
   * 鎵ц鍙戦€佷簨浠跺姩浣?
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
   * 鎵ц鏇存柊涓婁笅鏂囧姩浣?
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
   * 鎵ц璋冪敤鍑芥暟鍔ㄤ綔
   */
  private async executeCallFunctionAction(
    action: RuleAction,
    _event: SystemEvent,
    context: RuleContext
  ): Promise<any> {
    const functionName = action.parameters['function'];
    const args = action.parameters['arguments'] || [];
    
    // 杩欓噷鍙互鎵╁睍涓烘敮鎸佹彃浠剁郴缁?
    if (typeof context[functionName] === 'function') {
      return await context[functionName](...args);
    }
    
    throw new Error(`Function ${functionName} not found in context`);
  }

  /**
   * 鎵ц璁剧疆鍙橀噺鍔ㄤ綔
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
   * 鎵ц璁℃暟鍣ㄩ€掑鍔ㄤ綔
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
   * 瀛楃涓叉彃鍊?
   */
  private interpolateString(template: string, event: SystemEvent, context: RuleContext): string {
    return template.replace(/\{\{([^}]+)\}\}/g, (_match, field) => {
      const value = this.getFieldValue(field.trim(), event, context);
      return String(value || '');
    });
  }

  /**
   * 处理增强后的记忆对象，规范化为 Memory 类型
   * 该方法不依赖外部存储，纯转换逻辑，便于单元测试
   */
  }
  public async processMemory(enhanced: any, context: RuleContext = {}): Promise<Memory> {
    const rawContent = enhanced?.compressedContent ?? enhanced?.content ?? '';
    const content: string = typeof rawContent === 'string' ? rawContent : JSON.stringify(rawContent);

    const importance = typeof enhanced?.importanceScore === 'number'
      ? Math.max(0, Math.min(1, enhanced.importanceScore))
      : 0.5;

    const mapType = (t: string | undefined, imp: number): MemoryType => {
      const mapping: Record<string, MemoryType> = {
        error: MemoryType.EPISODIC,
        response: MemoryType.SEMANTIC,
        execution: MemoryType.PROCEDURAL,
        file_operation: MemoryType.WORKING,
        interaction: MemoryType.EPISODIC,
        session: MemoryType.CONSOLIDATED,
        general: MemoryType.SHORT_TERM,
      };
      if (imp >= 0.8) return MemoryType.LONG_TERM;
      if (!t) return MemoryType.SHORT_TERM;
      return mapping[t] ?? MemoryType.SHORT_TERM;
    };

    const type: MemoryType = mapType(enhanced?.type, importance);

    const mergedContext: MemoryContext = {
      ...(enhanced?.context ?? {}),
      ...(enhanced?.enrichedContext ?? {}),
      environment: {
        ...(enhanced?.context?.environment ?? {}),
        ...(enhanced?.enrichedContext?.environment ?? {}),
        ...(context?.environment ?? {}),
      }
    };

    const tags: string[] | undefined = Array.isArray(enhanced?.tags) ? enhanced.tags
      : (enhanced?.type ? [String(enhanced.type)] : undefined);

    const summary = typeof enhanced?.summary === 'string' && enhanced.summary.length > 0
      ? enhanced.summary
      : (typeof enhanced?.content === 'string'
        ? enhanced.content.slice(0, 200)
        : JSON.stringify(enhanced?.content ?? '').slice(0, 200));

    const createdAt = enhanced?.timestamp ? new Date(enhanced.timestamp) : new Date();
    const updatedAt = new Date();

    const memory: Memory = {
      id: String(enhanced?.id ?? `mem_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`),
      content,
      summary,
      type,
      importance,
      tags,
      context: mergedContext,
      metadata: {
        ...(enhanced?.metadata ?? {}),
        source: enhanced?.source ?? 'rule_engine',
        processedAt: enhanced?.processedAt ?? new Date().toISOString(),
        version: enhanced?.version ?? '1.0',
        originalType: enhanced?.type,
        compressed: typeof enhanced?.compressedContent === 'string',
      },
      createdAt,
      updatedAt,
    };

    try {
      const event: SystemEvent = {
        id: `memory_${memory.id}`,
        type: 'MEMORY_CREATED' as any,
        source: memory.metadata?.source ?? 'rule_engine',
        data: { memory },
        timestamp: new Date(),
        severity: EventSeverity.LOW
      };
      if (this.isRunning) await this.processEvent(event, context);
    } catch {
      // ignore rule processing errors
    }

    return memory;
  }

  /**
   * 瀵硅薄鎻掑€?
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
   * 鍊兼彃鍊?
   */
  private interpolateValue(value: any, event: SystemEvent, context: RuleContext): any {
    if (typeof value === 'string' && value.startsWith('{{') && value.endsWith('}}')) {
      const field = value.slice(2, -2).trim();
      return this.getFieldValue(field, event, context);
    }
    
    return this.interpolateObject(value, event, context);
  }

  /**
   * 璁板綍鎵ц鍘嗗彶
   */
  private recordExecution(execution: RuleExecution): void {
    this.executionHistory.push(execution);
    
    // 闄愬埗鍘嗗彶璁板綍澶у皬
    if (this.executionHistory.length > this.maxHistorySize) {
      this.executionHistory.shift();
    }
  }

  /**
   * 鑾峰彇鎵ц鍘嗗彶
   */
  getExecutionHistory(limit?: number): RuleExecution[] {
    const history = [...this.executionHistory].reverse();
    return limit ? history.slice(0, limit) : history;
  }

  /**
   * 鑾峰彇瑙勫垯缁熻淇℃伅
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
   * 娓呯┖鎵ц鍘嗗彶
   */
  clearHistory(): void {
    this.executionHistory = [];
    this.emit('historyCleaned');
  }
}

// 鎺ュ彛瀹氫箟
  /**
   * 处理增强后的记忆对象，规范化为 Memory 类型
   * 该方法不依赖外部存储，纯转换逻辑，便于单元测试
   */
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







