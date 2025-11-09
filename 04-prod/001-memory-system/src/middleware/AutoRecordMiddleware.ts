// src/middleware/AutoRecordMiddleware.ts
import { InteractionHook, InteractionEvent } from '../integrations/trae-ide/hooks/InteractionHook';
import { MemoryService, MemoryData } from '../services/MemoryService';
import { IntelligentFilter } from '../services/IntelligentFilter';
import { ContentProcessor } from '../services/ContentProcessor';
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
      
      
      enableProcessing: true,
      enableContextExtraction: true,
      maxRetries: 3,
      retryDelay: 1000,
      debugMode: false,
      ...config
    };

    
    
    this.intelligentFilter = intelligentFilter || new IntelligentFilter();
    this.contentProcessor = contentProcessor || new ContentProcessor();
    this.contextExtractor = contextExtractor || new ContextExtractor();
    
    
    
    
    
    
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

  // 鍒濆鍖栦腑闂翠欢
  private async initialize() {
    try {
      if (!this.config.enabled) {
        this.logger.info('AutoRecordMiddleware is disabled');
        return;
      }

      
      

      // 鍚姩鎵瑰鐞嗗畾鏃跺櫒
      this.startBatchTimer();

      this.logger.info('AutoRecordMiddleware initialized successfully');
    } catch (error) {
      this.logger.error('Failed to initialize AutoRecordMiddleware:', error);
      throw error;
    }
  }

  
  
    // 鐩戝惉鎵€鏈変氦浜掍簨浠?    this.interactionHook.on('userInput', (event) => this.handleEvent(event));
    this.interactionHook.on('agentResponse', (event) => this.handleEvent(event));
    this.interactionHook.on('codeExecution', (event) => this.handleEvent(event));
    this.interactionHook.on('fileChange', (event) => this.handleEvent(event));
    this.interactionHook.on('errorOccurred', (event) => this.handleEvent(event));
    this.interactionHook.on('sessionEnd', (event) => this.handleEvent(event));

    // 鐩戝惉鍐呭瓨鏈嶅姟浜嬩欢
    this.memoryService.on('memoryStored', (memory) => {
      this.logger.debug(`Memory stored: ${memory.id}`);
    });

    this.memoryService.on('error', (error) => {
      this.logger.error('MemoryService error:', error);
      this.stats.errorEvents++;
    });

    this.logger.debug('Event listeners set up');
  }

  // 澶勭悊浜嬩欢
  private async handleEvent(event: InteractionEvent) {
    try {
      if (!this.config.enabled) return;

      this.stats.totalEvents++;
      
      if (this.config.debugMode) {
        this.logger.debug(`Received event: ${event.type}`, event);
      }

      // 娣诲姞鍒颁簨浠堕槦鍒?      this.eventQueue.push(event);

      // 妫€鏌ユ槸鍚﹂渶瑕佺珛鍗冲鐞?      if (this.shouldProcessImmediately(event)) {
        await this.processEventQueue();
      } else if (this.eventQueue.length >= this.config.batchSize) {
        await this.processEventQueue();
      }
    } catch (error) {
      this.logger.error('Error handling event:', error);
      this.stats.errorEvents++;
    }
  }

  // 鍒ゆ柇鏄惁闇€瑕佺珛鍗冲鐞?  private shouldProcessImmediately(event: InteractionEvent): boolean {
    // 楂樹紭鍏堢骇浜嬩欢绔嬪嵆澶勭悊
    const highPriorityTypes = ['errorOccurred', 'sessionEnd'];
    return highPriorityTypes.includes(event.type) || event.priority === 'high';
  }

  // 鍚姩鎵瑰鐞嗗畾鏃跺櫒
  private startBatchTimer() {
    if (this.batchTimer) {
      clearTimeout(this.batchTimer);
    }

    this.batchTimer = setTimeout(async () => {
      if (this.eventQueue.length > 0) {
        await this.processEventQueue();
      }
      this.startBatchTimer(); // 閲嶆柊鍚姩瀹氭椂鍣?    }, this.config.batchTimeout);
  }

  // 澶勭悊浜嬩欢闃熷垪
  private async processEventQueue() {
    if (this.isProcessing || this.eventQueue.length === 0) {
      return;
    }

    this.isProcessing = true;
    const startTime = Date.now();

    try {
      // 鑾峰彇瑕佸鐞嗙殑浜嬩欢
      const eventsToProcess = this.eventQueue.splice(0, this.config.batchSize);
      
      this.logger.debug(`Processing ${eventsToProcess.length} events`);

      // 骞惰澶勭悊浜嬩欢
      const processingPromises = eventsToProcess.map(event => 
        this.processEvent(event).catch(error => {
          this.logger.error(`Error processing event ${event.id}:`, error);
          this.stats.errorEvents++;
          return null;
        })
      );

      const results = await Promise.all(processingPromises);
      const successfulResults = results.filter(result => result !== null);

      // 鏇存柊缁熻淇℃伅
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

  // 澶勭悊鍗曚釜浜嬩欢
  private async processEvent(event: InteractionEvent): Promise<MemoryData | null> {
    const startTime = Date.now();
    let filterResult = 'none';
    let success = false;
    let error: string | undefined;

    try {
      // 1. 杞崲浜嬩欢涓鸿蹇嗘暟鎹?      let memoryData = await this.convertEventToMemory(event);
      if (!memoryData) {
        this.logger.debug(`Event ${event.id} could not be converted to memory`);
        return null;
      }

      // 2. 鎻愬彇涓婁笅鏂囦俊鎭?      if (this.config.enableContextExtraction) {
        const context = await this.contextExtractor.extractContext();
        memoryData.context = { ...memoryData.context, ...context };
      }

      // 3. 鏅鸿兘绛涢€?      if (this.config.enableFiltering) {
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

      // 4. 鍐呭澶勭悊鍜屽寮?      if (this.config.enableProcessing) {
        const processingResult = await this.contentProcessor.processMemory(memoryData);
        memoryData = processingResult.processedMemory;

        // 娣诲姞澶勭悊鍏冩暟鎹?        memoryData.metadata = {
          ...memoryData.metadata,
          processed: true,
          enhancements: processingResult.enhancements.map(e => e.type),
          processingMetrics: processingResult.metrics
        };
      }

      // 5. 瀛樺偍璁板繂
      await this.memoryService.submitMemory(memoryData);
      success = true;
      this.logger.debug('Event successfully processed and stored as memory');
      return memoryData;
    } catch (err) {
      error = err instanceof Error ? err.message : String(err);
      this.logger.error(`Error processing event ${event.id}:`, err);
      throw err;
    } finally {
      // 璁板綍澶勭悊鎸囨爣
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

  // 杞崲浜嬩欢涓鸿蹇嗘暟鎹?  private async convertEventToMemory(event: InteractionEvent): Promise<MemoryData | null> {
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

      // 鏍规嵁浜嬩欢绫诲瀷杩涜鐗规畩澶勭悊
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

  // 鏄犲皠浜嬩欢绫诲瀷鍒拌蹇嗙被鍨?  private mapEventTypeToMemoryType(eventType: string): string {
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

  // 璁板綍澶勭悊鎸囨爣
  private recordMetrics(metrics: RecordingMetrics) {
    this.metrics.push(metrics);
    
    // 闄愬埗鎸囨爣鍘嗗彶璁板綍鏁伴噺
    if (this.metrics.length > 1000) {
      this.metrics = this.metrics.slice(-500); // 淇濈暀鏈€杩?00鏉¤褰?    }
  }

  // 鏇存柊骞冲潎澶勭悊鏃堕棿
  private updateAverageProcessingTime(newTime: number) {
    if (this.stats.averageProcessingTime === 0) {
      this.stats.averageProcessingTime = newTime;
    } else {
      // 浣跨敤鎸囨暟绉诲姩骞冲潎
      this.stats.averageProcessingTime = 
        this.stats.averageProcessingTime * 0.9 + newTime * 0.1;
    }
  }

  // 鍚姩鑷姩璁板綍
  public async start() {
    if (this.config.enabled) {
      this.logger.info('AutoRecordMiddleware is already running');
      return;
    }

    this.config.enabled = true;
    await this.initialize();
    this.logger.info('AutoRecordMiddleware started');
  }

  // 鍋滄鑷姩璁板綍
  public async stop() {
    this.config.enabled = false;
    
    if (this.batchTimer) {
      clearTimeout(this.batchTimer);
      this.batchTimer = null;
    }

    // 澶勭悊鍓╀綑鐨勪簨浠?    if (this.eventQueue.length > 0) {
      this.logger.info(`Processing remaining ${this.eventQueue.length} events before stopping`);
      await this.processEventQueue();
    }

    // 绛夊緟鎵€鏈夊鐞嗗畬鎴?    await Promise.all(this.processingQueue);

    this.logger.info('AutoRecordMiddleware stopped');
  }

  // 鏆傚仠鑷姩璁板綍
  public pause() {
    this.config.enabled = false;
    this.logger.info('AutoRecordMiddleware paused');
  }

  // 鎭㈠鑷姩璁板綍
  public resume() {
    this.config.enabled = true;
    this.startBatchTimer();
    this.logger.info('AutoRecordMiddleware resumed');
  }

  // 鑾峰彇缁熻淇℃伅
  public getStats(): RecordingStats {
    return { ...this.stats };
  }

  // 鑾峰彇鏈€杩戠殑澶勭悊鎸囨爣
  public getRecentMetrics(limit: number = 100): RecordingMetrics[] {
    return this.metrics.slice(-limit);
  }

  // 鑾峰彇鎬ц兘鎶ュ憡
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

  // 鏇存柊閰嶇疆
  public updateConfig(newConfig: Partial<AutoRecordConfig>) {
    const oldEnabled = this.config.enabled;
    this.config = { ...this.config, ...newConfig };

    // 濡傛灉鍚敤鐘舵€佹敼鍙橈紝閲嶆柊鍒濆鍖?    if (oldEnabled !== this.config.enabled) {
      if (this.config.enabled) {
        this.start();
      } else {
        this.stop();
      }
    }

    this.logger.info('AutoRecordMiddleware config updated');
  }

  // 鎵嬪姩瑙﹀彂浜嬩欢澶勭悊
  public async processNow() {
    if (this.eventQueue.length > 0) {
      await this.processEventQueue();
      this.logger.info(`Manually processed ${this.eventQueue.length} events`);
    } else {
      this.logger.info('No events in queue to process');
    }
  }

  // 娓呯┖浜嬩欢闃熷垪
  public clearQueue() {
    const queueSize = this.eventQueue.length;
    this.eventQueue = [];
    this.logger.info(`Cleared ${queueSize} events from queue`);
  }

  // 鑾峰彇闃熷垪鐘舵€?  public getQueueStatus() {
    return {
      queueSize: this.eventQueue.length,
      isProcessing: this.isProcessing,
      batchSize: this.config.batchSize,
      batchTimeout: this.config.batchTimeout
    };
  }

  // 鍋ュ悍妫€鏌?  public healthCheck() {
    const now = Date.now();
    const lastProcessedTime = this.stats.lastProcessedAt.getTime();
    const timeSinceLastProcess = now - lastProcessedTime;

    return {
      status: this.config.enabled ? 'running' : 'stopped',
      healthy: timeSinceLastProcess < 60000, // 1鍒嗛挓鍐呮湁澶勭悊娲诲姩
      queueSize: this.eventQueue.length,
      isProcessing: this.isProcessing,
      timeSinceLastProcess,
      errorRate: this.stats.totalEvents > 0 ? this.stats.errorEvents / this.stats.totalEvents : 0,
      config: this.config
    };
  }

  // 娓呯悊璧勬簮
  public async cleanup() {
    await this.stop();
    
    // 娓呯悊鍚勪釜鏈嶅姟
    if (this.intelligentFilter) {
      this.intelligentFilter.cleanup();
    }

    this.eventQueue = [];
    this.metrics = [];
    
    this.logger.info('AutoRecordMiddleware cleaned up');
  }
}






