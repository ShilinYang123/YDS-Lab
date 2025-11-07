/**
 * 配置管理器
 * 统一管理所有配置操作
 */

import { EventEmitter } from 'events';
import { SystemConfiguration, Rule } from '../types/base';
import { ConfigurationLoader } from './loader';
import { ConfigurationValidator, ValidationResult } from './validator';
import { DEFAULT_SYSTEM_CONFIG } from './defaults';

export class ConfigurationManager extends EventEmitter {
  private loader: ConfigurationLoader;
  private validator: ConfigurationValidator;
  private currentConfig: SystemConfiguration;
  private rules: Rule[] = [];
  private isInitialized = false;

  constructor() {
    super();
    this.loader = new ConfigurationLoader();
    this.validator = new ConfigurationValidator();
    this.currentConfig = DEFAULT_SYSTEM_CONFIG;
  }

  /**
   * 初始化配置管理器
   */
  async initialize(configPath?: string): Promise<void> {
    try {
      // 加载系统配置
      this.currentConfig = await this.loader.loadSystemConfig(configPath);
      
      // 合并环境变量配置
      const envConfig = this.loader.getEnvironmentConfig();
      this.currentConfig = this.mergeConfigs(this.currentConfig, envConfig);

      // 验证配置
      const validation = this.validator.validateSystemConfig(this.currentConfig);
      if (!validation.isValid) {
        throw new Error(`Invalid configuration: ${validation.errors.join(', ')}`);
      }

      // 加载规则
      this.rules = await this.loader.loadRules();

      // 验证规则
      for (const rule of this.rules) {
        const ruleValidation = this.validator.validateRule(rule);
        if (!ruleValidation.isValid) {
          console.warn(`Invalid rule ${rule.id}: ${ruleValidation.errors.join(', ')}`);
        }
      }

      this.isInitialized = true;
      this.emit('initialized', this.currentConfig);
    } catch (error) {
      this.emit('error', error);
      throw error;
    }
  }

  /**
   * 获取系统配置
   */
  getSystemConfig(): SystemConfiguration {
    if (!this.isInitialized) {
      throw new Error('Configuration manager not initialized');
    }
    return { ...this.currentConfig };
  }

  /**
   * 更新系统配置
   */
  async updateSystemConfig(updates: Partial<SystemConfiguration>): Promise<void> {
    const newConfig = this.mergeConfigs(this.currentConfig, updates);
    
    const validation = this.validator.validateSystemConfig(newConfig);
    if (!validation.isValid) {
      throw new Error(`Invalid configuration updates: ${validation.errors.join(', ')}`);
    }

    this.currentConfig = newConfig;
    this.emit('configUpdated', this.currentConfig);
  }

  /**
   * 获取所有规则
   */
  getRules(): Rule[] {
    return [...this.rules];
  }

  /**
   * 获取指定类别的规则
   */
  getRulesByCategory(category: string): Rule[] {
    return this.rules.filter(rule => rule.category === category);
  }

  /**
   * 获取活跃规则
   */
  getActiveRules(): Rule[] {
    return this.rules.filter(rule => rule.isActive);
  }

  /**
   * 添加规则
   */
  async addRule(rule: Rule): Promise<void> {
    const validation = this.validator.validateRule(rule);
    if (!validation.isValid) {
      throw new Error(`Invalid rule: ${validation.errors.join(', ')}`);
    }

    // 检查规则ID是否已存在
    if (this.rules.some(r => r.id === rule.id)) {
      throw new Error(`Rule with ID ${rule.id} already exists`);
    }

    this.rules.push(rule);
    this.emit('ruleAdded', rule);
  }

  /**
   * 更新规则
   */
  updateRule(ruleId: string, updates: Partial<Rule>): boolean {
    const ruleIndex = this.rules.findIndex(rule => rule.id === ruleId);
    if (ruleIndex === -1) {
      return false;
    }

    const existingRule = this.rules[ruleIndex];
    if (!existingRule) {
      return false;
    }

    const updatedRule: Rule = {
      ...existingRule,
      ...updates,
      updatedAt: new Date(),
      id: existingRule.id // 确保id字段存在
    };

    this.rules[ruleIndex] = updatedRule;
    this.emit('ruleUpdated', updatedRule);
    return true;
  }

  /**
   * 删除规则
   */
  async removeRule(ruleId: string): Promise<void> {
    const ruleIndex = this.rules.findIndex(r => r.id === ruleId);
    if (ruleIndex === -1) {
      throw new Error(`Rule with ID ${ruleId} not found`);
    }

    const removedRule = this.rules.splice(ruleIndex, 1)[0];
    this.emit('ruleRemoved', removedRule);
  }

  /**
   * 启用规则
   */
  async enableRule(ruleId: string): Promise<void> {
    await this.updateRule(ruleId, { isActive: true });
  }

  /**
   * 禁用规则
   */
  async disableRule(ruleId: string): Promise<void> {
    await this.updateRule(ruleId, { isActive: false });
  }

  /**
   * 保存配置到文件
   */
  async saveConfig(filePath: string): Promise<void> {
    await this.loader.saveConfig(this.currentConfig, filePath);
    this.emit('configSaved', filePath);
  }

  /**
   * 保存规则到文件
   */
  async saveRules(filePath: string): Promise<void> {
    const rulesData = {
      rules: this.rules.map(rule => ({
        ...rule,
        createdAt: rule.createdAt.toISOString(),
        updatedAt: rule.updatedAt.toISOString()
      }))
    };

    await this.loader.saveConfig(rulesData, filePath);
    this.emit('rulesSaved', filePath);
  }

  /**
   * 重新加载配置
   */
  async reload(): Promise<void> {
    this.loader.clearCache();
    await this.initialize();
    this.emit('reloaded');
  }

  /**
   * 监听配置文件变化
   */
  watchConfigFile(filePath: string): void {
    this.loader.watchConfigFile(filePath, async (config) => {
      try {
        const validation = this.validator.validateSystemConfig(config);
        if (validation.isValid) {
          this.currentConfig = config;
          this.emit('configChanged', config);
        } else {
          this.emit('configError', new Error(`Invalid config file: ${validation.errors.join(', ')}`));
        }
      } catch (error) {
        this.emit('configError', error);
      }
    });
  }

  /**
   * 停止监听配置文件
   */
  unwatchConfigFile(filePath: string): void {
    this.loader.unwatchConfigFile(filePath);
  }

  /**
   * 获取配置统计信息
   */
  getStats(): ConfigurationStats {
    return {
      totalRules: this.rules.length,
      activeRules: this.rules.filter(r => r.isActive).length,
      rulesByCategory: this.getRulesCategoryStats(),
      cacheStats: this.loader.getCacheStats(),
      isInitialized: this.isInitialized
    };
  }

  /**
   * 验证当前配置
   */
  validateCurrentConfig(): ValidationResult {
    return this.validator.validateSystemConfig(this.currentConfig);
  }

  /**
   * 重置为默认配置
   */
  resetToDefaults(): void {
    this.currentConfig = { ...DEFAULT_SYSTEM_CONFIG };
    this.rules = [];
    this.emit('reset');
  }

  /**
   * 销毁配置管理器
   */
  async destroy(): Promise<void> {
    this.loader.destroy();
    this.rules = [];
    this.isInitialized = false;
    this.removeAllListeners();
  }

  /**
   * 合并配置对象
   */
  private mergeConfigs(target: any, source: any): any {
    const result = { ...target };

    for (const key in source) {
      if (source.hasOwnProperty(key)) {
        if (
          typeof source[key] === 'object' &&
          source[key] !== null &&
          !Array.isArray(source[key])
        ) {
          result[key] = this.mergeConfigs(result[key] || {}, source[key]);
        } else {
          result[key] = source[key];
        }
      }
    }

    return result;
  }

  /**
   * 获取规则类别统计
   */
  private getRulesCategoryStats(): Record<string, number> {
    const stats: Record<string, number> = {};
    
    for (const rule of this.rules) {
      stats[rule.category] = (stats[rule.category] || 0) + 1;
    }

    return stats;
  }
}

export interface ConfigurationStats {
  totalRules: number;
  activeRules: number;
  rulesByCategory: Record<string, number>;
  cacheStats: { size: number; keys: string[] };
  isInitialized: boolean;
}