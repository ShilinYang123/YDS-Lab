// src/services/MemoryService.ts
import { EventEmitter } from 'events';
import { Logger } from '../utils/logger';
import { MemoryManager } from './knowledge-graph/memory';
import { RuleEngine } from './rule-system/engine';
import { PerformanceMonitor } from '../utils/performance';

export interface MemoryData {
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
      flushInterval: 5000, // 5秒
      maxQueueSize: 1000,
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
    // 启动定时刷新
    this.startFlushTimer();
    
    // 监听内存管理器事件
    this.memoryManager.on('memoryStored', (memory) => {
      this.emit('memoryStored', memory);
      this.logger.debug('Memory stored successfully');
    });

    this.memoryManager.on('error', (error) => {
      this.emit('error', error);
      this.logger.error('Memory manager error:', error);
    });

    this.logger.info('MemoryService initialized');
  }

  // 提交记忆到队列
  public async submitMemory(memoryData: MemoryData): Promise<void> {
    if (!this.isEnabled) {
      this.logger.debug('MemoryService is disabled, skipping memory submission');
      return;
    }

    try {
      // 验证记忆数据
      if (!this.validateMemoryData(memoryData)) {
        this.logger.warn('Invalid memory data, skipping submission');
        return;
      }

      // 应用过滤规则
      if (this.config.enableFiltering && !this.shouldStoreMemory(memoryData)) {
        this.logger.debug('Memory filtered out by rules');
        return;
      }

      // 检查队列大小
      if (this.memoryQueue.length >= this.config.maxQueueSize) {
        this.logger.warn('Memory queue is full, forcing flush');
        await this.flushQueue();
      }

      // 添加到队列
      this.memoryQueue.push(memoryData);
      this.logger.debug(`Memory added to queue, queue size: ${this.memoryQueue.length}`);

      // 如果队列达到批处理大小，立即处理
      if (this.memoryQueue.length >= this.config.batchSize) {
        await this.flushQueue();
      }

      this.emit('memoryQueued', memoryData);
    } catch (error) {
      this.logger.error('Error submitting memory:', error);
      this.emit('error', error);
    }
  }

  // 刷新队列，批量处理记忆
  private async flushQueue(): Promise<void> {
    if (this.processingQueue || this.memoryQueue.length === 0) {
      return;
    }

    this.processingQueue = true;
    const startTime = Date.now();

    try {
      const batch = this.memoryQueue.splice(0, this.config.batchSize);
      this.logger.debug(`Processing batch of ${batch.length} memories`);

      // 批量处理记忆
      const processedMemories = await Promise.all(
        batch.map(memory => this.processMemory(memory))
      );

      // 过滤掉处理失败的记忆
      const validMemories = processedMemories.filter(memory => memory !== null);

      if (validMemories.length > 0) {
        // 批量存储到记忆管理器
        await this.memoryManager.storeBatch(validMemories);
        this.logger.info(`Successfully stored ${validMemories.length} memories`);
      }

      // 记录性能指标
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

  // 处理单个记忆
  private async processMemory(memoryData: MemoryData): Promise<any | null> {
    try {
      // 增强记忆数据
      const enhancedMemory = await this.enhanceMemory(memoryData);

      // 应用规则引擎
      const processedMemory = await this.ruleEngine.processMemory(enhancedMemory);

      return processedMemory;
    } catch (error) {
      this.logger.error('Error processing individual memory:', error);
      return null;
    }
  }

  // 增强记忆数据
  private async enhanceMemory(memoryData: MemoryData): Promise<any> {
    const enhanced = {
      ...memoryData,
      id: this.generateMemoryId(),
      processedAt: new Date().toISOString(),
      version: '1.0'
    };

    // 添加上下文信息
    if (memoryData.context) {
      enhanced.enrichedContext = await this.enrichContext(memoryData.context);
    }

    // 计算重要性分数
    enhanced.importanceScore = this.calculateImportanceScore(memoryData);

    // 压缩内容（如果启用）
    if (this.config.enableCompression) {
      enhanced.compressedContent = await this.compressContent(memoryData.content);
    }

    return enhanced;
  }

  // 验证记忆数据
  private validateMemoryData(memoryData: MemoryData): boolean {
    if (!memoryData.type || !memoryData.content || !memoryData.timestamp) {
      return false;
    }

    // 检查内容长度
    const contentStr = typeof memoryData.content === 'string' 
      ? memoryData.content 
      : JSON.stringify(memoryData.content);
    
    if (contentStr.length > 50000) { // 50KB限制
      this.logger.warn('Memory content too large, truncating');
      return false;
    }

    return true;
  }

  // 判断是否应该存储记忆
  private shouldStoreMemory(memoryData: MemoryData): boolean {
    // 基本过滤规则
    if (memoryData.metadata?.priority === 'low' && Math.random() > 0.3) {
      return false; // 70%概率过滤低优先级记忆
    }

    // 重复内容检测
    if (this.isDuplicateContent(memoryData)) {
      return false;
    }

    // 敏感信息检测
    if (this.containsSensitiveInfo(memoryData)) {
      this.logger.warn('Sensitive information detected, filtering memory');
      return false;
    }

    return true;
  }

  // 检测重复内容
  private isDuplicateContent(memoryData: MemoryData): boolean {
    // 简单的重复检测逻辑
    const recentMemories = this.memoryQueue.slice(-10);
    return recentMemories.some(memory => 
      memory.type === memoryData.type && 
      JSON.stringify(memory.content) === JSON.stringify(memoryData.content)
    );
  }

  // 检测敏感信息
  private containsSensitiveInfo(memoryData: MemoryData): boolean {
    const sensitivePatterns = [
      /password\s*[:=]\s*\S+/i,
      /api[_-]?key\s*[:=]\s*\S+/i,
      /token\s*[:=]\s*\S+/i,
      /secret\s*[:=]\s*\S+/i,
      /\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b/, // 信用卡号
      /\b\d{3}-\d{2}-\d{4}\b/ // SSN
    ];

    const contentStr = typeof memoryData.content === 'string' 
      ? memoryData.content 
      : JSON.stringify(memoryData.content);

    return sensitivePatterns.some(pattern => pattern.test(contentStr));
  }

  // 丰富上下文信息
  private async enrichContext(context: any): Promise<any> {
    // 添加环境信息
    return {
      ...context,
      environment: {
        platform: process.platform,
        nodeVersion: process.version,
        timestamp: new Date().toISOString()
      }
    };
  }

  // 计算重要性分数
  private calculateImportanceScore(memoryData: MemoryData): number {
    let score = 0.5; // 基础分数

    // 根据类型调整分数
    const typeScores: { [key: string]: number } = {
      'error_log': 0.9,
      'agent_response': 0.8,
      'code_execution': 0.7,
      'user_input': 0.6,
      'file_change': 0.5
    };

    score = typeScores[memoryData.type] || score;

    // 根据优先级调整
    if (memoryData.metadata?.priority === 'high') score += 0.2;
    if (memoryData.metadata?.priority === 'low') score -= 0.2;

    // 根据内容长度调整
    const contentLength = typeof memoryData.content === 'string' 
      ? memoryData.content.length 
      : JSON.stringify(memoryData.content).length;
    
    if (contentLength > 1000) score += 0.1;
    if (contentLength < 50) score -= 0.1;

    return Math.max(0, Math.min(1, score));
  }

  // 压缩内容
  private async compressContent(content: any): Promise<string> {
    // 简单的压缩逻辑，实际可以使用zlib等
    const contentStr = typeof content === 'string' ? content : JSON.stringify(content);
    return Buffer.from(contentStr).toString('base64');
  }

  // 生成记忆ID
  private generateMemoryId(): string {
    return `mem_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  // 启动定时刷新
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

  // 完成对话处理
  public async finalizeConversation(conversationId: string): Promise<void> {
    try {
      // 刷新当前队列
      await this.flushQueue();

      // 通知记忆管理器对话结束
      await this.memoryManager.finalizeConversation(conversationId);

      this.logger.info(`Conversation ${conversationId} finalized`);
      this.emit('conversationFinalized', conversationId);
    } catch (error) {
      this.logger.error('Error finalizing conversation:', error);
      this.emit('error', error);
    }
  }

  // 获取服务状态
  public getStatus() {
    return {
      enabled: this.isEnabled,
      queueSize: this.memoryQueue.length,
      processing: this.processingQueue,
      config: this.config,
      performance: this.performanceMonitor.getMetrics()
    };
  }

  // 启用/禁用服务
  public setEnabled(enabled: boolean) {
    this.isEnabled = enabled;
    if (!enabled && this.flushTimer) {
      clearInterval(this.flushTimer);
      this.flushTimer = null;
    } else if (enabled && !this.flushTimer) {
      this.startFlushTimer();
    }
    this.logger.info(`MemoryService ${enabled ? 'enabled' : 'disabled'}`);
  }

  // 清理资源
  public async cleanup(): Promise<void> {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
      this.flushTimer = null;
    }

    // 最后一次刷新队列
    await this.flushQueue();

    this.removeAllListeners();
    this.logger.info('MemoryService cleaned up');
  }
}