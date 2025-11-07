import { EventEmitter } from 'events';
import type { Memory, KnowledgeNode, MemoryContext, RetrievalQuery, RetrievalResult } from '../../types/base';
import { MemoryManager } from '../knowledge-graph/memory';
import { KnowledgeGraph } from '../knowledge-graph/graph';

export interface RetrievalStrategy {
  name: string;
  weight: number;
  execute(query: RetrievalQuery, memories: Memory[]): Promise<Memory[]>;
}

export class MemoryRetriever extends EventEmitter {
  private memoryManager: MemoryManager;
  private knowledgeGraph: KnowledgeGraph;
  private strategies: Map<string, RetrievalStrategy>;
  private cache: Map<string, RetrievalResult>;
  private cacheTimeout: number = 5 * 60 * 1000; // 5分钟缓存

  constructor(memoryManager: MemoryManager, knowledgeGraph: KnowledgeGraph) {
    super();
    this.memoryManager = memoryManager;
    this.knowledgeGraph = knowledgeGraph;
    this.strategies = new Map();
    this.cache = new Map();
    
    this.initializeStrategies();
    this.setupCacheCleanup();
  }

  private initializeStrategies(): void {
    // 文本相似度策略
    this.addStrategy({
      name: 'textSimilarity',
      weight: 0.4,
      execute: async (query: RetrievalQuery, memories: Memory[]): Promise<Memory[]> => {
        if (!query.text) return [];
        
        return memories.filter(memory => {
          const similarity = this.calculateTextSimilarity(query.text!, memory.content);
          return similarity > 0.3;
        }).sort((a, b) => {
          const simA = this.calculateTextSimilarity(query.text!, a.content);
          const simB = this.calculateTextSimilarity(query.text!, b.content);
          return simB - simA;
        });
      }
    });

    // 上下文匹配策略
    this.addStrategy({
      name: 'contextMatch',
      weight: 0.3,
      execute: async (query: RetrievalQuery, memories: Memory[]): Promise<Memory[]> => {
        if (!query.context) return [];
        
        return memories.filter(memory => {
          return this.matchContext(query.context!, memory.context);
        }).sort((a, b) => {
          const scoreA = this.calculateContextScore(query.context!, a.context);
          const scoreB = this.calculateContextScore(query.context!, b.context);
          return scoreB - scoreA;
        });
      }
    });

    // 时间相关性策略
    this.addStrategy({
      name: 'temporalRelevance',
      weight: 0.2,
      execute: async (_query: RetrievalQuery, memories: Memory[]): Promise<Memory[]> => {
        const now = new Date();
        return memories.sort((a, b) => {
          const ageA = now.getTime() - a.createdAt.getTime();
          const ageB = now.getTime() - b.createdAt.getTime();
          
          // 结合重要性和新鲜度
          const scoreA = a.importance * Math.exp(-ageA / (7 * 24 * 60 * 60 * 1000)); // 7天衰减
          const scoreB = b.importance * Math.exp(-ageB / (7 * 24 * 60 * 60 * 1000));
          
          return scoreB - scoreA;
        });
      }
    });

    // 重要性策略
    this.addStrategy({
      name: 'importance',
      weight: 0.1,
      execute: async (_query: RetrievalQuery, memories: Memory[]): Promise<Memory[]> => {
        return memories.sort((a, b) => b.importance - a.importance);
      }
    });
  }

  public addStrategy(strategy: RetrievalStrategy): void {
    this.strategies.set(strategy.name, strategy);
    this.emit('strategyAdded', strategy.name);
  }

  public removeStrategy(name: string): boolean {
    const removed = this.strategies.delete(name);
    if (removed) {
      this.emit('strategyRemoved', name);
    }
    return removed;
  }

  public async retrieve(query: RetrievalQuery): Promise<RetrievalResult> {
    const startTime = Date.now();
    const cacheKey = this.generateCacheKey(query);
    
    // 检查缓存
    if (this.cache.has(cacheKey)) {
      const cached = this.cache.get(cacheKey)!;
      this.emit('cacheHit', { query, result: cached });
      return cached;
    }

    try {
      // 获取候选记忆
      const candidateMemories = await this.getCandidateMemories(query);
      
      // 应用检索策略
      const strategyResults = await this.applyStrategies(query, candidateMemories);
      
      // 合并和排序结果
      const rankedMemories = this.mergeStrategyResults(strategyResults);
      
      // 应用限制
      const limitedMemories = query.limit ? rankedMemories.slice(0, query.limit) : rankedMemories;
      
      // 获取相关节点
      const relatedNodes = query.includeRelated ? 
        await this.getRelatedNodes(limitedMemories) : [];
      
      const result: RetrievalResult = {
        memories: limitedMemories,
        relatedNodes,
        confidence: this.calculateConfidence(limitedMemories, query),
        searchTime: Date.now() - startTime,
        totalResults: candidateMemories.length
      };

      // 缓存结果
      this.cache.set(cacheKey, result);
      
      this.emit('retrievalCompleted', { query, result });
      return result;
      
    } catch (error) {
      this.emit('retrievalError', { query, error });
      throw error;
    }
  }

  private async getCandidateMemories(query: RetrievalQuery): Promise<Memory[]> {
    let memories: Memory[] = [];

    // 基础过滤
    if (query.type) {
      memories = await this.memoryManager.getMemoriesByType(query.type);
    } else {
      memories = await this.memoryManager.getAllMemories();
    }

    // 应用过滤器
    memories = memories.filter(memory => {
      // 标签过滤
      if (query.tags && query.tags.length > 0) {
        const hasMatchingTag = query.tags.some(tag => memory.tags?.includes(tag));
        if (!hasMatchingTag) return false;
      }

      // 时间范围过滤
      if (query.timeRange) {
        if (query.timeRange.start && memory.createdAt < query.timeRange.start) return false;
        if (query.timeRange.end && memory.createdAt > query.timeRange.end) return false;
      }

      // 重要性过滤
      if (query.importance) {
        if (query.importance.min && memory.importance < query.importance.min) return false;
        if (query.importance.max && memory.importance > query.importance.max) return false;
      }

      return true;
    });

    return memories;
  }

  private async applyStrategies(query: RetrievalQuery, memories: Memory[]): Promise<Map<string, Memory[]>> {
    const results = new Map<string, Memory[]>();
    
    for (const [name, strategy] of Array.from(this.strategies)) {
      try {
        const strategyResult = await strategy.execute(query, memories);
        results.set(name, strategyResult);
      } catch (error) {
        this.emit('strategyError', { strategy: name, error });
        results.set(name, []);
      }
    }
    
    return results;
  }

  private mergeStrategyResults(strategyResults: Map<string, Memory[]>): Memory[] {
    const memoryScores = new Map<string, number>();
    
    // 计算每个记忆的综合得分
    for (const [strategyName, memories] of Array.from(strategyResults)) {
      const strategy = this.strategies.get(strategyName);
      if (!strategy) continue;
      
      memories.forEach((memory, index) => {
        const positionScore = Math.max(0, 1 - index / memories.length);
        const weightedScore = positionScore * strategy.weight;
        
        const currentScore = memoryScores.get(memory.id) || 0;
        memoryScores.set(memory.id, currentScore + weightedScore);
      });
    }
    
    // 获取所有唯一记忆并按得分排序
    const allMemories = new Map<string, Memory>();
    for (const memories of Array.from(strategyResults.values())) {
      memories.forEach(memory => allMemories.set(memory.id, memory));
    }
    
    return Array.from(allMemories.values())
      .sort((a, b) => (memoryScores.get(b.id) || 0) - (memoryScores.get(a.id) || 0));
  }

  private async getRelatedNodes(memories: Memory[]): Promise<KnowledgeNode[]> {
    const relatedNodes: KnowledgeNode[] = [];
    
    for (const memory of memories) {
      if (memory.knowledgeLinks && memory.knowledgeLinks.length > 0) {
        for (const nodeId of memory.knowledgeLinks) {
          const node = await this.knowledgeGraph.getNode(nodeId);
          if (node && !relatedNodes.find(n => n.id === node.id)) {
            relatedNodes.push(node);
          }
        }
      }
    }
    
    return relatedNodes;
  }

  private calculateTextSimilarity(text1: string, text2: string): number {
    // 简单的文本相似度计算（可以替换为更复杂的算法）
    const words1 = text1.toLowerCase().split(/\s+/);
    const words2 = text2.toLowerCase().split(/\s+/);
    
    const intersection = words1.filter(word => words2.includes(word));
    const union = Array.from(new Set([...words1, ...words2]));
    
    return intersection.length / union.length;
  }

  private matchContext(queryContext: Partial<MemoryContext>, memoryContext?: MemoryContext): boolean {
    if (!memoryContext) return false;
    if (queryContext.userId && queryContext.userId !== memoryContext.userId) return false;
    if (queryContext.sessionId && queryContext.sessionId !== memoryContext.sessionId) return false;
    if (queryContext.domain && queryContext.domain !== memoryContext.domain) return false;
    if (queryContext.task && queryContext.task !== memoryContext.task) return false;
    
    return true;
  }

  private calculateContextScore(queryContext: Partial<MemoryContext>, memoryContext?: MemoryContext): number {
    if (!memoryContext) return 0;
    let score = 0;
    let totalFields = 0;
    
    const fields = ['userId', 'sessionId', 'domain', 'task'] as const;
    
    for (const field of fields) {
      if (queryContext[field] !== undefined) {
        totalFields++;
        if (queryContext[field] === memoryContext[field]) {
          score++;
        }
      }
    }
    
    return totalFields > 0 ? score / totalFields : 0;
  }

  private calculateConfidence(memories: Memory[], query: RetrievalQuery): number {
    if (memories.length === 0) return 0;
    
    // 基于多个因素计算置信度
    let confidence = 0;
    
    // 结果数量因子
    const resultFactor = Math.min(memories.length / 10, 1);
    confidence += resultFactor * 0.3;
    
    // 平均重要性因子
    const avgImportance = memories.reduce((sum, m) => sum + m.importance, 0) / memories.length;
    confidence += avgImportance * 0.4;
    
    // 查询匹配度因子
    const matchFactor = query.text ? 
      memories.reduce((sum, m) => sum + this.calculateTextSimilarity(query.text!, m.content), 0) / memories.length :
      0.5;
    confidence += matchFactor * 0.3;
    
    return Math.min(confidence, 1);
  }

  private generateCacheKey(query: RetrievalQuery): string {
    return JSON.stringify(query);
  }

  private setupCacheCleanup(): void {
    setInterval(() => {
      const now = Date.now();
      for (const [key, result] of Array.from(this.cache.entries())) {
        if (now - result.searchTime > this.cacheTimeout) {
          this.cache.delete(key);
        }
      }
    }, this.cacheTimeout);
  }

  public clearCache(): void {
    this.cache.clear();
    this.emit('cacheCleared');
  }

  public getStats() {
    return {
      strategiesCount: this.strategies.size,
      cacheSize: this.cache.size,
      strategies: Array.from(this.strategies.keys())
    };
  }

  public destroy(): void {
    this.clearCache();
    this.strategies.clear();
    this.removeAllListeners();
  }
}



