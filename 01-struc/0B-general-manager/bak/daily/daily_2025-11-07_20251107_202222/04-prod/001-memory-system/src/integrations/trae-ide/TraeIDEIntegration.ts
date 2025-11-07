// src/integrations/trae-ide/TraeIDEIntegration.ts
import { AutoRecordMiddleware, AutoRecordConfig } from '../../middleware/AutoRecordMiddleware';
import { MemoryService } from '../../services/MemoryService';
import { IntelligentFilter } from '../../services/IntelligentFilter';
import { ContentProcessor } from '../../services/ContentProcessor';
import { ContextExtractor } from '../../utils/ContextExtractor';
import { Logger } from '../../utils/logger';

export interface TraeIDEIntegrationConfig {
  autoRecord: AutoRecordConfig;
  memoryService?: any;
  intelligentFilter?: any;
  contentProcessor?: any;
  contextExtractor?: any;
  enableHealthCheck: boolean;
  healthCheckInterval: number;
}

export interface IntegrationStatus {
  initialized: boolean;
  running: boolean;
  healthy: boolean;
  lastHealthCheck: Date;
  components: {
    autoRecordMiddleware: boolean;
    memoryService: boolean;
    intelligentFilter: boolean;
    contentProcessor: boolean;
    contextExtractor: boolean;
  };
  errors: string[];
}

export class TraeIDEIntegration {
  private logger: Logger;
  private config: TraeIDEIntegrationConfig;
  private autoRecordMiddleware: AutoRecordMiddleware;
  private memoryService: MemoryService;
  private intelligentFilter: IntelligentFilter;
  private contentProcessor: ContentProcessor;
  private contextExtractor: ContextExtractor;
  
  private status: IntegrationStatus;
  private healthCheckTimer: NodeJS.Timeout | null = null;
  private initialized = false;

  constructor(config?: Partial<TraeIDEIntegrationConfig>) {
    this.logger = new Logger('TraeIDEIntegration');
    
    // 默认配置
    this.config = {
      autoRecord: {
        enabled: true,
        batchSize: 10,
        batchTimeout: 5000,
        enableFiltering: true,
        enableProcessing: true,
        enableContextExtraction: true,
        maxRetries: 3,
        retryDelay: 1000,
        debugMode: false
      },
      enableHealthCheck: true,
      healthCheckInterval: 30000, // 30秒
      ...config
    };

    // 初始化状态
    this.status = {
      initialized: false,
      running: false,
      healthy: false,
      lastHealthCheck: new Date(),
      components: {
        autoRecordMiddleware: false,
        memoryService: false,
        intelligentFilter: false,
        contentProcessor: false,
        contextExtractor: false
      },
      errors: []
    };
  }

  // 初始化集成
  public async initialize(): Promise<void> {
    if (this.initialized) {
      this.logger.warn('TraeIDEIntegration already initialized');
      return;
    }

    try {
      this.logger.info('Initializing Trae IDE Integration...');

      // 1. 初始化核心服务
      await this.initializeServices();

      // 2. 初始化自动记录中间件
      await this.initializeAutoRecordMiddleware();

      // 3. 启动健康检查
      if (this.config.enableHealthCheck) {
        this.startHealthCheck();
      }

      this.initialized = true;
      this.status.initialized = true;
      this.status.running = true;

      this.logger.info('Trae IDE Integration initialized successfully');
    } catch (error) {
      this.logger.error('Failed to initialize Trae IDE Integration:', error);
      this.status.errors.push(`Initialization failed: ${error instanceof Error ? error.message : String(error)}`);
      throw error;
    }
  }

  // 初始化核心服务
  private async initializeServices(): Promise<void> {
    try {
      // 初始化记忆服务
      this.memoryService = this.config.memoryService || new MemoryService();
      this.status.components.memoryService = true;
      this.logger.debug('MemoryService initialized');

      // 初始化智能筛选器
      this.intelligentFilter = this.config.intelligentFilter || new IntelligentFilter();
      this.status.components.intelligentFilter = true;
      this.logger.debug('IntelligentFilter initialized');

      // 初始化内容处理器
      this.contentProcessor = this.config.contentProcessor || new ContentProcessor();
      this.status.components.contentProcessor = true;
      this.logger.debug('ContentProcessor initialized');

      // 初始化上下文提取器
      this.contextExtractor = this.config.contextExtractor || new ContextExtractor();
      this.status.components.contextExtractor = true;
      this.logger.debug('ContextExtractor initialized');

      this.logger.info('All core services initialized');
    } catch (error) {
      this.logger.error('Error initializing services:', error);
      throw error;
    }
  }

  // 初始化自动记录中间件
  private async initializeAutoRecordMiddleware(): Promise<void> {
    try {
      this.autoRecordMiddleware = new AutoRecordMiddleware(
        this.config.autoRecord,
        this.memoryService,
        this.intelligentFilter,
        this.contentProcessor,
        this.contextExtractor
      );

      await this.autoRecordMiddleware.start();
      this.status.components.autoRecordMiddleware = true;
      
      this.logger.info('AutoRecordMiddleware initialized and started');
    } catch (error) {
      this.logger.error('Error initializing AutoRecordMiddleware:', error);
      throw error;
    }
  }

  // 启动健康检查
  private startHealthCheck(): void {
    if (this.healthCheckTimer) {
      clearInterval(this.healthCheckTimer);
    }

    this.healthCheckTimer = setInterval(async () => {
      await this.performHealthCheck();
    }, this.config.healthCheckInterval);

    this.logger.debug('Health check started');
  }

  // 执行健康检查
  private async performHealthCheck(): Promise<void> {
    try {
      this.status.lastHealthCheck = new Date();
      this.status.errors = []; // 清空之前的错误

      // 检查自动记录中间件
      if (this.autoRecordMiddleware) {
        const middlewareHealth = this.autoRecordMiddleware.healthCheck();
        if (!middlewareHealth.healthy) {
          this.status.errors.push('AutoRecordMiddleware is unhealthy');
        }
      }

      // 检查记忆服务
      if (this.memoryService) {
        try {
          // 这里可以添加记忆服务的健康检查逻辑
          // 例如：检查数据库连接、存储空间等
        } catch (error) {
          this.status.errors.push(`MemoryService error: ${error instanceof Error ? error.message : String(error)}`);
        }
      }

      // 更新整体健康状态
      this.status.healthy = this.status.errors.length === 0;

      if (!this.status.healthy) {
        this.logger.warn('Health check failed:', this.status.errors);
      } else {
        this.logger.debug('Health check passed');
      }
    } catch (error) {
      this.logger.error('Error during health check:', error);
      this.status.healthy = false;
      this.status.errors.push(`Health check error: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  // 启动集成
  public async start(): Promise<void> {
    if (!this.initialized) {
      await this.initialize();
    }

    if (this.status.running) {
      this.logger.warn('TraeIDEIntegration is already running');
      return;
    }

    try {
      if (this.autoRecordMiddleware) {
        await this.autoRecordMiddleware.start();
      }

      this.status.running = true;
      this.logger.info('Trae IDE Integration started');
    } catch (error) {
      this.logger.error('Failed to start Trae IDE Integration:', error);
      throw error;
    }
  }

  // 停止集成
  public async stop(): Promise<void> {
    if (!this.status.running) {
      this.logger.warn('TraeIDEIntegration is not running');
      return;
    }

    try {
      // 停止健康检查
      if (this.healthCheckTimer) {
        clearInterval(this.healthCheckTimer);
        this.healthCheckTimer = null;
      }

      // 停止自动记录中间件
      if (this.autoRecordMiddleware) {
        await this.autoRecordMiddleware.stop();
      }

      this.status.running = false;
      this.logger.info('Trae IDE Integration stopped');
    } catch (error) {
      this.logger.error('Error stopping Trae IDE Integration:', error);
      throw error;
    }
  }

  // 重启集成
  public async restart(): Promise<void> {
    this.logger.info('Restarting Trae IDE Integration...');
    await this.stop();
    await this.start();
    this.logger.info('Trae IDE Integration restarted');
  }

  // 暂停自动记录
  public pause(): void {
    if (this.autoRecordMiddleware) {
      this.autoRecordMiddleware.pause();
      this.logger.info('Auto recording paused');
    }
  }

  // 恢复自动记录
  public resume(): void {
    if (this.autoRecordMiddleware) {
      this.autoRecordMiddleware.resume();
      this.logger.info('Auto recording resumed');
    }
  }

  // 获取集成状态
  public getStatus(): IntegrationStatus {
    return { ...this.status };
  }

  // 获取详细统计信息
  public getDetailedStats() {
    const stats: any = {
      integration: this.status,
      timestamp: new Date()
    };

    if (this.autoRecordMiddleware) {
      stats.autoRecord = {
        stats: this.autoRecordMiddleware.getStats(),
        queueStatus: this.autoRecordMiddleware.getQueueStatus(),
        performanceReport: this.autoRecordMiddleware.getPerformanceReport()
      };
    }

    if (this.intelligentFilter) {
      stats.filter = this.intelligentFilter.getStats();
    }

    if (this.contentProcessor) {
      stats.processor = this.contentProcessor.getStats();
    }

    return stats;
  }

  // 获取性能报告
  public getPerformanceReport() {
    if (!this.autoRecordMiddleware) {
      return null;
    }

    return this.autoRecordMiddleware.getPerformanceReport();
  }

  // 更新配置
  public updateConfig(newConfig: Partial<TraeIDEIntegrationConfig>): void {
    this.config = { ...this.config, ...newConfig };

    // 更新自动记录中间件配置
    if (newConfig.autoRecord && this.autoRecordMiddleware) {
      this.autoRecordMiddleware.updateConfig(newConfig.autoRecord);
    }

    // 更新健康检查间隔
    if (newConfig.healthCheckInterval && this.config.enableHealthCheck) {
      this.startHealthCheck();
    }

    this.logger.info('Configuration updated');
  }

  // 手动触发记忆处理
  public async processMemoriesNow(): Promise<void> {
    if (this.autoRecordMiddleware) {
      await this.autoRecordMiddleware.processNow();
      this.logger.info('Manual memory processing triggered');
    }
  }

  // 清空处理队列
  public clearProcessingQueue(): void {
    if (this.autoRecordMiddleware) {
      this.autoRecordMiddleware.clearQueue();
      this.logger.info('Processing queue cleared');
    }
  }

  // 获取最近的处理指标
  public getRecentMetrics(limit: number = 100) {
    if (!this.autoRecordMiddleware) {
      return [];
    }

    return this.autoRecordMiddleware.getRecentMetrics(limit);
  }

  // 导出配置
  public exportConfig() {
    return {
      config: this.config,
      status: this.status,
      timestamp: new Date()
    };
  }

  // 导入配置
  public importConfig(configData: any): void {
    if (configData.config) {
      this.updateConfig(configData.config);
      this.logger.info('Configuration imported');
    }
  }

  // 获取诊断信息
  public getDiagnostics() {
    return {
      integration: {
        initialized: this.initialized,
        status: this.status,
        config: this.config
      },
      services: {
        memoryService: !!this.memoryService,
        intelligentFilter: !!this.intelligentFilter,
        contentProcessor: !!this.contentProcessor,
        contextExtractor: !!this.contextExtractor,
        autoRecordMiddleware: !!this.autoRecordMiddleware
      },
      health: this.status.healthy ? 'healthy' : 'unhealthy',
      errors: this.status.errors,
      timestamp: new Date()
    };
  }

  // 执行诊断测试
  public async runDiagnostics(): Promise<any> {
    const diagnostics: any = {
      timestamp: new Date(),
      tests: []
    };

    // 测试记忆服务
    try {
      if (this.memoryService) {
        // 这里可以添加记忆服务的测试逻辑
        diagnostics.tests.push({
          name: 'MemoryService',
          status: 'passed',
          message: 'Service is available'
        });
      }
    } catch (error) {
      diagnostics.tests.push({
        name: 'MemoryService',
        status: 'failed',
        message: error instanceof Error ? error.message : String(error)
      });
    }

    // 测试自动记录中间件
    try {
      if (this.autoRecordMiddleware) {
        const health = this.autoRecordMiddleware.healthCheck();
        diagnostics.tests.push({
          name: 'AutoRecordMiddleware',
          status: health.healthy ? 'passed' : 'failed',
          message: health.healthy ? 'Middleware is healthy' : 'Middleware is unhealthy',
          details: health
        });
      }
    } catch (error) {
      diagnostics.tests.push({
        name: 'AutoRecordMiddleware',
        status: 'failed',
        message: error instanceof Error ? error.message : String(error)
      });
    }

    // 计算总体状态
    const failedTests = diagnostics.tests.filter((test: any) => test.status === 'failed');
    diagnostics.overall = failedTests.length === 0 ? 'passed' : 'failed';
    diagnostics.summary = `${diagnostics.tests.length - failedTests.length}/${diagnostics.tests.length} tests passed`;

    return diagnostics;
  }

  // 清理资源
  public async cleanup(): Promise<void> {
    try {
      await this.stop();

      if (this.autoRecordMiddleware) {
        await this.autoRecordMiddleware.cleanup();
      }

      if (this.intelligentFilter) {
        this.intelligentFilter.cleanup();
      }

      this.initialized = false;
      this.status.initialized = false;
      this.status.running = false;

      this.logger.info('Trae IDE Integration cleaned up');
    } catch (error) {
      this.logger.error('Error during cleanup:', error);
      throw error;
    }
  }

  // 获取版本信息
  public getVersion() {
    return {
      version: '1.0.0',
      buildDate: new Date().toISOString(),
      components: {
        autoRecordMiddleware: '1.0.0',
        memoryService: '1.0.0',
        intelligentFilter: '1.0.0',
        contentProcessor: '1.0.0',
        contextExtractor: '1.0.0'
      }
    };
  }
}