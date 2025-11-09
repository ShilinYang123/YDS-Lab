import { EventEmitter } from 'events';
import { Logger } from '../utils/logger';
import { PerformanceMonitor } from '../utils/performance';
import { MemoryManager } from './knowledge-graph/memory';
import { RuleEngine } from './rule-system/engine';
import type { Memory } from '../types/base';


export interface MemoryData {
  id?: string;
  source?: string;
  type: string;
  content: any;
  conversationId?: string;
  timestamp: string;
  context?: any;
  metadata?: {
    source?: string;
    priority?: string;
    confidenceScore?: number;
    responseTime?: number;
    severity?: string;
    [key: string]: any;
  };
}

export interface MemoryServiceConfig {
  batchSize: number;
  flushInterval: number;
  maxQueueSize: number;
  enableFiltering: boolean;
  enableCompression: boolean;
}

export class MemoryService extends EventEmitter {
  private memoryManager: MemoryManager;
  private ruleEngine: RuleEngine;
  private logger: Logger;
  private performanceMonitor: PerformanceMonitor;
  private config: MemoryServiceConfig;
  
  private memoryQueue: MemoryData[] = [];
  private processingQueue: boolean = false;
  private flushTimer: NodeJS.Timeout | null = null;
  private isEnabled: boolean = true;

  constructor(config?: Partial<MemoryServiceConfig>) {
    super();
    
    this.config = {
      batchSize: 10,
      flushInterval: 5000, // 5绉?      maxQueueSize: 1000,
      enableFiltering: true,
      enableCompression: true,
      ...config
    };

    this.memoryManager = new MemoryManager();
    this.ruleEngine = new RuleEngine();
    this.logger = new Logger('MemoryService');
    this.performanceMonitor = new PerformanceMonitor();

    this.initializeService();
  }

  private initializeService() {
    // 鍚姩瀹氭椂鍒锋柊
        this.ruleEngine.start();
    // 鐩戝惉鍐呭瓨绠＄悊鍣ㄤ簨浠?    this.memoryManager.on('memoryStored', (memory) => {
      this.emit('memoryStored', memory);
      this.logger.debug('Memory stored successfully');
    });

    this.memoryManager.on('error', (error) => {
      this.emit('error', error);
      this.logger.error('Memory manager error:', error);
    });

    this.logger.info('MemoryService initialized');
  }

  // 鎻愪氦璁板繂鍒伴槦鍒?  public async submitMemory(memoryData: MemoryData): Promise<void> {
    if (!this.isEnabled) {
      this.logger.debug('MemoryService is disabled, skipping memory submission');
      return;
    }

    try {
      // 楠岃瘉璁板繂鏁版嵁
      if (!this.validateMemoryData(memoryData)) {
        this.logger.warn('Invalid memory data, skipping submission');
        return;
      }

      // 搴旂敤杩囨护瑙勫垯
      if (this.config.enableFiltering && !this.shouldStoreMemory(memoryData)) {
        this.logger.debug('Memory filtered out by rules');
        return;
      }

      // 妫€鏌ラ槦鍒楀ぇ灏?      if (this.memoryQueue.length >= this.config.maxQueueSize) {
        this.logger.warn('Memory queue is full, forcing flush');
        await this.flushQueue();
      }

      // 娣诲姞鍒伴槦鍒?      this.memoryQueue.push(memoryData);
      this.logger.debug(`Memory added to queue, queue size: ${this.memoryQueue.length}`);

      // 濡傛灉闃熷垪杈惧埌鎵瑰鐞嗗ぇ灏忥紝绔嬪嵆澶勭悊
      if (this.memoryQueue.length >= this.config.batchSize) {
        await this.flushQueue();
      }

      this.emit('memoryQueued', memoryData);
    } catch (error) {
      this.logger.error('Error submitting memory:', error);
      this.emit('error', error);
    }
  }

  // 鍒锋柊闃熷垪锛屾壒閲忓鐞嗚蹇?  private async flushQueue(): Promise<void> {
    if (this.processingQueue || this.memoryQueue.length === 0) {
      return;
    }

    this.processingQueue = true;
    const startTime = Date.now();

    try {
      const batch = this.memoryQueue.splice(0, this.config.batchSize);
      this.logger.debug(`Processing batch of ${batch.length} memories`);

      // 鎵归噺澶勭悊璁板繂
      const processedMemories = await Promise.all(
        batch.map(memory => this.processMemory(memory))
      );

      // 杩囨护鎺夊鐞嗗け璐ョ殑璁板繂
      const validMemories = processedMemories.filter(memory => memory !== null);

      if (validMemories.length > 0) {
        // 鎵归噺瀛樺偍鍒拌蹇嗙鐞嗗櫒
        await this.memoryManager.storeBatch(validMemories);
        this.logger.info(`Successfully stored ${validMemories.length} memories`);
      }

      // 璁板綍鎬ц兘鎸囨爣
      const processingTime = Date.now() - startTime;
      this.performanceMonitor.recordMetric('memory_batch_processing_time', processingTime);
      this.performanceMonitor.recordMetric('memory_batch_size', batch.length);

      this.emit('batchProcessed', { count: validMemories.length, processingTime });
    } catch (error) {
      this.logger.error('Error processing memory batch:', error);
      this.emit('error', error);
    } finally {
      this.processingQueue = false;
    }
  }

  // 澶勭悊鍗曚釜璁板繂
  private async processMemory(memoryData: MemoryData): Promise<any | null> {
    try {
      // 澧炲己璁板繂鏁版嵁
      const enhancedMemory = await this.enhanceMemory(memoryData);

      // 搴旂敤瑙勫垯寮曟搸
      const processedMemory = await this.ruleEngine.processMemory(enhancedMemory);

      return processedMemory;
    } catch (error) {
      this.logger.error('Error processing individual memory:', error);
      return null;
    }
  }

  // 澧炲己璁板繂鏁版嵁
  private async enhanceMemory(memoryData: MemoryData): Promise<any> {
    const enhanced: Record<string, any> = {
      ...memoryData,
      id: this.generateMemoryId(),
      processedAt: new Date().toISOString(),
      version: '1.0'
    };

    // 娣诲姞涓婁笅鏂囦俊鎭?    if (memoryData.context) {
      enhanced.enrichedContext = await this.enrichContext(memoryData.context);
    }

    // 璁＄畻閲嶈鎬у垎鏁?    enhanced.importanceScore = this.calculateImportanceScore(memoryData);

    // 鍘嬬缉鍐呭锛堝鏋滃惎鐢級
    if (this.config.enableCompression) {
      enhanced.compressedContent = await this.compressContent(memoryData.content);
    }

    return enhanced;
  }

  // 楠岃瘉璁板繂鏁版嵁
  private validateMemoryData(memoryData: MemoryData): boolean {
    if (!memoryData.type || !memoryData.content || !memoryData.timestamp) {
      return false;
    }

    // 妫€鏌ュ唴瀹归暱搴?    const contentStr = typeof memoryData.content === 'string' 
      ? memoryData.content 
      : JSON.stringify(memoryData.content);
    
    if (contentStr.length > 50000) { // 50KB闄愬埗
      this.logger.warn('Memory content too large, truncating');
      return false;
    }

    return true;
  }

  // 鍒ゆ柇鏄惁搴旇瀛樺偍璁板繂
  private shouldStoreMemory(memoryData: MemoryData): boolean {
    // 鍩烘湰杩囨护瑙勫垯
    if (memoryData.metadata?.priority === 'low' && Math.random() > 0.3) {
      return false; // 70%姒傜巼杩囨护浣庝紭鍏堢骇璁板繂
    }

    // 閲嶅鍐呭妫€娴?    if (this.isDuplicateContent(memoryData)) {
      return false;
    }

    // 鏁忔劅淇℃伅妫€娴?    if (this.containsSensitiveInfo(memoryData)) {
      this.logger.warn('Sensitive information detected, filtering memory');
      return false;
    }

    return true;
  }

  // 妫€娴嬮噸澶嶅唴瀹?  private isDuplicateContent(memoryData: MemoryData): boolean {
    // 绠€鍗曠殑閲嶅妫€娴嬮€昏緫
    const recentMemories = this.memoryQueue.slice(-10);
    return recentMemories.some(memory => 
      memory.type === memoryData.type && 
      JSON.stringify(memory.content) === JSON.stringify(memoryData.content)
    );
  }

  // 妫€娴嬫晱鎰熶俊鎭?  private containsSensitiveInfo(memoryData: MemoryData): boolean {
    const sensitivePatterns = [
      /password\s*[:=]\s*\S+/i,
      /api[_-]?key\s*[:=]\s*\S+/i,
      /token\s*[:=]\s*\S+/i,
      /secret\s*[:=]\s*\S+/i,
      /\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b/, // 淇＄敤鍗″彿
      /\b\d{3}-\d{2}-\d{4}\b/ // SSN
    ];

    const contentStr = typeof memoryData.content === 'string' 
      ? memoryData.content 
      : JSON.stringify(memoryData.content);

    return sensitivePatterns.some(pattern => pattern.test(contentStr));
  }

  // 涓板瘜涓婁笅鏂囦俊鎭?  private async enrichContext(context: any): Promise<any> {
    // 娣诲姞鐜淇℃伅
    return {
      ...context,
      environment: {
        platform: process.platform,
        nodeVersion: process.version,
        timestamp: new Date().toISOString()
      }
    };
  }

  // 璁＄畻閲嶈鎬у垎鏁?  private calculateImportanceScore(memoryData: MemoryData): number {
    let score = 0.5; // 鍩虹鍒嗘暟

    // 鏍规嵁绫诲瀷璋冩暣鍒嗘暟
    const typeScores: { [key: string]: number } = {
      'error_log': 0.9,
      'agent_response': 0.8,
      'code_execution': 0.7,
      'user_input': 0.6,
      'file_change': 0.5
    };

    score = typeScores[memoryData.type] || score;

    // 鏍规嵁浼樺厛绾ц皟鏁?    if (memoryData.metadata?.priority === 'high') score += 0.2;
    if (memoryData.metadata?.priority === 'low') score -= 0.2;

    // 鏍规嵁鍐呭闀垮害璋冩暣
    const contentLength = typeof memoryData.content === 'string' 
      ? memoryData.content.length 
      : JSON.stringify(memoryData.content).length;
    
    if (contentLength > 1000) score += 0.1;
    if (contentLength < 50) score -= 0.1;

    return Math.max(0, Math.min(1, score));
  }

  // 鍘嬬缉鍐呭
  private async compressContent(content: any): Promise<string> {
    // 绠€鍗曠殑鍘嬬缉閫昏緫锛屽疄闄呭彲浠ヤ娇鐢▃lib绛?    const contentStr = typeof content === 'string' ? content : JSON.stringify(content);
    return Buffer.from(contentStr).toString('base64');
  }

  // 鐢熸垚璁板繂ID
  private generateMemoryId(): string {
    return `mem_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  // 鍚姩瀹氭椂鍒锋柊
  private startFlushTimer() {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
    }

    this.flushTimer = setInterval(() => {
      if (this.memoryQueue.length > 0) {
        this.flushQueue().catch(error => {
          this.logger.error('Error in scheduled flush:', error);
        });
      }
    }, this.config.flushInterval);
  }

  // 瀹屾垚瀵硅瘽澶勭悊
  public async finalizeConversation(conversationId: string): Promise<void> {
    try {
      
    

      
      

      this.logger.info(`Conversation ${conversationId} finalized`);
      this.emit('conversationFinalized', conversationId);
    } catch (error) {
      this.logger.error('Error finalizing conversation:', error);
      this.emit('error', error);
    }
  }

  
  
    return {
      enabled: this.isEnabled,
      queueSize: this.memoryQueue.length,
      processing: this.processingQueue,
      config: this.config,
      performance: this.performanceMonitor.getMetrics()
    };
  }

  // 鍚敤/绂佺敤鏈嶅姟
  public setEnabled(enabled: boolean) {
    this.isEnabled = enabled;
    if (!enabled && this.flushTimer) {
      clearInterval(this.flushTimer);
      this.flushTimer = null;
    } else if (enabled && !this.flushTimer) {
          this.ruleEngine.start();
    }
    this.logger.info(`MemoryService ${enabled ? 'enabled' : 'disabled'}`);
  }

  // 娓呯悊璧勬簮
  public async cleanup(): Promise<void> {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
      this.flushTimer = null;
    }

    
    

    this.removeAllListeners();
    this.logger.info('MemoryService cleaned up');
  }
}




