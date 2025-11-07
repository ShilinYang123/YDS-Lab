import { EventEmitter } from 'events';
import type { Agent, Memory, PerformanceMetrics, MemoryContext, RetrievalQuery, RetrievalResult, EnhancementContext, EnhancementResult, KnowledgeNode } from '../../types/base';
import { MemoryType } from '../../types/base';
import { MemoryRetriever } from './retriever';
import { AgentEnhancer } from './enhancer';
import { MemoryManager } from '../knowledge-graph/memory';
import { KnowledgeGraph } from '../knowledge-graph/graph';
import { ConfigurationManager } from '../../config/manager';

export interface RetrievalManagerConfig {
  cacheTimeout?: number;
  maxCacheSize?: number;
  enableLearning?: boolean;
  performanceThreshold?: number;
}

export interface RetrievalStats {
  totalQueries: number;
  cacheHitRate: number;
  averageRetrievalTime: number;
  averageEnhancementTime: number;
  totalEnhancements: number;
  averagePerformanceImprovement: number;
  totalMemories: number;
  enhancementQueue: {
    pending: number;
    processing: number;
    completed: number;
    failed: number;
    cancelled: number;
  };
}

export class MemoryRetrievalManager extends EventEmitter {
  private memoryRetriever: MemoryRetriever;
  private agentEnhancer: AgentEnhancer;
  private memoryManager: MemoryManager;
  private config: RetrievalManagerConfig;
  private stats: RetrievalStats;
  private queryHistory: Array<{ query: any; result: RetrievalResult; timestamp: Date }>;
  private enhancementQueue: Map<string, { id: string; context: any; createdAt: Date; status: 'pending'|'processing'|'completed'|'failed'|'cancelled' }>;
  private isProcessingQueue: boolean = false;
  private queueTimer?: NodeJS.Timeout;
  private configManager?: ConfigurationManager;
  private knowledgeGraph: KnowledgeGraph;
  private enhancementPatterns: Array<{
    agentType: string;
    taskType?: string;
    memoryTypes: string[];
    context?: Record<string, any>;
    outcome: { success: boolean; performanceImprovement: number; executionTime?: number };
    recordedAt: Date;
  }> = [];

  constructor(
    managerOrConfig: MemoryManager | ConfigurationManager,
    config: RetrievalManagerConfig = {}
  ) {
    super();
    
    // 创建KnowledgeGraph实例（作为成员保存）
    this.knowledgeGraph = new KnowledgeGraph();

    // 支持两种构造：传入 MemoryManager 或 ConfigurationManager
    if ((managerOrConfig as any)?.getSystemConfig) {
      this.configManager = managerOrConfig as ConfigurationManager;
      // 使用默认选项创建 MemoryManager（可在 initialize 中根据配置进一步调整）
      this.memoryManager = new MemoryManager(this.knowledgeGraph, { enableAutoCleanup: false });
    } else {
      this.memoryManager = managerOrConfig as MemoryManager;
    }
    this.config = {
      cacheTimeout: 5 * 60 * 1000, // 5分钟
      maxCacheSize: 1000,
      enableLearning: true,
      performanceThreshold: 0.1,
      ...config
    };
    
    // 初始化组件
    this.memoryRetriever = new MemoryRetriever(this.memoryManager, this.knowledgeGraph);
    this.agentEnhancer = new AgentEnhancer(this.memoryRetriever);
    
    this.stats = {
      totalQueries: 0,
      cacheHitRate: 0,
      averageRetrievalTime: 0,
      averageEnhancementTime: 0,
      totalEnhancements: 0,
      averagePerformanceImprovement: 0,
      totalMemories: 0,
      enhancementQueue: { pending: 0, processing: 0, completed: 0, failed: 0, cancelled: 0 }
    };
    
    this.queryHistory = [];
    this.enhancementQueue = new Map();
    
    this.setupEventHandlers();
    this.startQueueProcessor();
  }

  private setupEventHandlers(): void {
    // 监听检索事件
    this.memoryRetriever.on('retrievalCompleted', (data) => {
      this.updateRetrievalStats(data.result);
      this.recordQuery(data.query, data.result);
      this.emit('retrievalCompleted', data);
    });

    this.memoryRetriever.on('cacheHit', (data) => {
      this.stats.cacheHitRate = this.calculateCacheHitRate();
      this.emit('cacheHit', data);
    });

    // 监听增强事件
    this.agentEnhancer.on('agentEnhanced', (data) => {
      this.updateEnhancementStats(data.result);
      this.emit('agentEnhanced', data);
    });

    // 监听错误事件
    this.memoryRetriever.on('retrievalError', (error) => {
      this.emit('retrievalError', error);
    });

    this.agentEnhancer.on('enhancementError', (error) => {
      this.emit('enhancementError', error);
    });
  }

  /**
   * 初始化记忆检索管理器
   */
  public async initialize(): Promise<void> {
    // 若有配置管理器，可在此应用配置（当前简化）
    if (this.configManager) {
      // 可根据配置调整 MemoryManager 选项，当前保持默认
    }
    // 这里可以添加其他初始化逻辑
    this.emit('initialized');
  }

  public async retrieveMemories(query: RetrievalQuery): Promise<RetrievalResult> {
    try {
      const result = await this.memoryRetriever.retrieve(query);
      
      // 如果启用学习，分析查询模式
      if (this.config.enableLearning) {
        await this.analyzeQueryPattern(query, result);
      }
      
      return result;
    } catch (error) {
      this.emit('error', { operation: 'retrieve', query, error });
      throw error;
    }
  }

  // 方法重载：支持 (agent, context) 与 (context { agent }) 两种调用
  public async enhanceAgent(agent: Agent, context: EnhancementContext): Promise<EnhancementResult>;
  public async enhanceAgent(context: EnhancementContext & { agent?: Agent }): Promise<{ success: boolean; enhancedAgent?: Agent; appliedMemories: Memory[]; relatedKnowledge: KnowledgeNode[]; performanceImprovement: number; enhancementTime: number; error?: any }>;
  public async enhanceAgent(arg1: any, arg2?: any): Promise<any> {
    try {
      if (arg1 && arg2) {
        // 原始签名 (agent, context)
        const agent: Agent = arg1 as Agent;
        const context: EnhancementContext = arg2 as EnhancementContext;
        const result = await this.agentEnhancer.enhanceAgent(agent, context);
        if (result.performanceImprovement > this.config.performanceThreshold!) {
          await this.recordSuccessfulEnhancement(agent, context, result);
        }
        return result;
      }
      // 新签名 (context { agent })
      const context: EnhancementContext & { agent?: Agent } = arg1;
      const agent = context?.agent as Agent;
      if (!agent) {
        return { success: false, appliedMemories: [], relatedKnowledge: [], performanceImprovement: 0, enhancementTime: 0, error: new Error('Agent is required') };
      }
      const result = await this.agentEnhancer.enhanceAgent(agent, context);
      if (result.performanceImprovement > this.config.performanceThreshold!) {
        await this.recordSuccessfulEnhancement(agent, context, result);
      }
      return { success: true, enhancedAgent: result.enhancedAgent, appliedMemories: result.appliedMemories, relatedKnowledge: result.relatedKnowledge, performanceImprovement: result.performanceImprovement, enhancementTime: result.enhancementTime };
    } catch (error) {
      this.emit('error', { operation: 'enhance', context: arg2 ? arg2 : arg1, error });
      if (arg1 && !arg2) {
        return { success: false, appliedMemories: [], relatedKnowledge: [], performanceImprovement: 0, enhancementTime: 0, error };
      }
      throw error;
    }
  }

  // 异步增强方法重载：返回任务ID
  public async enhanceAgentAsync(agent: Agent, context: EnhancementContext): Promise<string>;
  public async enhanceAgentAsync(context: EnhancementContext & { agent?: Agent }): Promise<string>;
  public async enhanceAgentAsync(arg1: any, arg2?: any): Promise<string> {
    const ctx: any = arg2 ? arg2 : arg1;
    const agent: Agent = arg2 ? arg1 : ctx?.agent;
    if (!agent) throw new Error('Agent is required for enhancement');
    const id = `enh_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    this.enhancementQueue.set(id, { id, context: ctx, createdAt: new Date(), status: 'pending' });
    this.stats.enhancementQueue.pending = this.countQueueByStatus('pending');
    this.emit('enhancementQueued', { id, agentId: agent.id, context: ctx });
    return id;
  }

  private startQueueProcessor(): void {
    this.queueTimer = setInterval(async () => {
      if (this.isProcessingQueue || this.enhancementQueue.size === 0) return;
      
      this.isProcessingQueue = true;
      
      try {
        for (const task of Array.from(this.enhancementQueue.values())) {
          if (task.status !== 'pending') continue;
          const agent: Agent | undefined = task.context?.agent;
          if (!agent) {
            task.status = 'failed';
            this.stats.enhancementQueue.failed = this.countQueueByStatus('failed');
            continue;
          }
          task.status = 'processing';
          this.stats.enhancementQueue.processing = this.countQueueByStatus('processing');
          try {
            const res = await this.enhanceAgent(task.context);
            if (res?.success) {
              task.status = 'completed';
              this.stats.enhancementQueue.completed = this.countQueueByStatus('completed');
            } else {
              task.status = 'failed';
              this.stats.enhancementQueue.failed = this.countQueueByStatus('failed');
            }
          } catch (error) {
            task.status = 'failed';
            this.stats.enhancementQueue.failed = this.countQueueByStatus('failed');
            this.emit('queueProcessingError', error);
          }
        }
        // 更新 pending 计数
        this.stats.enhancementQueue.pending = this.countQueueByStatus('pending');
      } finally {
        this.isProcessingQueue = false;
      }
    }, 1000); // 每秒处理一次队列
  }

  // 已不再使用 getAgentById，移除以避免 TS6133 警告

  public async searchSimilarMemories(memory: Memory, limit: number = 10): Promise<Memory[]> {
    // 保持原方法用于兼容，内部直接调用 retriever
    const query: RetrievalQuery = {
      text: memory.content,
      type: memory.type,
      tags: (memory as any).tags || (memory as any).metadata?.tags,
      limit,
      semanticSearch: true
    };
    const result = await this.memoryRetriever.retrieve(query);
    return result.memories.filter(m => m.id !== memory.id);
  }

  /** 查找相似记忆（返回 { memory, similarity }） */
  public async findSimilarMemories(memory: Memory, options?: { limit?: number; threshold?: number }): Promise<Array<{ memory: Memory; similarity: number }>> {
    const query: RetrievalQuery = {
      text: memory.content,
      type: memory.type,
      ...(memory.context && { context: memory.context }),
      tags: (memory as any).tags || (memory as any).metadata?.tags,
      limit: options?.limit ?? 10,
      semanticSearch: true
    };
    const res = await this.memoryRetriever.retrieve(query);
    const tokens = (str: string) => (str || '').toLowerCase().split(/\W+/).filter(Boolean);
    const targetTokens = new Set(tokens(memory.content));
    const sim = (m: Memory) => {
      const t = tokens(m.content);
      let inter = 0;
      for (const w of t) if (targetTokens.has(w)) inter++;
      const union = new Set([...t, ...Array.from(targetTokens)]).size;
      const jaccard = union === 0 ? 0 : inter / union;
      const ctxBoost = (m.context?.domain && memory.context?.domain && m.context.domain === memory.context.domain) ? 0.2 : 0;
      return Math.max(0, Math.min(1, jaccard + ctxBoost));
    };
    const mapped = res.memories.filter(m => m.id !== memory.id).map(m => ({ memory: m, similarity: sim(m) }));
    const threshold = options?.threshold ?? 0;
    const filtered = mapped.filter(x => x.similarity >= threshold);
    filtered.sort((a, b) => b.similarity - a.similarity);
    return options?.limit ? filtered.slice(0, options.limit) : filtered;
  }

  public async getRecommendedMemories(agent: Agent, context: EnhancementContext): Promise<Memory[]> {
    const memoryContext: Partial<MemoryContext> = {
      ...(context.domain && { domain: context.domain }),
      ...(context.sessionId && { sessionId: context.sessionId })
    };
    
    const query: RetrievalQuery = {
      text: context.userInput || context.currentTask || '',
      context: memoryContext,
      limit: 15,
      includeRelated: true,
      semanticSearch: true
    };
    
    // 基于智能体类型调整查询
    switch (agent.type) {
      case 'rule_processor':
        query.tags = ['rule', 'logic', 'processing'];
        break;
      case 'memory_manager':
        query.tags = ['memory', 'storage', 'management'];
        break;
      case 'knowledge_curator':
        query.tags = ['knowledge', 'curation', 'organization'];
        break;
      case 'task_executor':
        query.tags = ['task', 'execution', 'workflow'];
        break;
      case 'performance_monitor':
        query.tags = ['performance', 'monitoring', 'metrics'];
        break;
    }
    
    const result = await this.retrieveMemories(query);
    return result.memories;
  }

  /** 为智能体推荐记忆（返回 { memory, relevance, reason }） */
  public async recommendMemories(agent: Agent, options?: { limit?: number; task?: any }): Promise<Array<{ memory: Memory; relevance: number; reason: string }>> {
    const tags: string[] = [];
    switch (agent.type) {
      case 'rule_processor': tags.push('rule', 'logic', 'processing'); break;
      case 'memory_manager': tags.push('memory', 'storage', 'management'); break;
      case 'knowledge_curator': tags.push('knowledge', 'curation', 'organization'); break;
      case 'task_executor': tags.push('task', 'execution', 'workflow'); break;
      case 'performance_monitor': tags.push('performance', 'monitoring', 'metrics'); break;
    }
    const text = options?.task?.description || options?.task?.type || '';
    const baseQuery: RetrievalQuery = {
      text,
      tags,
      limit: options?.limit ?? 15,
      includeRelated: true,
      semanticSearch: true
    };
    const res = await this.memoryRetriever.retrieve(baseQuery);
    const computeRel = (m: Memory) => {
      const imp = typeof m.importance === 'number' ? Math.max(0, Math.min(1, m.importance)) : 0.5;
      const taskTypeMatch = options?.task?.type && (m.context?.['taskType']) === options.task.type ? 0.3 : 0;
      const planningMatch = options?.task?.requirements?.includes('planning') && ((m as any).metadata?.tags?.includes('planning') || (m as any).tags?.includes('planning')) ? 0.3 : 0;
      return Math.max(0, Math.min(1, imp + taskTypeMatch + planningMatch));
    };
    const reasonFor = (m: Memory) => {
      const reasons: string[] = [];
      if ((m.context?.['taskType']) && options?.task?.type && (m.context?.['taskType']) === options.task.type) reasons.push('matches task type');
      const hasPlanning = ((m as any).metadata?.tags?.includes('planning') || (m as any).tags?.includes('planning'));
      if (options?.task?.requirements?.includes('planning') && hasPlanning) reasons.push('supports planning requirement');
      if (tags.some(t => ((m as any).tags || (m as any).metadata?.tags || []).includes(t))) reasons.push('matches agent domain');
      return reasons.join('; ') || 'relevant memory';
    };
    const mapped = res.memories.map(m => ({ memory: m, relevance: computeRel(m), reason: reasonFor(m) }));
    mapped.sort((a, b) => b.relevance - a.relevance);
    return options?.limit ? mapped.slice(0, options.limit) : mapped;
  }

  private async analyzeQueryPattern(query: RetrievalQuery, result: RetrievalResult): Promise<void> {
    // 分析查询模式，用于优化未来的检索
    if (result.confidence > 0.8 && result.memories.length > 0) {
      // 记录成功的查询模式
      const pattern = {
        queryType: this.categorizeQuery(query),
        tags: query.tags || [],
        resultCount: result.memories.length,
        confidence: result.confidence,
        timestamp: new Date()
      };
      
      // 这里可以存储模式用于未来优化
      this.emit('patternAnalyzed', pattern);
    }
  }

  private categorizeQuery(query: RetrievalQuery): string {
    if (query.text && query.semanticSearch) return 'semantic_text';
    if (query.tags && query.tags.length > 0) return 'tag_based';
    if (query.context) return 'context_based';
    if (query.timeRange) return 'temporal';
    return 'general';
  }

  private async recordSuccessfulEnhancement(
    agent: Agent, 
    context: EnhancementContext, 
    result: EnhancementResult
  ): Promise<void> {
    // 记录成功的增强模式
    const successPattern = {
      agentType: agent.type,
      context: {
        domain: context.domain,
        task: context.currentTask
      },
      appliedMemoryTypes: result.appliedMemories.map(m => m.type),
      performanceImprovement: result.performanceImprovement,
      timestamp: new Date()
    };
    
    // 存储成功模式用于学习
    await this.memoryManager.storeMemory({
      id: `enhancement_success_${Date.now()}`,
      type: MemoryType.PROCEDURAL,
      content: `Successful enhancement pattern: ${JSON.stringify(successPattern)}`,
      tags: ['enhancement', 'success', 'pattern', agent.type],
      importance: result.performanceImprovement,
      context: {
        userId: 'system',
        sessionId: 'enhancement_learning',
        domain: context.domain || 'general',
        task: 'agent_enhancement'
      },
      createdAt: new Date(),
      lastAccessedAt: new Date(),
      accessCount: 1
    });
  }

  private updateRetrievalStats(result: RetrievalResult): void {
    this.stats.totalQueries++;
    this.stats.averageRetrievalTime = 
      (this.stats.averageRetrievalTime * (this.stats.totalQueries - 1) + result.searchTime) / 
      this.stats.totalQueries;
  }

  private updateEnhancementStats(result: EnhancementResult): void {
    this.stats.totalEnhancements++;
    this.stats.averageEnhancementTime = 
      (this.stats.averageEnhancementTime * (this.stats.totalEnhancements - 1) + result.enhancementTime) / 
      this.stats.totalEnhancements;
    
    this.stats.averagePerformanceImprovement = 
      (this.stats.averagePerformanceImprovement * (this.stats.totalEnhancements - 1) + result.performanceImprovement) / 
      this.stats.totalEnhancements;
  }

  private calculateCacheHitRate(): number {
    // 简化的缓存命中率计算
    return this.stats.totalQueries > 0 ? 
      Math.min(0.3, this.stats.totalQueries / 100) : 0; // 假设30%的最大命中率
  }

  private recordQuery(query: RetrievalQuery, result: RetrievalResult): void {
    this.queryHistory.push({
      query,
      result,
      timestamp: new Date()
    } as any);
    
    // 保持历史记录在合理范围内
    if (this.queryHistory.length > 1000) {
      this.queryHistory.splice(0, this.queryHistory.length - 1000);
    }
  }

  public getStats(): RetrievalStats {
    return { ...this.stats };
  }

  public getDetailedStats() {
    return {
      ...this.stats,
      retrieverStats: this.memoryRetriever.getStats(),
      enhancerStats: this.agentEnhancer.getStats(),
      queueSize: this.enhancementQueue.size,
      queryHistorySize: this.queryHistory.length
    };
  }

  public clearCache(): void {
    this.memoryRetriever.clearCache();
    this.emit('cacheCleared');
  }

  public clearHistory(): void {
    this.queryHistory = [];
    this.emit('historyCleared');
  }

  public async setPerformanceBaseline(agentId: string, metrics: PerformanceMetrics): Promise<void> {
    await this.agentEnhancer.setPerformanceBaseline(agentId, metrics);
  }

  public getLearningPatterns() {
    return this.agentEnhancer.getLearningPatterns();
  }

  public getEnhancementHistory(agentId: string) {
    return this.agentEnhancer.getEnhancementHistory(agentId);
  }

  public destroy(): void {
    this.memoryRetriever.destroy();
    this.agentEnhancer.destroy();
    this.enhancementQueue.clear();
    this.queryHistory = [];
    if (this.queueTimer) clearInterval(this.queueTimer);
    this.removeAllListeners();
  }

  /** 存储记忆（接受 metadata.tags） */
  public async storeMemory(memory: any): Promise<void> {
    if (!memory || typeof memory !== 'object') throw new Error('Invalid memory');
    if (!memory.id || !memory.content || !memory.type) throw new Error('Missing required memory fields');
    const normalized: Memory = {
      id: memory.id,
      content: memory.content,
      type: memory.type,
      importance: memory.importance ?? 0.5,
      tags: memory.tags || memory.metadata?.tags || [],
      context: memory.context || {},
      embeddings: memory.embeddings,
      knowledgeLinks: memory.knowledgeLinks,
      metadata: memory.metadata,
      createdAt: memory.createdAt || new Date(),
      updatedAt: memory.updatedAt,
      lastAccessedAt: memory.lastAccessedAt,
      accessCount: memory.accessCount,
      expiresAt: memory.expiresAt
    };
    await this.memoryManager.storeMemory(normalized);
    this.stats.totalMemories++;
  }

  /** 获取增强任务状态 */
  public async getEnhancementStatus(id: string): Promise<{ id: string; status: 'pending'|'processing'|'completed'|'failed'|'cancelled'|'not_found'; createdAt?: Date }> {
    const task = this.enhancementQueue.get(id);
    if (!task) return { id, status: 'not_found' };
    return { id, status: task.status, createdAt: task.createdAt };
  }

  /** 取消增强任务 */
  public async cancelEnhancement(id: string): Promise<boolean> {
    const task = this.enhancementQueue.get(id);
    if (!task) return false;
    task.status = 'cancelled';
    this.stats.enhancementQueue.cancelled = this.countQueueByStatus('cancelled');
    return true;
  }

  /** 分析查询模式（聚合统计） */
  public async analyzeQueryPatterns(options?: { timeRange?: { start?: Date; end?: Date } }): Promise<{ totalQueries: number; uniqueUsers: number; commonTerms: string[]; queryFrequency: Record<string, number>; popularQueries: Array<{ query: string; count: number }> }> {
    const start = options?.timeRange?.start?.getTime() ?? 0;
    const end = options?.timeRange?.end?.getTime() ?? Date.now();
    const within = this.queryHistory.filter(h => {
      const ts = (h as any).timestamp?.getTime?.() ?? Date.now();
      return ts >= start && ts <= end;
    });
    const totalQueries = within.length;
    const users = new Set<string>();
    const freq: Record<string, number> = {};
    const termCount: Record<string, number> = {};
    for (const h of within) {
      const q: any = h.query || {};
      const text = (q.text || '').toString();
      if (text) freq[text] = (freq[text] || 0) + 1;
      const ctxUser = q.context?.userId;
      if (ctxUser) users.add(ctxUser);
      for (const t of text.split(/\W+/).filter(Boolean)) {
        termCount[t.toLowerCase()] = (termCount[t.toLowerCase()] || 0) + 1;
      }
    }
    const commonTerms = Object.entries(termCount).sort((a, b) => b[1] - a[1]).map(([k]) => k).slice(0, 10);
    const popularQueries = Object.entries(freq).sort((a, b) => b[1] - a[1]).map(([query, count]) => ({ query, count }));
    return {
      totalQueries,
      uniqueUsers: users.size,
      commonTerms,
      queryFrequency: freq,
      popularQueries
    };
  }

  /** 记录成功的增强模式（供优化使用） */
  public async recordEnhancementPattern(pattern: { agentType: string; taskType?: string; memoryTypes: string[]; context?: Record<string, any>; outcome: { success: boolean; performanceImprovement: number; executionTime?: number } }): Promise<void> {
    this.enhancementPatterns.push({ ...pattern, recordedAt: new Date() });
  }

  /** 获取已记录的增强模式 */
  public async getEnhancementPatterns(filter?: { agentType?: string; taskType?: string }): Promise<Array<{ agentType: string; taskType?: string; memoryTypes: string[]; context?: Record<string, any>; outcome: { success: boolean; performanceImprovement: number; executionTime?: number }; recordedAt: Date }>> {
    return this.enhancementPatterns.filter(p => {
      if (filter?.agentType && p.agentType !== filter.agentType) return false;
      if (filter?.taskType && p.taskType !== filter.taskType) return false;
      return true;
    });
  }

  /** 基于历史模式优化增强 */
  public async optimizeEnhancement(options: { agentType: string; taskType?: string; context?: Record<string, any> }): Promise<{ recommendedMemoryTypes: string[]; expectedImprovement: number; confidence: number }> {
    const patterns = this.enhancementPatterns.filter(p => p.agentType === options.agentType && (!options.taskType || p.taskType === options.taskType));
    if (patterns.length === 0) return { recommendedMemoryTypes: [], expectedImprovement: 0, confidence: 0 };
    const typeScore: Record<string, { count: number; perf: number }> = {};
    for (const p of patterns) {
      for (const t of p.memoryTypes) {
        if (!typeScore[t]) typeScore[t] = { count: 0, perf: 0 };
        typeScore[t].count++;
        typeScore[t].perf += p.outcome.performanceImprovement || 0;
      }
    }
    const sortedTypes = Object.entries(typeScore).sort((a, b) => (b[1].perf / b[1].count) - (a[1].perf / a[1].count)).map(([t]) => t);
    const expectedImprovement = patterns.reduce((s, p) => s + (p.outcome.performanceImprovement || 0), 0) / patterns.length;
    const confidence = Math.max(0.1, Math.min(1, patterns.length / 10));
    return { recommendedMemoryTypes: sortedTypes.slice(0, 3), expectedImprovement, confidence };
  }

  private countQueueByStatus(status: 'pending'|'processing'|'completed'|'failed'|'cancelled'): number {
    let n = 0;
    for (const [, t] of this.enhancementQueue) if (t.status === status) n++;
    return n;
  }
}