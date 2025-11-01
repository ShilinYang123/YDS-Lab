/**
 * 配置加载器
 * 负责加载、验证和合并配置文件
 */

import * as fs from 'fs-extra';
import * as path from 'path';
import * as yaml from 'yaml';
import { SystemConfiguration, Rule, LogLevel, DatabaseConfig, LoggingConfig, PerformanceConfig } from '../types/base';
import { DEFAULT_SYSTEM_CONFIG, DEFAULT_FILE_PATHS } from './defaults';

export class ConfigurationLoader {
  private configCache: Map<string, any> = new Map();
  private watchedFiles: Set<string> = new Set();

  /**
   * 加载系统配置
   */
  async loadSystemConfig(configPath?: string): Promise<SystemConfiguration> {
    const defaultPath = path.join(process.cwd(), DEFAULT_FILE_PATHS.configFile);
    const targetPath = configPath || defaultPath;

    try {
      if (await fs.pathExists(targetPath)) {
        const configData = await this.loadConfigFile(targetPath);
        return this.mergeConfigs(DEFAULT_SYSTEM_CONFIG, configData);
      }
    } catch (error) {
      console.warn(`Failed to load config from ${targetPath}:`, error);
    }

    return DEFAULT_SYSTEM_CONFIG;
  }

  /**
   * 加载规则配置
   */
  async loadRules(rulesPath?: string): Promise<Rule[]> {
    const defaultPath = path.join(process.cwd(), DEFAULT_FILE_PATHS.rulesDirectory);
    const targetPath = rulesPath || defaultPath;

    const rules: Rule[] = [];

    try {
      if (await fs.pathExists(targetPath)) {
        const files = await fs.readdir(targetPath);
        const yamlFiles = files.filter(file => 
          file.endsWith('.yaml') || file.endsWith('.yml')
        );

        for (const file of yamlFiles) {
          const filePath = path.join(targetPath, file);
          try {
            const rulesData = await this.loadConfigFile(filePath);
            const parsedRules = this.parseRulesFromConfig(rulesData, file);
            rules.push(...parsedRules);
          } catch (error) {
            console.error(`Failed to load rules from ${filePath}:`, error);
          }
        }
      }
    } catch (error) {
      console.error(`Failed to load rules from directory ${targetPath}:`, error);
    }

    return rules;
  }

  /**
   * 保存配置到文件
   */
  async saveConfig(config: any, filePath: string): Promise<void> {
    try {
      await fs.ensureDir(path.dirname(filePath));
      
      const extension = path.extname(filePath).toLowerCase();
      let content: string;

      if (extension === '.yaml' || extension === '.yml') {
        content = yaml.stringify(config, { indent: 2 });
      } else {
        content = JSON.stringify(config, null, 2);
      }

      await fs.writeFile(filePath, content, 'utf8');
      this.configCache.delete(filePath);
    } catch (error) {
      throw new Error(`Failed to save config to ${filePath}: ${error}`);
    }
  }

  /**
   * 监听配置文件变化
   */
  watchConfigFile(filePath: string, callback: (config: any) => void): void {
    if (this.watchedFiles.has(filePath)) {
      return;
    }

    this.watchedFiles.add(filePath);

    fs.watchFile(filePath, { interval: 1000 }, async () => {
      try {
        const config = await this.loadConfigFile(filePath);
        callback(config);
      } catch (error) {
        console.error(`Error reloading config from ${filePath}:`, error);
      }
    });
  }

  /**
   * 停止监听配置文件
   */
  unwatchConfigFile(filePath: string): void {
    if (this.watchedFiles.has(filePath)) {
      fs.unwatchFile(filePath);
      this.watchedFiles.delete(filePath);
    }
  }

  /**
   * 验证配置
   */
  validateConfig(config: SystemConfiguration): boolean {
    try {
      // 验证必需字段
      if (!config.database || !config.cache || !config.logging) {
        return false;
      }

      // 验证数据库配置
      if (!['memory', 'file', 'sqlite', 'postgresql'].includes(config.database.type)) {
        return false;
      }

      // 验证日志级别
      if (!Object.values(LogLevel).includes(config.logging.level)) {
        return false;
      }

      // 验证缓存策略
      if (!['lru', 'fifo', 'lfu'].includes(config.cache.strategy)) {
        return false;
      }

      return true;
    } catch (error) {
      console.error('Config validation error:', error);
      return false;
    }
  }

  /**
   * 获取环境变量配置
   */
  getEnvironmentConfig(): Partial<SystemConfiguration> {
    const envConfig: Partial<SystemConfiguration> = {};

    // 数据库配置
    if (process.env['DB_TYPE']) {
      const dbConfig = envConfig.database || {} as DatabaseConfig;
      dbConfig.type = process.env['DB_TYPE'] as 'memory' | 'file' | 'sqlite' | 'postgresql';
      envConfig.database = dbConfig;
    }
    if (process.env['DB_CONNECTION_STRING']) {
      const dbConfig = envConfig.database || {} as DatabaseConfig;
      dbConfig.connectionString = process.env['DB_CONNECTION_STRING'];
      envConfig.database = dbConfig; 
      }

    // 日志配置
    if (process.env['LOG_LEVEL']) {
      const logConfig = envConfig.logging || {} as LoggingConfig;
      logConfig.level = process.env['LOG_LEVEL'] as LogLevel;
      envConfig.logging = logConfig;
    }

    // 性能配置
    if (process.env['MAX_CONCURRENT_OPERATIONS']) {
      const perfConfig = envConfig.performance || {} as PerformanceConfig;
      perfConfig.maxConcurrentOperations = parseInt(process.env['MAX_CONCURRENT_OPERATIONS'], 10);
      envConfig.performance = perfConfig;
    }

    return envConfig;
  }

  /**
   * 加载配置文件
   */
  private async loadConfigFile(filePath: string): Promise<SystemConfiguration> {
    if (this.configCache.has(filePath)) {
      return this.configCache.get(filePath)!;
    }

    const content = await fs.readFile(filePath, 'utf8');
    const extension = path.extname(filePath).toLowerCase();

    let config: SystemConfiguration;
    if (extension === '.yaml' || extension === '.yml') {
      config = yaml.parse(content) as SystemConfiguration;
    } else {
      config = JSON.parse(content) as SystemConfiguration;
    }

    this.configCache.set(filePath, config);
    return config;
  }

  /**
   * 合并配置对象
   */
  private mergeConfigs(defaultConfig: SystemConfiguration, userConfig: Partial<SystemConfiguration>): SystemConfiguration {
    const merged = { ...defaultConfig };

    for (const key in userConfig) {
      if (userConfig.hasOwnProperty(key)) {
        const userValue = userConfig[key as keyof Partial<SystemConfiguration>];
        const mergedValue = merged[key as keyof SystemConfiguration];
        
        if (
          typeof userValue === 'object' &&
          userValue !== null &&
          !Array.isArray(userValue) &&
          typeof mergedValue === 'object' &&
          mergedValue !== null &&
          !Array.isArray(mergedValue)
        ) {
          (merged as Record<string, any>)[key] = this.mergeConfigs(
            mergedValue as unknown as SystemConfiguration, 
            userValue as unknown as SystemConfiguration
          );
        } else {
          (merged as Record<string, any>)[key] = userValue;
        }
      }
    }

    return merged;
  }

  /**
   * 从配置中解析规则
   */
  private parseRulesFromConfig(config: any, fileName: string): Rule[] {
    const rules: Rule[] = [];

    if (config.rules && Array.isArray(config.rules)) {
      config.rules.forEach((ruleData: any, index: number) => {
        try {
          const rule: Rule = {
            id: ruleData.id || `${fileName}-${index}`,
            name: ruleData.name || `Rule ${index + 1}`,
            description: ruleData.description || '',
            category: ruleData.category || 'personal',
            priority: ruleData.priority || 1,
            conditions: ruleData.conditions || [],
            actions: ruleData.actions || [],
            isActive: ruleData.isActive !== false,
            createdAt: new Date(),
            updatedAt: new Date()
          };

          rules.push(rule);
        } catch (error) {
          console.error(`Failed to parse rule ${index} from ${fileName}:`, error);
        }
      });
    }

    return rules;
  }

  /**
   * 清理缓存
   */
  clearCache(): void {
    this.configCache.clear();
  }

  /**
   * 获取缓存统计
   */
  getCacheStats(): { size: number; keys: string[] } {
    return {
      size: this.configCache.size,
      keys: Array.from(this.configCache.keys())
    };
  }

  /**
   * 销毁配置加载器
   */
  destroy(): void {
    this.clearCache();
    this.watchedFiles.forEach(filePath => {
      fs.unwatchFile(filePath);
    });
    this.watchedFiles.clear();
  }
}