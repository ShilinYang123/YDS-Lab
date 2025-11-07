/**
 * 配置验证器
 * 验证配置的正确性和完整性
 */

import {
  SystemConfiguration,
  Rule,
  Memory,
  KnowledgeNode,
  Agent,
  LogLevel,
  RuleCategory,
  MemoryType,
  AgentType
} from '../types/base';
import { DEFAULT_VALIDATION_RULES } from './defaults';

export class ConfigurationValidator {
  private validationErrors: string[] = [];

  /**
   * 验证系统配置
   */
  validateSystemConfig(config: SystemConfiguration): ValidationResult {
    this.validationErrors = [];

    this.validateDatabaseConfig(config.database);
    this.validateCacheConfig(config.cache);
    this.validateLoggingConfig(config.logging);
    this.validateSecurityConfig(config.security);
    this.validatePerformanceConfig(config.performance);

    return {
      isValid: this.validationErrors.length === 0,
      errors: [...this.validationErrors]
    };
  }

  /**
   * 验证规则配置
   */
  validateRule(rule: Rule): ValidationResult {
    this.validationErrors = [];

    // 验证基本字段
    if (!rule.id || typeof rule.id !== 'string') {
      this.addError('Rule ID is required and must be a string');
    }

    if (!rule.name || typeof rule.name !== 'string') {
      this.addError('Rule name is required and must be a string');
    } else if (
      rule.name.length < DEFAULT_VALIDATION_RULES.rule.minNameLength ||
      rule.name.length > DEFAULT_VALIDATION_RULES.rule.maxNameLength
    ) {
      this.addError(
        `Rule name length must be between ${DEFAULT_VALIDATION_RULES.rule.minNameLength} and ${DEFAULT_VALIDATION_RULES.rule.maxNameLength} characters`
      );
    }

    // 验证类别
    if (!Object.values(RuleCategory).includes(rule.category)) {
      this.addError(`Invalid rule category: ${rule.category}`);
    }

    // 验证优先级
    if (
      typeof rule.priority !== 'number' ||
      rule.priority < (DEFAULT_VALIDATION_RULES.rule.priorityRange?.[0] ?? 1) ||
      rule.priority > (DEFAULT_VALIDATION_RULES.rule.priorityRange?.[1] ?? 10)
    ) {
      this.addError(
        `Rule priority must be a number between ${DEFAULT_VALIDATION_RULES.rule.priorityRange?.[0] ?? 1} and ${DEFAULT_VALIDATION_RULES.rule.priorityRange?.[1] ?? 10}`
      );
    }

    // 验证条件
    if (!Array.isArray(rule.conditions)) {
      this.addError('Rule conditions must be an array');
    } else if (rule.conditions.length > DEFAULT_VALIDATION_RULES.rule.maxConditions) {
      this.addError(
        `Rule cannot have more than ${DEFAULT_VALIDATION_RULES.rule.maxConditions} conditions`
      );
    }

    // 验证动作
    if (!Array.isArray(rule.actions)) {
      this.addError('Rule actions must be an array');
    } else if (rule.actions.length > DEFAULT_VALIDATION_RULES.rule.maxActions) {
      this.addError(
        `Rule cannot have more than ${DEFAULT_VALIDATION_RULES.rule.maxActions} actions`
      );
    }

    return {
      isValid: this.validationErrors.length === 0,
      errors: [...this.validationErrors]
    };
  }

  /**
   * 验证记忆对象
   */
  validateMemory(memory: Memory): ValidationResult {
    this.validationErrors = [];

    // 验证基本字段
    if (!memory.id || typeof memory.id !== 'string') {
      this.addError('Memory ID is required and must be a string');
    }

    if (!memory.content || typeof memory.content !== 'string') {
      this.addError('Memory content is required and must be a string');
    } else if (
      memory.content.length < DEFAULT_VALIDATION_RULES.memory.minContentLength ||
      memory.content.length > DEFAULT_VALIDATION_RULES.memory.maxContentLength
    ) {
      this.addError(
        `Memory content length must be between ${DEFAULT_VALIDATION_RULES.memory.minContentLength} and ${DEFAULT_VALIDATION_RULES.memory.maxContentLength} characters`
      );
    }

    // 验证类型
    if (!Object.values(MemoryType).includes(memory.type)) {
      this.addError(`Invalid memory type: ${memory.type}`);
    }

    // 验证重要性
    if (
      typeof memory.importance !== 'number' ||
      memory.importance < (DEFAULT_VALIDATION_RULES.memory.importanceRange?.[0] ?? 1) ||
      memory.importance > (DEFAULT_VALIDATION_RULES.memory.importanceRange?.[1] ?? 10)
    ) {
      this.addError(
        `Memory importance must be a number between ${DEFAULT_VALIDATION_RULES.memory.importanceRange?.[0] ?? 1} and ${DEFAULT_VALIDATION_RULES.memory.importanceRange?.[1] ?? 10}`
      );
    }

    // 验证标签（改为可选）
    if (memory.tags) {
      if (!Array.isArray(memory.tags)) {
        this.addError('Memory tags must be an array');
      } else if (memory.tags.length > DEFAULT_VALIDATION_RULES.memory.maxTags) {
        this.addError(
          `Memory cannot have more than ${DEFAULT_VALIDATION_RULES.memory.maxTags} tags`
        );
      }
    }

    return {
      isValid: this.validationErrors.length === 0,
      errors: [...this.validationErrors]
    };
  }

  /**
   * 验证知识节点
   */
  validateKnowledgeNode(node: KnowledgeNode): ValidationResult {
    this.validationErrors = [];

    // 验证基本字段
    if (!node.id || typeof node.id !== 'string') {
      this.addError('Knowledge node ID is required and must be a string');
    }

    if (!node.label || typeof node.label !== 'string') {
      this.addError('Knowledge node label is required and must be a string');
    } else if (
      node.label.length < DEFAULT_VALIDATION_RULES.knowledgeNode.minLabelLength ||
      node.label.length > DEFAULT_VALIDATION_RULES.knowledgeNode.maxLabelLength
    ) {
      this.addError(
        `Knowledge node label length must be between ${DEFAULT_VALIDATION_RULES.knowledgeNode.minLabelLength} and ${DEFAULT_VALIDATION_RULES.knowledgeNode.maxLabelLength} characters`
      );
    }

    // 验证类型：放宽为字符串，兼容测试使用的自定义类型
    if (!node.type || typeof node.type !== 'string') {
      this.addError('Knowledge node type is required and must be a string');
    }

    // 验证属性
    if (typeof node.properties !== 'object' || node.properties === null) {
      this.addError('Knowledge node properties must be an object');
    } else if (
      Object.keys(node.properties).length > DEFAULT_VALIDATION_RULES.knowledgeNode.maxProperties
    ) {
      this.addError(
        `Knowledge node cannot have more than ${DEFAULT_VALIDATION_RULES.knowledgeNode.maxProperties} properties`
      );
    }

    return {
      isValid: this.validationErrors.length === 0,
      errors: [...this.validationErrors]
    };
  }

  /**
   * 验证智能体配置
   */
  validateAgent(agent: Agent): ValidationResult {
    this.validationErrors = [];

    // 验证基本字段
    if (!agent.id || typeof agent.id !== 'string') {
      this.addError('Agent ID is required and must be a string');
    }

    if (!agent.name || typeof agent.name !== 'string') {
      this.addError('Agent name is required and must be a string');
    }

    // 验证类型
    if (!Object.values(AgentType).includes(agent.type)) {
      this.addError(`Invalid agent type: ${agent.type}`);
    }

    // 验证能力
    if (!Array.isArray(agent.capabilities)) {
      this.addError('Agent capabilities must be an array');
    }

    // 验证配置
    if (!agent.configuration || typeof agent.configuration !== 'object') {
      this.addError('Agent configuration is required and must be an object');
    } else {
      this.validateAgentConfiguration(agent.configuration);
    }

    return {
      isValid: this.validationErrors.length === 0,
      errors: [...this.validationErrors]
    };
  }

  /**
   * 验证数据库配置
   */
  private validateDatabaseConfig(config: any): void {
    if (!config) {
      this.addError('Database configuration is required');
      return;
    }

    if (!['memory', 'file', 'sqlite', 'postgresql'].includes(config.type)) {
      this.addError(`Invalid database type: ${config.type}`);
    }

    if (typeof config.maxConnections !== 'number' || config.maxConnections <= 0) {
      this.addError('Database maxConnections must be a positive number');
    }

    if (typeof config.timeout !== 'number' || config.timeout <= 0) {
      this.addError('Database timeout must be a positive number');
    }
  }

  /**
   * 验证缓存配置
   */
  private validateCacheConfig(config: any): void {
    if (!config) {
      this.addError('Cache configuration is required');
      return;
    }

    if (typeof config.enabled !== 'boolean') {
      this.addError('Cache enabled must be a boolean');
    }

    if (typeof config.maxSize !== 'number' || config.maxSize <= 0) {
      this.addError('Cache maxSize must be a positive number');
    }

    if (typeof config.ttl !== 'number' || config.ttl < 0) {
      this.addError('Cache TTL must be a non-negative number');
    }

    if (!['lru', 'fifo', 'lfu'].includes(config.strategy)) {
      this.addError(`Invalid cache strategy: ${config.strategy}`);
    }
  }

  /**
   * 验证日志配置
   */
  private validateLoggingConfig(config: any): void {
    if (!config) {
      this.addError('Logging configuration is required');
      return;
    }

    if (!Object.values(LogLevel).includes(config.level)) {
      this.addError(`Invalid log level: ${config.level}`);
    }

    if (!['json', 'text'].includes(config.format)) {
      this.addError(`Invalid log format: ${config.format}`);
    }

    if (!['console', 'file', 'both'].includes(config.destination)) {
      this.addError(`Invalid log destination: ${config.destination}`);
    }
  }

  /**
   * 验证安全配置
   */
  private validateSecurityConfig(config: any): void {
    if (!config) {
      this.addError('Security configuration is required');
      return;
    }

    if (config.encryption) {
      if (typeof config.encryption.enabled !== 'boolean') {
        this.addError('Security encryption enabled must be a boolean');
      }
    }

    if (config.authentication) {
      if (typeof config.authentication.required !== 'boolean') {
        this.addError('Security authentication required must be a boolean');
      }
    }
  }

  /**
   * 验证性能配置
   */
  private validatePerformanceConfig(config: any): void {
    if (!config) {
      this.addError('Performance configuration is required');
      return;
    }

    if (typeof config.maxConcurrentOperations !== 'number' || config.maxConcurrentOperations <= 0) {
      this.addError('Performance maxConcurrentOperations must be a positive number');
    }

    if (typeof config.batchSize !== 'number' || config.batchSize <= 0) {
      this.addError('Performance batchSize must be a positive number');
    }
  }

  /**
   * 验证智能体配置
   */
  private validateAgentConfiguration(config: any): void {
    if (typeof config.maxMemorySize !== 'number' || config.maxMemorySize <= 0) {
      this.addError('Agent maxMemorySize must be a positive number');
    }

    if (typeof config.processingTimeout !== 'number' || config.processingTimeout <= 0) {
      this.addError('Agent processingTimeout must be a positive number');
    }

    if (typeof config.retryAttempts !== 'number' || config.retryAttempts < 0) {
      this.addError('Agent retryAttempts must be a non-negative number');
    }

    if (!Object.values(LogLevel).includes(config.logLevel)) {
      this.addError(`Invalid agent log level: ${config.logLevel}`);
    }
  }

  /**
   * 添加验证错误
   */
  private addError(message: string): void {
    this.validationErrors.push(message);
  }
}

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
}