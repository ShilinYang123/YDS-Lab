/**
 * YDS-Lab 统一长记忆系统
 * 主入口文件
 * 
 * @description 基于Trae长记忆功能的企业级部署，提供统一的记忆管理服务
 * @author YDS-Lab Team
 * @version 1.0.0
 */

// 配置模块
export * from './config';

// 服务模块
export * from './services';

// 工具模块
export * from './utils';

// 类型定义
export * from './types';

// 导入核心组件用于主类
import { ConfigurationManager } from './config';
import { RuleManager } from './services/rule-system';
import { KnowledgeGraphManager } from './services/knowledge-graph';
import { MemoryRetrievalManager } from './services/memory-retrieval';
import { PerformanceMonitor, logger } from './utils';
import { TraeIDEIntegration, TraeIDEIntegrationConfig } from './integrations/trae-ide/TraeIDEIntegration';
import type { Memory, RetrievalQuery, RetrievalResult, EnhancementContext, EnhancementResult } from './types/base';

/**
 * YDS-Lab 长期记忆系统主类
 * 
 * 提供统一的接口来管理整个长期记忆系统，包括：
 * - 配置管理
 * - 规则系统
 * - 知识图谱
 * - 记忆检索
 * - 智能体增强
 * - 性能监控
 */
export class LongTermMemorySystem {
  private configManager: ConfigurationManager;
  private ruleManager: RuleManager;
  private knowledgeGraphManager: KnowledgeGraphManager;
  private memoryRetrievalManager: MemoryRetrievalManager;
  private performanceMonitor: PerformanceMonitor;
  private traeIDEIntegration: TraeIDEIntegration | null = null;
  private isInitialized: boolean = false;
  private configPath: string | undefined;

  constructor(configPath?: string) {
    this.configManager = new ConfigurationManager();
    this.ruleManager = new RuleManager(this.configManager);
    
    // 创建知识图谱和记忆管理器
    const knowledgeGraph = new (require('./services/knowledge-graph/graph').KnowledgeGraph)();
    const memoryManager = new (require('./services/knowledge-graph/memory').MemoryManager)(knowledgeGraph);
    
    this.knowledgeGraphManager = new KnowledgeGraphManager(memoryManager, knowledgeGraph);
    
    // 初始化记忆检索管理器
    this.memoryRetrievalManager = new MemoryRetrievalManager(
      memoryManager
    );
    this.performanceMonitor = new PerformanceMonitor();
    
    // 存储配置路径以便在初始化时使用
    this.configPath = configPath;
  }

  /**
   * 初始化长期记忆系统
   */
  public async initialize(): Promise<void> {
    if (this.isInitialized) {
      throw new Error('Long-term memory system is already initialized');
    }

    try {
      // 初始化配置
      await this.configManager.initialize(this.configPath);
      
      // 初始化规则系统
      await this.ruleManager.initialize();
      
      // 知识图谱管理器在构造函数中已经初始化，无需单独初始化
      
      // 初始化记忆检索
      await this.memoryRetrievalManager.initialize();
      
      // 启动性能监控
      this.performanceMonitor.startMonitoring();
      
      // 初始化Trae IDE集成（自动记录功能）
      await this.initializeTraeIDEIntegration();
      
      this.isInitialized = true;
      
      logger.info('YDS-Lab memory system initialized successfully', {}, 'LongTermMemorySystem');
      
    } catch (error) {
      logger.error('Failed to initialize YDS-Lab memory system', { error }, 'LongTermMemorySystem');
      throw error;
    }
  }

  /**
   * 获取配置管理器
   */
  public getConfigManager(): ConfigurationManager {
    return this.configManager;
  }

  /**
   * 获取规则管理器
   */
  public getRuleManager(): RuleManager {
    return this.ruleManager;
  }

  /**
   * 获取知识图谱管理器
   */
  public getKnowledgeGraphManager(): KnowledgeGraphManager {
    return this.knowledgeGraphManager;
  }

  /**
   * 获取记忆检索管理器
   */
  public getMemoryRetrievalManager(): MemoryRetrievalManager {
    return this.memoryRetrievalManager;
  }

  /**
   * 获取性能监控器
   */
  public getPerformanceMonitor(): PerformanceMonitor {
    return this.performanceMonitor;
  }

  /**
   * 获取Trae IDE集成组件
   */
  public getTraeIDEIntegration(): TraeIDEIntegration | null {
    return this.traeIDEIntegration;
  }

  /**
   * 存储记忆
   */
  public async storeMemory(memory: Omit<Memory, 'id' | 'createdAt' | 'updatedAt'>): Promise<string> {
    this.ensureInitialized();
    
    return this.performanceMonitor.measureAsync('storeMemory', async () => {
      // 创建完整的Memory对象
      const fullMemory: Memory = {
        ...memory,
        id: `memory_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        createdAt: new Date(),
        updatedAt: new Date()
      };
      
      const success = await this.knowledgeGraphManager.storeMemoryWithKnowledge(fullMemory);
      if (!success) {
        throw new Error('Failed to store memory');
      }
      return fullMemory.id;
    });
  }

  /**
   * 检索记忆
   */
  public async retrieveMemories(query: RetrievalQuery): Promise<RetrievalResult> {
    this.ensureInitialized();
    
    return this.performanceMonitor.measureAsync('retrieveMemories', async () => {
      return await this.memoryRetrievalManager.retrieveMemories(query);
    });
  }

  /**
   * 增强智能体
   */
  public async enhanceAgent(agent: import('./types/base').Agent, context: EnhancementContext): Promise<EnhancementResult> {
    this.ensureInitialized();
    
    return this.performanceMonitor.measureAsync('enhanceAgent', async () => {
      return await this.memoryRetrievalManager.enhanceAgent(agent, context);
    });
  }

  /**
   * 获取系统统计信息
   */
  public getSystemStats(): {
    rules: any;
    knowledge: any;
    memory: any;
    performance: any;
    traeIDEIntegration?: any;
  } {
    this.ensureInitialized();
    
    const stats: any = {
      rules: this.ruleManager.getStats(),
      knowledge: this.knowledgeGraphManager.getStats(),
      memory: this.memoryRetrievalManager.getStats(),
      performance: this.performanceMonitor.getPerformanceReport()
    };

    // 添加Trae IDE集成统计信息
    if (this.traeIDEIntegration) {
      stats.traeIDEIntegration = this.traeIDEIntegration.getDetailedStats();
    }

    return stats;
  }

  /**
   * 销毁系统
   */
  public async destroy(): Promise<void> {
    if (!this.isInitialized) return;

    try {
      // 停止性能监控
      this.performanceMonitor.stopMonitoring();
      
      // 停止并清理Trae IDE集成
      if (this.traeIDEIntegration) {
        await this.traeIDEIntegration.cleanup();
        this.traeIDEIntegration = null;
      }
      
      // 销毁各个组件
      await this.memoryRetrievalManager.destroy();
      await this.knowledgeGraphManager.destroy();
      await this.ruleManager.destroy();
      await this.configManager.destroy();
      
      this.performanceMonitor.destroy();
      
      this.isInitialized = false;
      
      logger.info('YDS-Lab memory system destroyed successfully', {}, 'LongTermMemorySystem');
      
    } catch (error) {
      logger.error('Failed to destroy YDS-Lab memory system', { error }, 'LongTermMemorySystem');
      throw error;
    }
  }

  private ensureInitialized(): void {
    if (!this.isInitialized) {
      throw new Error('Long-term memory system is not initialized. Call initialize() first.');
    }
  }

  /**
   * 初始化Trae IDE集成
   */
  private async initializeTraeIDEIntegration(): Promise<void> {
    try {
      // 从配置中获取自动记录设置
      const config = this.configManager.getSystemConfig();
      const autoRecordEnabled = config.auto_record_operations || false;

      if (autoRecordEnabled) {
        // 创建Trae IDE集成配置
        const integrationConfig: Partial<TraeIDEIntegrationConfig> = {
          autoRecord: {
            enabled: true,
            batchSize: config.batch_size || 10,
            batchTimeout: config.batch_timeout || 5000,
            enableFiltering: true,
            enableProcessing: true,
            enableContextExtraction: true,
            maxRetries: 3,
            retryDelay: 1000,
            debugMode: config.debug_mode || false
          },
          enableHealthCheck: true,
          healthCheckInterval: 30000
        };

        // 初始化Trae IDE集成
        this.traeIDEIntegration = new TraeIDEIntegration(integrationConfig);
        await this.traeIDEIntegration.initialize();
        await this.traeIDEIntegration.start();

        logger.info('Trae IDE Integration initialized and started', {}, 'LongTermMemorySystem');
      } else {
        logger.info('Auto record operations disabled, skipping Trae IDE Integration', {}, 'LongTermMemorySystem');
      }
    } catch (error) {
      logger.error('Failed to initialize Trae IDE Integration', { error }, 'LongTermMemorySystem');
      // 不抛出错误，允许系统在没有自动记录功能的情况下继续运行
    }
  }

  /**
   * 启用自动记录功能
   */
  public async enableAutoRecord(): Promise<void> {
    this.ensureInitialized();

    if (this.traeIDEIntegration) {
      this.traeIDEIntegration.resume();
      logger.info('Auto record enabled', {}, 'LongTermMemorySystem');
    } else {
      // 如果集成尚未初始化，则初始化它
      await this.initializeTraeIDEIntegration();
    }
  }

  /**
   * 禁用自动记录功能
   */
  public disableAutoRecord(): void {
    if (this.traeIDEIntegration) {
      this.traeIDEIntegration.pause();
      logger.info('Auto record disabled', {}, 'LongTermMemorySystem');
    }
  }

  /**
   * 获取自动记录状态
   */
  public getAutoRecordStatus(): { enabled: boolean; running: boolean; healthy: boolean } {
    if (!this.traeIDEIntegration) {
      return { enabled: false, running: false, healthy: false };
    }

    const status = this.traeIDEIntegration.getStatus();
    return {
      enabled: status.initialized,
      running: status.running,
      healthy: status.healthy
    };
  }

  /**
   * 手动触发记忆处理
   */
  public async processMemoriesNow(): Promise<void> {
    this.ensureInitialized();

    if (this.traeIDEIntegration) {
      await this.traeIDEIntegration.processMemoriesNow();
      logger.info('Manual memory processing triggered', {}, 'LongTermMemorySystem');
    } else {
      logger.warn('Trae IDE Integration not available for manual processing', {}, 'LongTermMemorySystem');
    }
  }
}

// 导出默认实例
export const longTermMemorySystem = new LongTermMemorySystem();

/**
 * 项目版本信息
 */
export const VERSION = '1.0.0';

/**
 * 项目名称
 */
export const PROJECT_NAME = 'YDS-Lab统一长记忆系统';

/**
 * 项目描述
 */
export const PROJECT_DESCRIPTION = 'YDS-Lab企业级长记忆系统，基于Trae平台长记忆功能';

/**
 * 默认导出项目信息
 */
export default {
  VERSION,
  PROJECT_NAME,
  PROJECT_DESCRIPTION,
  LongTermMemorySystem,
  longTermMemorySystem,
};