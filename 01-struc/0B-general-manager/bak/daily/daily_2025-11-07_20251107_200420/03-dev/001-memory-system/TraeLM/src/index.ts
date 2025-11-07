/**
 * JS003 - Trae长记忆功能实施项目
 * 主入口文件
 * 
 * @description 导出项目的核心功能模块，包括规则系统、知识图谱记忆和智能体增强功能
 * @author 高级软件专家
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
import type { Memory, RetrievalQuery, RetrievalResult, EnhancementContext, EnhancementResult } from './types/base';

/**
 * 长期记忆系统主类
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
      
      this.isInitialized = true;
      
      logger.info('Long-term memory system initialized successfully', {}, 'LongTermMemorySystem');
      
    } catch (error) {
      logger.error('Failed to initialize long-term memory system', { error }, 'LongTermMemorySystem');
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
  } {
    this.ensureInitialized();
    
    return {
      rules: this.ruleManager.getStats(),
      knowledge: this.knowledgeGraphManager.getStats(),
      memory: this.memoryRetrievalManager.getStats(),
      performance: this.performanceMonitor.getPerformanceReport()
    };
  }

  /**
   * 销毁系统
   */
  public async destroy(): Promise<void> {
    if (!this.isInitialized) return;

    try {
      // 停止性能监控
      this.performanceMonitor.stopMonitoring();
      
      // 销毁各个组件
      await this.memoryRetrievalManager.destroy();
      await this.knowledgeGraphManager.destroy();
      await this.ruleManager.destroy();
      await this.configManager.destroy();
      
      this.performanceMonitor.destroy();
      
      this.isInitialized = false;
      
      logger.info('Long-term memory system destroyed successfully', {}, 'LongTermMemorySystem');
      
    } catch (error) {
      logger.error('Failed to destroy long-term memory system', { error }, 'LongTermMemorySystem');
      throw error;
    }
  }

  private ensureInitialized(): void {
    if (!this.isInitialized) {
      throw new Error('Long-term memory system is not initialized. Call initialize() first.');
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
export const PROJECT_NAME = 'JS003-Trae长记忆功能实施';

/**
 * 项目描述
 */
export const PROJECT_DESCRIPTION = 'Trae平台长记忆功能实施，包括规则系统和知识图谱记忆';

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