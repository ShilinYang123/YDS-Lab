/**
 * 记忆管理类
 * 实现记忆的存储、检索、分类和生命周期管理
 */

import { EventEmitter } from 'events';
import { Memory, MemoryType, MemoryContext, NodeType } from '../../types/base';
import { KnowledgeGraph } from './graph';
import * as fs from 'fs-extra';
import * as path from 'path';

export class MemoryManager extends EventEmitter {
  private memories: Map<string, Memory> = new Map();
  private memoriesByType: Map<MemoryType, Set<string>> = new Map();
  private memoriesByContext: Map<string, Set<string>> = new Map();
  private memoryIndex: Map<string, Set<string>> = new Map(); // 关键词索引
  private knowledgeGraph: KnowledgeGraph;
  private maxMemories: number;
  private cleanupInterval: NodeJS.Timeout | null = null;
  // 持久化相关
  private persistenceEnabled: boolean = false;
  private persistenceDir?: string;
  private persistenceFileName: string = 'memories.json';
  private persistencePath?: string;
  private autoSave: boolean = true;
  private autoSaveInterval: number = 5000;
  private autoSaveTimer: NodeJS.Timeout | null = null;
  private saveOnDestroy: boolean = true;

  constructor(knowledgeGraph: KnowledgeGraph, options: MemoryManagerOptions = {}) {
    super();
    this.knowledgeGraph = knowledgeGraph;
    this.maxMemories = options.maxMemories || 100000;
    
    // 启动定期清理
    if (options.enableAutoCleanup !== false) {
      this.startAutoCleanup(options.cleanupInterval || 3600000); // 默认1小时
    }

    // 初始化持久化配置
    const persistence = options.persistence || {};
    this.persistenceEnabled = persistence.enabled ?? false;
    this.persistenceDir = persistence.dir || path.join(process.cwd(), 'data');
    this.persistenceFileName = persistence.fileName || 'memories.json';
    this.autoSave = persistence.autoSave ?? true;
    this.autoSaveInterval = persistence.autoSaveInterval ?? 5000;
    this.saveOnDestroy = persistence.saveOnDestroy ?? true;
    this.persistencePath = path.join(this.persistenceDir, this.persistenceFileName);

    // 初始化记忆类型映射
    Object.values(MemoryType).forEach(type => {
      this.memoriesByType.set(type, new Set());
    });

    // 尝试加载历史记忆
    if (this.persistenceEnabled) {
      // 异步加载，不阻塞构造过程
      this.loadFromFile().catch(err => {
        console.warn('MemoryManager: 加载持久化记忆失败', err);
      });
    }
  }

  /**
   * 存储记忆
   */
  storeMemory(memory: Memory): boolean {
    if (this.memories.size >= this.maxMemories) {
      this.emit('capacityWarning', { 
        type: 'memories', 
        current: this.memories.size, 
        max: this.maxMemories 
      });
      
      // 尝试清理过期记忆
      this.cleanupExpiredMemories();
      
      if (this.memories.size >= this.maxMemories) {
        return false;
      }
    }

    if (this.memories.has(memory.id)) {
      return false;
    }

    // 设置时间戳
    if (!memory.createdAt) {
      memory.createdAt = new Date();
    }
    memory.updatedAt = new Date();

    // 默认值兜底
    if (!Array.isArray(memory.tags)) { memory.tags = []; }
    if (!memory.context) { memory.context = {}; }

    // 计算重要性分数
    if (memory.importance === undefined) {
      memory.importance = this.calculateImportance(memory);
    }

    this.memories.set(memory.id, memory);

    // 更新类型索引
    this.memoriesByType.get(memory.type)!.add(memory.id);

    // 更新上下文索引
    if (memory.context) {
      for (const contextKey of Object.keys(memory.context)) {
        if (!this.memoriesByContext.has(contextKey)) {
          this.memoriesByContext.set(contextKey, new Set());
        }
        this.memoriesByContext.get(contextKey)!.add(memory.id);
      }
    }

    // 更新关键词索引
    this.updateMemoryIndex(memory);

    // 创建知识图谱节点
    this.createKnowledgeNode(memory);

    this.emit('memoryStored', memory);
    // 安排持久化
    this.schedulePersist();
    return true;
  }

  /**
   * 更新记忆
   */
  updateMemory(memoryId: string, updates: Partial<Memory>): boolean {
    const memory = this.memories.get(memoryId);
    if (!memory) {
      return false;
    }

    const oldMemory = { ...memory };
    const updatedMemory = { ...memory, ...updates, updatedAt: new Date() };

    // 更新类型索引
    if (updates.type && updates.type !== memory.type) {
      this.memoriesByType.get(memory.type)!.delete(memoryId);
      this.memoriesByType.get(updates.type)!.add(memoryId);
    }

    // 更新上下文索引
    if (updates.context) {
      // 删除旧的上下文索引
      if (memory.context) {
        for (const contextKey of Object.keys(memory.context)) {
          this.memoriesByContext.get(contextKey)?.delete(memoryId);
        }
      }
      
      // 添加新的上下文索引
      for (const contextKey of Object.keys(updates.context)) {
        if (!this.memoriesByContext.has(contextKey)) {
          this.memoriesByContext.set(contextKey, new Set());
        }
        this.memoriesByContext.get(contextKey)!.add(memoryId);
      }
    }

    // 重新计算重要性分数
    if (updates.content || updates.context || updates.tags) {
      updatedMemory.importance = this.calculateImportance(updatedMemory);
    }

    this.memories.set(memoryId, updatedMemory);

    // 更新关键词索引
    this.removeFromMemoryIndex(oldMemory);
    this.updateMemoryIndex(updatedMemory);

    // 更新知识图谱节点
    this.updateKnowledgeNode(updatedMemory);

    this.emit('memoryUpdated', { old: oldMemory, new: updatedMemory });
    // 安排持久化
    this.schedulePersist();
    return true;
  }

  /**
   * 删除记忆
   */
  removeMemory(memoryId: string): boolean {
    const memory = this.memories.get(memoryId);
    if (!memory) {
      return false;
    }

    // 从类型索引中删除
    this.memoriesByType.get(memory.type)!.delete(memoryId);

    // 从上下文索引中删除
    if (memory.context) {
      for (const contextKey of Object.keys(memory.context)) {
        this.memoriesByContext.get(contextKey)?.delete(memoryId);
      }
    }

    // 从关键词索引中删除
    this.removeFromMemoryIndex(memory);

    // 删除知识图谱节点
    this.knowledgeGraph.removeNode(`memory_${memoryId}`);

    this.memories.delete(memoryId);
    this.emit('memoryRemoved', memory);
    // 安排持久化
    this.schedulePersist();
    return true;
  }

  /**
   * 获取记忆
   */
  getMemory(memoryId: string): Memory | undefined {
    const memory = this.memories.get(memoryId);
    if (memory) {
      // 更新访问时间
      memory.lastAccessedAt = new Date();
      memory.accessCount = (memory.accessCount || 0) + 1;
    }
    return memory;
  }

  /**
   * 根据类型获取记忆
   */
  getMemoriesByType(type: MemoryType): Memory[] {
    const memoryIds = this.memoriesByType.get(type);
    if (!memoryIds) {
      return [];
    }

    return Array.from(memoryIds)
      .map(id => this.memories.get(id))
      .filter((memory): memory is Memory => memory !== undefined);
  }

  /**
   * 获取所有记忆
   */
  getAllMemories(): Memory[] {
    return Array.from(this.memories.values());
  }

  /**
   * 搜索记忆
   */
  searchMemories(query: MemorySearchQuery): Memory[] {
    let results = Array.from(this.memories.values());

    // 按类型过滤
    if (query.type) {
      results = results.filter(memory => memory.type === query.type);
    }

    // 按标签过滤
    if (query.tags && query.tags.length > 0) {
      results = results.filter(memory => 
        query.tags!.some(tag => memory.tags?.includes(tag))
      );
    }

    // 按上下文过滤
    if (query.context) {
      results = results.filter(memory => {
        if (!memory.context) return false;
        
        for (const [key, value] of Object.entries(query.context!)) {
          if (memory.context[key] !== value) {
            return false;
          }
        }
        return true;
      });
    }

    // 文本搜索
    if (query.text) {
      const searchText = query.text.toLowerCase();
      results = results.filter(memory => 
        memory.content.toLowerCase().includes(searchText) ||
        (memory.summary && memory.summary.toLowerCase().includes(searchText)) ||
        (memory.tags && memory.tags.some(tag => tag.toLowerCase().includes(searchText)))
      );
    }

    // 关键词搜索
    if (query.keywords && query.keywords.length > 0) {
      const keywordResults = new Set<string>();
      
      for (const keyword of query.keywords) {
        const memoryIds = this.memoryIndex.get(keyword.toLowerCase());
        if (memoryIds) {
          for (const id of Array.from(memoryIds)) {
            keywordResults.add(id);
          }
        }
      }
      
      results = results.filter(memory => keywordResults.has(memory.id));
    }

    // 按重要性过滤
    if (query.minImportance !== undefined) {
      results = results.filter(memory => 
        (memory.importance || 0) >= query.minImportance!
      );
    }

    // 按时间范围过滤
    if (query.createdAfter) {
      results = results.filter(memory => memory.createdAt >= query.createdAfter!);
    }
    if (query.createdBefore) {
      results = results.filter(memory => memory.createdAt <= query.createdBefore!);
    }

    // 排序
    if (query.sortBy) {
      results.sort((a, b) => {
        let aValue: any, bValue: any;
        
        switch (query.sortBy) {
          case 'createdAt':
            aValue = a.createdAt.getTime();
            bValue = b.createdAt.getTime();
            break;
          case 'updatedAt':
            aValue = a.updatedAt?.getTime() || 0;
            bValue = b.updatedAt?.getTime() || 0;
            break;
          case 'lastAccessedAt':
            aValue = a.lastAccessedAt?.getTime() || 0;
            bValue = b.lastAccessedAt?.getTime() || 0;
            break;
          case 'importance':
            aValue = a.importance || 0;
            bValue = b.importance || 0;
            break;
          case 'accessCount':
            aValue = a.accessCount || 0;
            bValue = b.accessCount || 0;
            break;
          default:
            aValue = 0;
            bValue = 0;
        }

        if (query.sortOrder === 'desc') {
          return bValue > aValue ? 1 : bValue < aValue ? -1 : 0;
        } else {
          return aValue > bValue ? 1 : aValue < bValue ? -1 : 0;
        }
      });
    }

    // 限制结果数量
    if (query.limit) {
      results = results.slice(0, query.limit);
    }

    // 更新访问统计
    for (const memory of results) {
      memory.lastAccessedAt = new Date();
      memory.accessCount = (memory.accessCount || 0) + 1;
    }

    return results;
  }

  /**
   * 获取相关记忆
   * 重载：支持 (memoryId, limit) 或 (memoryId, filter, minScore)
   */
  getRelatedMemories(memoryId: string, limit?: number): Memory[];
  getRelatedMemories(memoryId: string, filter?: { type?: MemoryType }, minScore?: number): Memory[];
  getRelatedMemories(memoryId: string, arg2?: number | { type?: MemoryType }, arg3?: number): Memory[] {
    const memory = this.memories.get(memoryId);
    if (!memory) {
      return [];
    }

    const related: { memory: Memory; score: number }[] = [];

    for (const otherMemory of Array.from(this.memories.values())) {
      if (otherMemory.id === memoryId) {
        continue;
      }

      const score = this.calculateSimilarity(memory, otherMemory);
      if (score > 0) {
        related.push({ memory: otherMemory, score });
      }
    }

    // 按相似度排序
    related.sort((a, b) => b.score - a.score);

    if (typeof arg2 === 'object' && arg2) {
      const filter = arg2 as { type?: MemoryType };
      let results = related;
      if (filter.type) {
        results = results.filter(item => item.memory.type === filter.type);
      }
      const minScore = arg3 ?? 0;
      results = results.filter(item => item.score >= minScore);
      return results.map(item => item.memory);
    } else {
      const limit = (typeof arg2 === 'number' ? arg2 : 10) ?? 10;
      return related.slice(0, limit).map(item => item.memory);
    }
  }

  /**
   * 查找相似记忆
   * 重载：支持字符串查询 (query, minScore)，或基于记忆对象 (memory, limit, threshold)
   */
  findSimilarMemories(query: string, minScore: number): Memory[];
  findSimilarMemories(memory: Memory, limit?: number, threshold?: number): Memory[];
  findSimilarMemories(arg1: string | Memory, arg2?: number, arg3?: number): Memory[] {
    if (typeof arg1 === 'string') {
      const query = arg1.toLowerCase();
      const minScore = arg2 ?? 0.1;
      const similar: { memory: Memory; score: number }[] = [];

      for (const memory of Array.from(this.memories.values())) {
        const contentScore = this.computeTextSimilarity(query, memory.content) * 0.7;
        const tagScore = (memory.tags && memory.tags.length > 0)
          ? this.computeTagSimilarity(query, memory.tags) * 0.3
          : 0;
        const score = contentScore + tagScore;
        if (score >= minScore) {
          similar.push({ memory, score });
        }
      }

      similar.sort((a, b) => b.score - a.score);
      return similar.map(item => item.memory);
    }

    const memory = arg1 as Memory;
    const limit = (arg2 ?? 10) as number;
    const threshold = (arg3 ?? 0.5) as number;
    const similar: { memory: Memory; score: number }[] = [];

    for (const otherMemory of Array.from(this.memories.values())) {
      if (otherMemory.id === memory.id) continue;
      const score = this.calculateSimilarity(memory, otherMemory);
      if (score >= threshold) {
        similar.push({ memory: otherMemory, score });
      }
    }

    similar.sort((a, b) => b.score - a.score);
    return similar.slice(0, limit).map(item => item.memory);
  }

  /**
   * 合并记忆
   * 重载：支持传入两个记忆 ID 或 ID 数组
   */
  mergeMemories(id1: string, id2: string, newMemoryData: Partial<Memory>): string;
  mergeMemories(memoryIds: string[], newMemoryData: Partial<Memory>): string;
  mergeMemories(idsOrId1: string | string[], id2OrNewData: string | Partial<Memory>, newMemoryDataArg?: Partial<Memory>): string {
    const memoryIds = Array.isArray(idsOrId1) ? idsOrId1 : [idsOrId1, id2OrNewData as string];
    const newMemoryData = Array.isArray(idsOrId1) ? (id2OrNewData as Partial<Memory>) : (newMemoryDataArg || {});

    const memories = memoryIds
      .map(id => this.memories.get(id))
      .filter((memory): memory is Memory => memory !== undefined);

    if (memories.length < 2) { return `merged_${Date.now()}_${Math.random().toString(36).substr(2,9)}`; }

    // 创建合并后的记忆
    const mergedMemory: Memory = {
      id: `merged_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      type: newMemoryData.type || memories[0]?.type || MemoryType.EPISODIC,
      content: newMemoryData.content || memories.map(m => m.content).join('\\n\\n'),
      tags: [...Array.from(new Set(memories.flatMap(m => m.tags || [])))],
      context: this.mergeContexts(memories.map(m => m.context).filter(Boolean) as MemoryContext[]),
      importance: Math.max(...memories.map(m => m.importance || 0)),
      createdAt: new Date(Math.min(...memories.map(m => m.createdAt.getTime()))),
      ...(newMemoryData.summary && { summary: newMemoryData.summary }),
      ...(newMemoryData.expiresAt && { expiresAt: newMemoryData.expiresAt }),
      updatedAt: new Date(),
      metadata: {
        ...(newMemoryData.metadata || {}),
        mergedFrom: memoryIds,
        mergedAt: new Date().toISOString()
      }
    };

    // 存储合并后的记忆
    if (this.storeMemory(mergedMemory)) {
      // 删除原始记忆
      for (const memoryId of memoryIds) {
        this.removeMemory(memoryId);
      }

      this.emit('memoriesMerged', { 
        originalIds: memoryIds, 
        mergedId: mergedMemory.id 
      });

      return mergedMemory.id;
    }

    return mergedMemory.id;
  }

  /**
   * 清理过期记忆
   */
  cleanupExpiredMemories(): number {
    const now = new Date();
    const expiredMemories: string[] = [];

    for (const memory of Array.from(this.memories.values())) {
      if (memory.expiresAt && memory.expiresAt <= now) {
        expiredMemories.push(memory.id);
      }
    }

    for (const memoryId of expiredMemories) {
      this.removeMemory(memoryId);
    }

    if (expiredMemories.length > 0) {
      this.emit('memoriesExpired', { count: expiredMemories.length, ids: expiredMemories });
    }

    return expiredMemories.length;
  }

  /**
   * 清理低重要性记忆
   */
  cleanupLowImportanceMemories(threshold: number = 0.1, maxToRemove: number = 1000): number {
    const lowImportanceMemories = Array.from(this.memories.values())
      .filter(memory => (memory.importance || 0) < threshold)
      .sort((a, b) => (a.importance || 0) - (b.importance || 0))
      .slice(0, maxToRemove);

    for (const memory of lowImportanceMemories) {
      this.removeMemory(memory.id);
    }

    if (lowImportanceMemories.length > 0) {
      this.emit('lowImportanceMemoriesRemoved', { 
        count: lowImportanceMemories.length, 
        threshold 
      });
    }

    return lowImportanceMemories.length;
  }

  /**
   * 获取记忆统计信息
   */
  getStats(): MemoryStats {
    const typeStats: Record<string, number> = {};
    const importanceDistribution: Record<string, number> = {
      'very_low': 0,
      'low': 0,
      'medium': 0,
      'high': 0,
      'very_high': 0
    };

    for (const [type, memoryIds] of Array.from(this.memoriesByType)) {
      typeStats[type] = memoryIds.size;
    }

    for (const memory of Array.from(this.memories.values())) {
      const importance = memory.importance || 0;
      if (importance < 0.2) importanceDistribution['very_low'] = (importanceDistribution['very_low'] || 0) + 1;
      else if (importance < 0.4) importanceDistribution['low'] = (importanceDistribution['low'] || 0) + 1;
      else if (importance < 0.6) importanceDistribution['medium'] = (importanceDistribution['medium'] || 0) + 1;
      else if (importance < 0.8) importanceDistribution['high'] = (importanceDistribution['high'] || 0) + 1;
      else importanceDistribution['very_high'] = (importanceDistribution['very_high'] || 0) + 1;
    }

    return {
      totalMemories: this.memories.size,
      typeStats,
      importanceDistribution,
      maxMemories: this.maxMemories,
      memoryUsage: this.estimateMemoryUsage(),
      indexSize: this.memoryIndex.size
    };
  }

  /**
   * 计算记忆重要性
   */
  private calculateImportance(memory: Memory): number {
    let score = 0.5; // 基础分数

    // 根据类型调整分数
    switch (memory.type) {
      case MemoryType.LONG_TERM:
        score += 0.3;
        break;
      case MemoryType.EPISODIC:
        score += 0.2;
        break;
      case MemoryType.SEMANTIC:
        score += 0.25;
        break;
      case MemoryType.PROCEDURAL:
        score += 0.2;
        break;
      case MemoryType.WORKING:
        score += 0.1;
        break;
      case MemoryType.SHORT_TERM:
        score += 0.05;
        break;
    }

    // 根据内容长度调整
    const contentLength = memory.content.length;
    if (contentLength > 1000) score += 0.1;
    else if (contentLength > 500) score += 0.05;

    // 根据标签数量调整
    if (memory.tags && memory.tags.length > 0) {
      score += Math.min(memory.tags.length * 0.02, 0.1);
    }

    // 根据上下文丰富度调整
    if (memory.context && Object.keys(memory.context).length > 0) {
      score += Math.min(Object.keys(memory.context).length * 0.01, 0.05);
    }

    return Math.min(Math.max(score, 0), 1);
  }

  /**
   * 计算记忆相似度
   */
  private calculateSimilarity(memory1: Memory, memory2: Memory): number {
    let score = 0;

    // 类型相似度
    if (memory1.type === memory2.type) {
      score += 0.2;
    }

    // 标签相似度
    if (memory1.tags && memory2.tags) {
      const commonTags = memory1.tags.filter(tag => memory2.tags!.includes(tag));
      const totalTags = new Set([...memory1.tags, ...memory2.tags]).size;
      if (totalTags > 0) {
        score += (commonTags.length / totalTags) * 0.3;
      }
    }

    // 上下文相似度
    if (memory1.context && memory2.context) {
      const commonKeys = Object.keys(memory1.context).filter(key => 
        memory2.context![key] === memory1.context![key]
      );
      const totalKeys = new Set([
        ...Object.keys(memory1.context),
        ...Object.keys(memory2.context)
      ]).size;
      if (totalKeys > 0) {
        score += (commonKeys.length / totalKeys) * 0.3;
      }
    }

    // 内容相似度（使用关键词提取）
    const words1 = this.extractKeywords(memory1.content);
    const words2 = this.extractKeywords(memory2.content);
    const commonWords = words1.filter(word => words2.includes(word));
    const totalWords = new Set([...words1, ...words2]).size;
    if (totalWords > 0) {
      score += (commonWords.length / totalWords) * 0.2;
    }

    return score;
  }

  /**
   * 更新记忆索引
   */
  private updateMemoryIndex(memory: Memory): void {
    const words = this.extractKeywords(memory.content);
    
    for (const word of words) {
      if (!this.memoryIndex.has(word)) {
        this.memoryIndex.set(word, new Set());
      }
      this.memoryIndex.get(word)!.add(memory.id);
    }

    // 索引标签
    if (memory.tags) {
      for (const tag of memory.tags) {
        const tagKey = tag.toLowerCase();
        if (!this.memoryIndex.has(tagKey)) {
          this.memoryIndex.set(tagKey, new Set());
        }
        this.memoryIndex.get(tagKey)!.add(memory.id);
      }
    }
  }

  /**
   * 从索引中删除记忆
   */
  private removeFromMemoryIndex(memory: Memory): void {
    const words = this.extractKeywords(memory.content);
    
    for (const word of words) {
      this.memoryIndex.get(word)?.delete(memory.id);
      if (this.memoryIndex.get(word)?.size === 0) {
        this.memoryIndex.delete(word);
      }
    }

    if (memory.tags) {
      for (const tag of memory.tags) {
        const tagKey = tag.toLowerCase();
        this.memoryIndex.get(tagKey)?.delete(memory.id);
        if (this.memoryIndex.get(tagKey)?.size === 0) {
          this.memoryIndex.delete(tagKey);
        }
      }
    }
  }

  /**
   * 提取关键词
   */
  private extractKeywords(text: string): string[] {
    // 处理中文和英文混合文本
    const processed = text
      .toLowerCase()
      // 保留中文字符、英文字母、数字和空格
      .replace(/[^\u4e00-\u9fa5a-zA-Z0-9\s]/g, ' ')
      // 在中文字符之间添加空格以便分词
      .replace(/[\u4e00-\u9fa5]/g, ' $& ')
      // 清理多余空格
      .replace(/\s+/g, ' ')
      .trim();
    
    return processed
      .split(/\s+/)
      .filter(word => word.length > 0 && word.trim() !== '') // 过滤空字符串
      .slice(0, 50); // 限制关键词数量
  }

  // 计算文本相似度（基于简化 Jaccard）
  private computeTextSimilarity(query: string, content: string): number {
    const qWords = this.extractKeywords(query);
    const cWords = this.extractKeywords(content);
    const setQ = new Set(qWords);
    const setC = new Set(cWords);
    const intersection = Array.from(setQ).filter(w => setC.has(w)).length;
    const union = new Set([...Array.from(setQ), ...Array.from(setC)]).size || 1;
    return intersection / union;
  }

  // 计算标签相似度
  private computeTagSimilarity(query: string, tags: string[]): number {
    const qWords = this.extractKeywords(query);
    const tWords = tags.map(t => t.toLowerCase());
    const setQ = new Set(qWords);
    const setT = new Set(tWords);
    const intersection = Array.from(setQ).filter(w => setT.has(w)).length;
    const union = new Set([...Array.from(setQ), ...Array.from(setT)]).size || 1;
    return intersection / union;
  }

  /**
   * 合并上下文
   */
  private mergeContexts(contexts: MemoryContext[]): MemoryContext {
    const merged: MemoryContext = {};
    
    for (const context of contexts) {
      for (const [key, value] of Object.entries(context)) {
        if (merged[key] === undefined) {
          merged[key] = value;
        } else if (Array.isArray(merged[key]) && Array.isArray(value)) {
          merged[key] = [...Array.from(new Set([...merged[key], ...value]))];
        }
      }
    }

    return merged;
  }

  /**
   * 创建知识图谱节点
   */
  private createKnowledgeNode(memory: Memory): void {
    this.knowledgeGraph.addNode({
      id: `memory_${memory.id}`,
      type: NodeType.MEMORY,
      label: memory.summary || memory.content.substring(0, 50) + '...',
      description: memory.content,
      properties: {
        memoryType: memory.type,
        importance: memory.importance || 0,
        tags: memory.tags || [],
        ...memory.context
      },
      tags: memory.tags || [],
      createdAt: memory.createdAt,
      updatedAt: memory.updatedAt || new Date()
    });
  }

  /**
   * 更新知识图谱节点
   */
  private updateKnowledgeNode(memory: Memory): void {
    this.knowledgeGraph.updateNode(`memory_${memory.id}`, {
      label: memory.summary || memory.content.substring(0, 50) + '...',
      description: memory.content,
      properties: {
        memoryType: memory.type,
        importance: memory.importance || 0,
        tags: memory.tags || [],
        ...memory.context
      },
      tags: memory.tags || [],
      ...(memory.updatedAt && { updatedAt: memory.updatedAt })
    });
  }

  /**
   * 启动自动清理
   */
  private startAutoCleanup(interval: number): void {
    this.cleanupInterval = setInterval(() => {
      this.cleanupExpiredMemories();
    }, interval);
  }

  /**
   * 停止自动清理
   */
  stopAutoCleanup(): void {
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval);
      this.cleanupInterval = null;
    }
  }

  /**
   * 估算内存使用量
   */
  private estimateMemoryUsage(): number {
    let size = 0;
    
    for (const memory of Array.from(this.memories.values())) {
      size += JSON.stringify(memory).length;
    }

    return size;
  }

  /**
   * 销毁管理器
   */
  async destroy(): Promise<void> {
    this.stopAutoCleanup();
    // 在销毁前保存当前记忆状态（如果启用）
    if (this.persistenceEnabled && this.saveOnDestroy) {
      try {
        await this.persistToFile();
      } catch (err) {
        console.warn('MemoryManager: 销毁时持久化失败', err);
      }
    }
    if (this.autoSaveTimer) {
      clearTimeout(this.autoSaveTimer);
      this.autoSaveTimer = null;
    }
    this.memories.clear();
    this.memoriesByType.clear();
    this.memoriesByContext.clear();
    this.memoryIndex.clear();
    this.removeAllListeners();
  }

  /**
   * 立即保存到持久化存储
   */
  async saveNow(): Promise<void> {
    if (!this.persistenceEnabled) return;
    await this.persistToFile();
  }

  /**
   * 从持久化存储加载记忆
   */
  async loadNow(): Promise<void> {
    if (!this.persistenceEnabled) return;
    await this.loadFromFile();
  }

  /**
   * 安排持久化（节流）
   */
  private schedulePersist(): void {
    if (!this.persistenceEnabled || !this.autoSave) return;
    if (this.autoSaveTimer) {
      clearTimeout(this.autoSaveTimer);
    }
    this.autoSaveTimer = setTimeout(() => {
      this.persistToFile().catch(err => {
        console.warn('MemoryManager: 自动持久化失败', err);
      });
    }, this.autoSaveInterval);
  }

  /**
   * 将当前记忆保存到文件
   */
  private async persistToFile(): Promise<void> {
    if (!this.persistencePath) return;
    await fs.ensureDir(this.persistenceDir!);
    const payload = Array.from(this.memories.values()).map(m => ({
      ...m,
      createdAt: m.createdAt?.toISOString(),
      updatedAt: m.updatedAt ? m.updatedAt.toISOString() : undefined,
      lastAccessedAt: m.lastAccessedAt ? m.lastAccessedAt.toISOString() : undefined,
      expiresAt: m.expiresAt ? m.expiresAt.toISOString() : undefined
    }));
    await fs.writeFile(this.persistencePath, JSON.stringify({ memories: payload }, null, 2), 'utf-8');
    this.emit('memoriesPersisted', { count: payload.length, path: this.persistencePath });
  }

  /**
   * 从文件加载记忆并构建索引与图谱节点
   */
  private async loadFromFile(): Promise<void> {
    if (!this.persistencePath) return;
    const exists = await fs.pathExists(this.persistencePath);
    if (!exists) return;
    const content = await fs.readFile(this.persistencePath, 'utf-8');
    if (!content || content.trim().length === 0) return;
    try {
      const parsed = JSON.parse(content);
      const items: any[] = Array.isArray(parsed) ? parsed : parsed.memories;
      if (!items || !Array.isArray(items)) return;

      for (const raw of items) {
        // 反序列化日期字段
        const memory: Memory = {
          ...raw,
          createdAt: raw.createdAt ? new Date(raw.createdAt) : new Date(),
          updatedAt: raw.updatedAt ? new Date(raw.updatedAt) : undefined,
          lastAccessedAt: raw.lastAccessedAt ? new Date(raw.lastAccessedAt) : undefined,
          expiresAt: raw.expiresAt ? new Date(raw.expiresAt) : undefined,
          // 兜底默认值
          tags: raw.tags || [],
          context: raw.context || {}
        };

        // 写入内存映射
        this.memories.set(memory.id, memory);
        // 类型索引
        if (!this.memoriesByType.has(memory.type)) {
          this.memoriesByType.set(memory.type, new Set());
        }
        this.memoriesByType.get(memory.type)!.add(memory.id);
        // 上下文索引
        if (memory.context) {
          for (const contextKey of Object.keys(memory.context)) {
            if (!this.memoriesByContext.has(contextKey)) {
              this.memoriesByContext.set(contextKey, new Set());
            }
            this.memoriesByContext.get(contextKey)!.add(memory.id);
          }
        }
        // 关键词索引
        this.updateMemoryIndex(memory);
        // 图谱节点
        this.createKnowledgeNode(memory);
      }

      this.emit('memoriesLoaded', { count: this.memories.size, path: this.persistencePath });
    } catch (err) {
      console.warn('MemoryManager: 解析持久化文件失败', err);
    }
  }
}

// 接口定义
export interface MemoryManagerOptions {
  maxMemories?: number;
  enableAutoCleanup?: boolean;
  cleanupInterval?: number;
  persistence?: MemoryPersistenceOptions;
}

export interface MemoryPersistenceOptions {
  enabled?: boolean;
  dir?: string;
  fileName?: string;
  autoSave?: boolean;
  autoSaveInterval?: number;
  saveOnDestroy?: boolean;
}

export interface MemorySearchQuery {
  type?: MemoryType;
  tags?: string[];
  context?: MemoryContext;
  text?: string;
  keywords?: string[];
  minImportance?: number;
  createdAfter?: Date;
  createdBefore?: Date;
  sortBy?: 'createdAt' | 'updatedAt' | 'lastAccessedAt' | 'importance' | 'accessCount';
  sortOrder?: 'asc' | 'desc';
  limit?: number;
}

export interface MemoryStats {
  totalMemories: number;
  typeStats: Record<string, number>;
  importanceDistribution: Record<string, number>;
  maxMemories: number;
  memoryUsage: number;
  indexSize: number;
}








