// src/middleware/AutoRecordMiddleware.ts
import { InteractionHook, InteractionEvent } from '../integrations/trae-ide/hooks/InteractionHook';
import { MemoryService, MemoryData } from '../services/MemoryService';
import { IntelligentFilter, FilterResult } from '../services/IntelligentFilter';
import { ContentProcessor, ProcessingResult } from '../services/ContentProcessor';
import { ContextExtractor } from '../utils/ContextExtractor';
import { Logger } from '../utils/logger';

export interface AutoRecordConfig {
  enabled: boolean;
  batchSize: number;
  batchTimeout: number;
  enableFiltering: boolean;
  enableProcessing: boolean;
  enableContextExtraction: boolean;
  maxRetries: number;
  retryDelay: number;
  debugMode: boolean;
}

export interface RecordingStats {
  totalEvents: number;
  processedEvents: number;
  filteredEvents: number;
  rejectedEvents: number;
  errorEvents: number;
  averageProcessingTime: number;
  lastProcessedAt: Date;
}

export interface RecordingMetrics {
  eventType: string;
  processingTime: number;
  filterResult: string;
  success: boolean;
  error?: string;
  timestamp: Date;
}

export class AutoRecordMiddleware {
  private logger: Logger;
  private config: AutoRecordConfig;
  private interactionHook: InteractionHook;
  private memoryService: MemoryService;
  private intelligentFilter: IntelligentFilter;
  private contentProcessor: ContentProcessor;
  private contextExtractor: ContextExtractor;
  
  private eventQueue: InteractionEvent[] = [];
  private processingQueue: Promise<void>[] = [];
  private batchTimer: NodeJS.Timeout | null = null;
  private isProcessing = false;
  private stats: RecordingStats;
  private metrics: RecordingMetrics[] = [];

  constructor(
    config?: Partial<AutoRecordConfig>,
    memoryService?: MemoryService,
    intelligentFilter?: IntelligentFilter,
    contentProcessor?: ContentProcessor,
    contextExtractor?: ContextExtractor
  ) {
    this.logger = new Logger('AutoRecordMiddleware');
    this.config = {
      enabled: true,
      batchSize: 10,
      batchTimeout: 5000, // 5秒
      enableFiltering: true,
      enableProcessing: true,
      enableContextExtraction: true,
      maxRetries: 3,
      retryDelay: 1000,
      debugMode: false,
      ...config
    };

    // 初始化服务
    this.memoryService = memoryService || new MemoryService();
    this.intelligentFilter = intelligentFilter || new IntelligentFilter();
    this.contentProcessor = contentProcessor || new ContentProcessor();
    this.contextExtractor = contextExtractor || new ContextExtractor();
    
    // 初始化交互钩子
    this.interactionHook = new InteractionHook();
    
    // 初始化统计信息
    this.stats = {
      totalEvents: 0,
      processedEvents: 0,
      filteredEvents: 0,
      rejectedEvents: 0,
      errorEvents: 0,
      averageProcessingTime: 0,
      lastProcessedAt: new Date()
    };

    this.initialize();
  }

  // 初始化中间件
  private async initialize() {
    try {
      if (!this.config.enabled) {
        this.logger.info('AutoRecordMiddleware is disabled');
        return;
      }

      // 设置事件监听器
      this.setupEventListeners();

      // 启动批处理定时器
      this.startBatchTimer();

      this.logger.info('AutoRecordMiddleware initialized successfully');
    } catch (error) {
      this.logger.error('Failed to initialize AutoRecordMiddleware:', error);
      throw error;
    }
  }

  // 设置事件监听器
  private setupEventListeners() {
    // 监听所有交互事件
    this.interactionHook.on('userInput', (event) => this.handleEvent(event));
    this.interactionHook.on('agentResponse', (event) => this.handleEvent(event));
    this.interactionHook.on('codeExecution', (event) => this.handleEvent(event));
    this.interactionHook.on('fileChange', (event) => this.handleEvent(event));
    this.interactionHook.on('errorOccurred', (event) => this.handleEvent(event));
    this.interactionHook.on('sessionEnd', (event) => this.handleEvent(event));

    // 监听内存服务事件
    this.memoryService.on('memoryStored', (memory) => {
      this.logger.debug(`Memory stored: ${memory.id}`);
    });

    this.memoryService.on('error', (error) => {
      this.logger.error('MemoryService error:', error);
      this.stats.errorEvents++;
    });

    this.logger.debug('Event listeners set up');
  }

  // 处理事件
  private async handleEvent(event: InteractionEvent) {
    try {
      if (!this.config.enabled) return;

      this.stats.totalEvents++;
      
      if (this.config.debugMode) {
        this.logger.debug(`Received event: ${event.type}`, event);
      }

      // 添加到事件队列
      this.eventQueue.push(event);

      // 检查是否需要立即处理
      if (this.shouldProcessImmediately(event)) {
        await this.processEventQueue();
      } else if (this.eventQueue.length >= this.config.batchSize) {
        await this.processEventQueue();
      }
    } catch (error) {
      this.logger.error('Error handling event:', error);
      this.stats.errorEvents++;
    }
  }

  // 判断是否需要立即处理
  private shouldProcessImmediately(event: InteractionEvent): boolean {
    // 高优先级事件立即处理
    const highPriorityTypes = ['errorOccurred', 'sessionEnd'];
    return highPriorityTypes.includes(event.type) || event.priority === 'high';
  }

  // 启动批处理定时器
  private startBatchTimer() {
    if (this.batchTimer) {
      clearTimeout(this.batchTimer);
    }

    this.batchTimer = setTimeout(async () => {
      if (this.eventQueue.length > 0) {
        await this.processEventQueue();
      }
      this.startBatchTimer(); // 重新启动定时器
    }, this.config.batchTimeout);
  }

  // 处理事件队列
  private async processEventQueue() {
    if (this.isProcessing || this.eventQueue.length === 0) {
      return;
    }

    this.isProcessing = true;
    const startTime = Date.now();

    try {
      // 获取要处理的事件
      const eventsToProcess = this.eventQueue.splice(0, this.config.batchSize);
      
      this.logger.debug(`Processing ${eventsToProcess.length} events`);

      // 并行处理事件
      const processingPromises = eventsToProcess.map(event => 
        this.processEvent(event).catch(error => {
          this.logger.error(`Error processing event ${event.id}:`, error);
          this.stats.errorEvents++;
          return null;
        })
      );

      const results = await Promise.all(processingPromises);
      const successfulResults = results.filter(result => result !== null);

      // 更新统计信息
      this.stats.processedEvents += successfulResults.length;
      this.stats.lastProcessedAt = new Date();
      
      const processingTime = Date.now() - startTime;
      this.updateAverageProcessingTime(processingTime);

      this.logger.debug(`Processed ${successfulResults.length}/${eventsToProcess.length} events in ${processingTime}ms`);
    } catch (error) {
      this.logger.error('Error processing event queue:', error);
      this.stats.errorEvents++;
    } finally {
      this.isProcessing = false;
    }
  }

  // 处理单个事件
  private async processEvent(event: InteractionEvent): Promise<MemoryData | null> {
    const startTime = Date.now();
    let filterResult = 'none';
    let success = false;
    let error: string | undefined;

    try {
      // 1. 转换事件为记忆数据
      let memoryData = await this.convertEventToMemory(event);
      if (!memoryData) {
        this.logger.debug(`Event ${event.id} could not be converted to memory`);
        return null;
      }

      // 2. 提取上下文信息
      if (this.config.enableContextExtraction) {
        const context = await this.contextExtractor.extractContext();
        memoryData.context = { ...memoryData.context, ...context };
      }

      // 3. 智能筛选
      if (this.config.enableFiltering) {
        const filterResultObj = await this.intelligentFilter.filterMemory(memoryData);
        filterResult = filterResultObj.action;

        if (filterResultObj.action === 'reject') {
          this.stats.rejectedEvents++;
          this.logger.debug(`Event ${event.id} rejected by filter: ${filterResultObj.reasons.join(', ')}`);
          return null;
        }

        if (filterResultObj.action === 'modify' && filterResultObj.modifiedMemory) {
          memoryData = filterResultObj.modifiedMemory;
        }

        this.stats.filteredEvents++;
      }

      // 4. 内容处理和增强
      if (this.config.enableProcessing) {
        const processingResult = await this.contentProcessor.processMemory(memoryData);
        memoryData = processingResult.processedMemory;

        // 添加处理元数据
        memoryData.metadata = {
          ...memoryData.metadata,
          processed: true,
          enhancements: processingResult.enhancements.map(e => e.type),
          processingMetrics: processingResult.metrics
        };
      }

      // 5. 存储记忆
      const storedMemory = await this.memoryService.submitMemory(memoryData);
      
      success = true;
      this.logger.debug(`Event ${event.id} successfully processed and stored as memory ${storedMemory.id}`);
      
      return storedMemory;
    } catch (err) {
      error = err instanceof Error ? err.message : String(err);
      this.logger.error(`Error processing event ${event.id}:`, err);
      throw err;
    } finally {
      // 记录处理指标
      const processingTime = Date.now() - startTime;
      this.recordMetrics({
        eventType: event.type,
        processingTime,
        filterResult,
        success,
        error,
        timestamp: new Date()
      });
    }
  }

  // 转换事件为记忆数据
  private async convertEventToMemory(event: InteractionEvent): Promise<MemoryData | null> {
    try {
      const baseMemory: MemoryData = {
        id: `memory_${event.id}_${Date.now()}`,
        type: this.mapEventTypeToMemoryType(event.type),
        content: event.data,
        timestamp: event.timestamp,
        source: 'trae-ide-auto-record',
        metadata: {
          eventId: event.id,
          eventType: event.type,
          priority: event.priority,
          autoRecorded: true,
          originalTimestamp: event.timestamp
        },
        context: event.context || {}
      };

      // 根据事件类型进行特殊处理
      switch (event.type) {
        case 'userInput':
          baseMemory.metadata.inputType = event.data.type;
          baseMemory.metadata.inputLength = event.data.content?.length || 0;
          break;

        case 'agentResponse':
          baseMemory.metadata.responseTime = event.data.responseTime;
          baseMemory.metadata.confidenceScore = event.data.confidence;
          break;

        case 'codeExecution':
          baseMemory.metadata.executionTime = event.data.executionTime;
          baseMemory.metadata.exitCode = event.data.exitCode;
          baseMemory.metadata.hasOutput = !!event.data.output;
          break;

        case 'fileChange':
          baseMemory.metadata.changeType = event.data.changeType;
          baseMemory.metadata.filePath = event.data.filePath;
          baseMemory.metadata.fileSize = event.data.fileSize;
          break;

        case 'errorOccurred':
          baseMemory.metadata.errorType = event.data.errorType;
          baseMemory.metadata.errorLevel = event.data.level;
          baseMemory.metadata.stackTrace = event.data.stackTrace;
          break;

        case 'sessionEnd':
          baseMemory.metadata.sessionDuration = event.data.duration;
          baseMemory.metadata.sessionStats = event.data.stats;
          break;
      }

      return baseMemory;
    } catch (error) {
      this.logger.error('Error converting event to memory:', error);
      return null;
    }
  }

  // 映射事件类型到记忆类型
  private mapEventTypeToMemoryType(eventType: string): string {
    const typeMapping: { [key: string]: string } = {
      'userInput': 'interaction',
      'agentResponse': 'response',
      'codeExecution': 'execution',
      'fileChange': 'file_operation',
      'errorOccurred': 'error',
      'sessionEnd': 'session'
    };

    return typeMapping[eventType] || 'general';
  }

  // 记录处理指标
  private recordMetrics(metrics: RecordingMetrics) {
    this.metrics.push(metrics);
    
    // 限制指标历史记录数量
    if (this.metrics.length > 1000) {
      this.metrics = this.metrics.slice(-500); // 保留最近500条记录
    }
  }

  // 更新平均处理时间
  private updateAverageProcessingTime(newTime: number) {
    if (this.stats.averageProcessingTime === 0) {
      this.stats.averageProcessingTime = newTime;
    } else {
      // 使用指数移动平均
      this.stats.averageProcessingTime = 
        this.stats.averageProcessingTime * 0.9 + newTime * 0.1;
    }
  }

  // 启动自动记录
  public async start() {
    if (this.config.enabled) {
      this.logger.info('AutoRecordMiddleware is already running');
      return;
    }

    this.config.enabled = true;
    await this.initialize();
    this.logger.info('AutoRecordMiddleware started');
  }

  // 停止自动记录
  public async stop() {
    this.config.enabled = false;
    
    if (this.batchTimer) {
      clearTimeout(this.batchTimer);
      this.batchTimer = null;
    }

    // 处理剩余的事件
    if (this.eventQueue.length > 0) {
      this.logger.info(`Processing remaining ${this.eventQueue.length} events before stopping`);
      await this.processEventQueue();
    }

    // 等待所有处理完成
    await Promise.all(this.processingQueue);

    this.logger.info('AutoRecordMiddleware stopped');
  }

  // 暂停自动记录
  public pause() {
    this.config.enabled = false;
    this.logger.info('AutoRecordMiddleware paused');
  }

  // 恢复自动记录
  public resume() {
    this.config.enabled = true;
    this.startBatchTimer();
    this.logger.info('AutoRecordMiddleware resumed');
  }

  // 获取统计信息
  public getStats(): RecordingStats {
    return { ...this.stats };
  }

  // 获取最近的处理指标
  public getRecentMetrics(limit: number = 100): RecordingMetrics[] {
    return this.metrics.slice(-limit);
  }

  // 获取性能报告
  public getPerformanceReport() {
    const recentMetrics = this.getRecentMetrics(100);
    const successfulMetrics = recentMetrics.filter(m => m.success);
    const errorMetrics = recentMetrics.filter(m => !m.success);

    const avgProcessingTime = successfulMetrics.length > 0 
      ? successfulMetrics.reduce((sum, m) => sum + m.processingTime, 0) / successfulMetrics.length
      : 0;

    const eventTypeStats = recentMetrics.reduce((stats, metric) => {
      stats[metric.eventType] = (stats[metric.eventType] || 0) + 1;
      return stats;
    }, {} as { [key: string]: number });

    const filterStats = recentMetrics.reduce((stats, metric) => {
      stats[metric.filterResult] = (stats[metric.filterResult] || 0) + 1;
      return stats;
    }, {} as { [key: string]: number });

    return {
      totalEvents: this.stats.totalEvents,
      processedEvents: this.stats.processedEvents,
      errorRate: this.stats.totalEvents > 0 ? this.stats.errorEvents / this.stats.totalEvents : 0,
      averageProcessingTime: avgProcessingTime,
      queueSize: this.eventQueue.length,
      isProcessing: this.isProcessing,
      eventTypeDistribution: eventTypeStats,
      filterResultDistribution: filterStats,
      recentErrors: errorMetrics.slice(-10).map(m => ({
        eventType: m.eventType,
        error: m.error,
        timestamp: m.timestamp
      }))
    };
  }

  // 更新配置
  public updateConfig(newConfig: Partial<AutoRecordConfig>) {
    const oldEnabled = this.config.enabled;
    this.config = { ...this.config, ...newConfig };

    // 如果启用状态改变，重新初始化
    if (oldEnabled !== this.config.enabled) {
      if (this.config.enabled) {
        this.start();
      } else {
        this.stop();
      }
    }

    this.logger.info('AutoRecordMiddleware config updated');
  }

  // 手动触发事件处理
  public async processNow() {
    if (this.eventQueue.length > 0) {
      await this.processEventQueue();
      this.logger.info(`Manually processed ${this.eventQueue.length} events`);
    } else {
      this.logger.info('No events in queue to process');
    }
  }

  // 清空事件队列
  public clearQueue() {
    const queueSize = this.eventQueue.length;
    this.eventQueue = [];
    this.logger.info(`Cleared ${queueSize} events from queue`);
  }

  // 获取队列状态
  public getQueueStatus() {
    return {
      queueSize: this.eventQueue.length,
      isProcessing: this.isProcessing,
      batchSize: this.config.batchSize,
      batchTimeout: this.config.batchTimeout
    };
  }

  // 健康检查
  public healthCheck() {
    const now = Date.now();
    const lastProcessedTime = this.stats.lastProcessedAt.getTime();
    const timeSinceLastProcess = now - lastProcessedTime;

    return {
      status: this.config.enabled ? 'running' : 'stopped',
      healthy: timeSinceLastProcess < 60000, // 1分钟内有处理活动
      queueSize: this.eventQueue.length,
      isProcessing: this.isProcessing,
      timeSinceLastProcess,
      errorRate: this.stats.totalEvents > 0 ? this.stats.errorEvents / this.stats.totalEvents : 0,
      config: this.config
    };
  }

  // 清理资源
  public async cleanup() {
    await this.stop();
    
    // 清理各个服务
    if (this.intelligentFilter) {
      this.intelligentFilter.cleanup();
    }

    this.eventQueue = [];
    this.metrics = [];
    
    this.logger.info('AutoRecordMiddleware cleaned up');
  }
}