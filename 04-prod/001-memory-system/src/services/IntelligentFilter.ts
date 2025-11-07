// src/services/IntelligentFilter.ts
import { Logger } from '../utils/logger';
import { MemoryData } from './MemoryService';

export interface FilterRule {
  id: string;
  name: string;
  type: 'content' | 'metadata' | 'context' | 'frequency' | 'similarity';
  condition: any;
  action: 'accept' | 'reject' | 'modify' | 'flag';
  priority: number;
  enabled: boolean;
}

export interface FilterConfig {
  enableContentAnalysis: boolean;
  enableSimilarityDetection: boolean;
  enableFrequencyFiltering: boolean;
  enableContextualFiltering: boolean;
  similarityThreshold: number;
  frequencyWindow: number;
  maxDuplicates: number;
}

export interface FilterResult {
  action: 'accept' | 'reject' | 'modify';
  confidence: number;
  reasons: string[];
  modifiedMemory?: MemoryData;
  flags?: string[];
}

export class IntelligentFilter {
  private logger: Logger;
  private config: FilterConfig;
  private rules: FilterRule[] = [];
  private recentMemories: MemoryData[] = [];
  private contentHashes: Map<string, number> = new Map();
  private keywordWeights: Map<string, number> = new Map();

  constructor(config?: Partial<FilterConfig>) {
    this.logger = new Logger('IntelligentFilter');
    this.config = {
      enableContentAnalysis: true,
      enableSimilarityDetection: true,
      enableFrequencyFiltering: true,
      enableContextualFiltering: true,
      similarityThreshold: 0.8,
      frequencyWindow: 300000, // 5分钟
      maxDuplicates: 3,
      ...config
    };

    this.initializeDefaultRules();
    this.initializeKeywordWeights();
  }

  // 主要的筛选方法
  public async filterMemory(memory: MemoryData): Promise<FilterResult> {
    try {
      const results: FilterResult[] = [];

      // 应用所有启用的规则
      for (const rule of this.rules.filter(r => r.enabled)) {
        const result = await this.applyRule(rule, memory);
        if (result) {
          results.push(result);
        }
      }

      // 综合所有结果
      const finalResult = this.combineResults(results, memory);

      // 更新内部状态
      this.updateInternalState(memory, finalResult);

      this.logger.debug(`Memory filtered: ${finalResult.action} (confidence: ${finalResult.confidence})`);
      return finalResult;
    } catch (error) {
      this.logger.error('Error filtering memory:', error);
      return {
        action: 'accept',
        confidence: 0.5,
        reasons: ['Filter error, defaulting to accept']
      };
    }
  }

  // 应用单个规则
  private async applyRule(rule: FilterRule, memory: MemoryData): Promise<FilterResult | null> {
    try {
      switch (rule.type) {
        case 'content':
          return this.applyContentRule(rule, memory);
        case 'metadata':
          return this.applyMetadataRule(rule, memory);
        case 'context':
          return this.applyContextRule(rule, memory);
        case 'frequency':
          return this.applyFrequencyRule(rule, memory);
        case 'similarity':
          return this.applySimilarityRule(rule, memory);
        default:
          return null;
      }
    } catch (error) {
      this.logger.error(`Error applying rule ${rule.id}:`, error);
      return null;
    }
  }

  // 应用内容规则
  private applyContentRule(rule: FilterRule, memory: MemoryData): FilterResult | null {
    if (!this.config.enableContentAnalysis) return null;

    const content = this.extractTextContent(memory.content);
    const condition = rule.condition;

    let matches = false;
    let confidence = 0;
    const reasons: string[] = [];

    // 关键词匹配
    if (condition.keywords) {
      const keywordMatches = condition.keywords.filter((keyword: string) => 
        content.toLowerCase().includes(keyword.toLowerCase())
      );
      if (keywordMatches.length > 0) {
        matches = true;
        confidence += 0.3 * (keywordMatches.length / condition.keywords.length);
        reasons.push(`Matched keywords: ${keywordMatches.join(', ')}`);
      }
    }

    // 正则表达式匹配
    if (condition.patterns) {
      for (const pattern of condition.patterns) {
        const regex = new RegExp(pattern, 'i');
        if (regex.test(content)) {
          matches = true;
          confidence += 0.4;
          reasons.push(`Matched pattern: ${pattern}`);
        }
      }
    }

    // 内容长度检查
    if (condition.minLength && content.length < condition.minLength) {
      matches = true;
      confidence += 0.2;
      reasons.push(`Content too short: ${content.length} < ${condition.minLength}`);
    }

    if (condition.maxLength && content.length > condition.maxLength) {
      matches = true;
      confidence += 0.3;
      reasons.push(`Content too long: ${content.length} > ${condition.maxLength}`);
    }

    // 内容质量分析
    const qualityScore = this.analyzeContentQuality(content);
    if (condition.minQuality && qualityScore < condition.minQuality) {
      matches = true;
      confidence += 0.4;
      reasons.push(`Low content quality: ${qualityScore}`);
    }

    return matches ? {
      action: rule.action,
      confidence: Math.min(confidence, 1.0),
      reasons
    } : null;
  }

  // 应用元数据规则
  private applyMetadataRule(rule: FilterRule, memory: MemoryData): FilterResult | null {
    const metadata = memory.metadata || {};
    const condition = rule.condition;
    let matches = false;
    let confidence = 0;
    const reasons: string[] = [];

    // 优先级检查
    if (condition.priority && metadata.priority === condition.priority) {
      matches = true;
      confidence += 0.5;
      reasons.push(`Priority match: ${condition.priority}`);
    }

    // 来源检查
    if (condition.source && metadata.source === condition.source) {
      matches = true;
      confidence += 0.3;
      reasons.push(`Source match: ${condition.source}`);
    }

    // 置信度检查
    if (condition.minConfidence && metadata.confidenceScore < condition.minConfidence) {
      matches = true;
      confidence += 0.4;
      reasons.push(`Low confidence: ${metadata.confidenceScore}`);
    }

    // 响应时间检查
    if (condition.maxResponseTime && metadata.responseTime > condition.maxResponseTime) {
      matches = true;
      confidence += 0.2;
      reasons.push(`Slow response: ${metadata.responseTime}ms`);
    }

    return matches ? {
      action: rule.action,
      confidence,
      reasons
    } : null;
  }

  // 应用上下文规则
  private applyContextRule(rule: FilterRule, memory: MemoryData): FilterResult | null {
    if (!this.config.enableContextualFiltering) return null;

    const context = memory.context || {};
    const condition = rule.condition;
    let matches = false;
    let confidence = 0;
    const reasons: string[] = [];

    // 文件类型检查
    if (condition.fileTypes && context.file?.extension) {
      const fileType = context.file.extension.toLowerCase();
      if (condition.fileTypes.includes(fileType)) {
        matches = true;
        confidence += 0.3;
        reasons.push(`File type match: ${fileType}`);
      }
    }

    // 项目类型检查
    if (condition.projectTypes && context.project?.type) {
      if (condition.projectTypes.includes(context.project.type)) {
        matches = true;
        confidence += 0.4;
        reasons.push(`Project type match: ${context.project.type}`);
      }
    }

    // Git分支检查
    if (condition.gitBranches && context.git?.branch) {
      if (condition.gitBranches.includes(context.git.branch)) {
        matches = true;
        confidence += 0.2;
        reasons.push(`Git branch match: ${context.git.branch}`);
      }
    }

    return matches ? {
      action: rule.action,
      confidence,
      reasons
    } : null;
  }

  // 应用频率规则
  private applyFrequencyRule(rule: FilterRule, memory: MemoryData): FilterResult | null {
    if (!this.config.enableFrequencyFiltering) return null;

    const condition = rule.condition;
    const contentHash = this.generateContentHash(memory.content);
    const now = Date.now();

    // 清理过期的记录
    this.cleanupOldMemories(now);

    // 检查重复频率
    const duplicateCount = this.recentMemories.filter(m => 
      this.generateContentHash(m.content) === contentHash
    ).length;

    if (duplicateCount >= (condition.maxDuplicates || this.config.maxDuplicates)) {
      return {
        action: rule.action,
        confidence: 0.8,
        reasons: [`Too many duplicates: ${duplicateCount}`]
      };
    }

    // 检查类型频率
    if (condition.maxTypeFrequency) {
      const typeCount = this.recentMemories.filter(m => m.type === memory.type).length;
      if (typeCount >= condition.maxTypeFrequency) {
        return {
          action: rule.action,
          confidence: 0.6,
          reasons: [`Too many of type ${memory.type}: ${typeCount}`]
        };
      }
    }

    return null;
  }

  // 应用相似度规则
  private applySimilarityRule(rule: FilterRule, memory: MemoryData): FilterResult | null {
    if (!this.config.enableSimilarityDetection) return null;

    const condition = rule.condition;
    const currentContent = this.extractTextContent(memory.content);

    for (const recentMemory of this.recentMemories) {
      const recentContent = this.extractTextContent(recentMemory.content);
      const similarity = this.calculateSimilarity(currentContent, recentContent);

      if (similarity >= (condition.threshold || this.config.similarityThreshold)) {
        return {
          action: rule.action,
          confidence: similarity,
          reasons: [`High similarity with recent memory: ${similarity.toFixed(2)}`]
        };
      }
    }

    return null;
  }

  // 综合多个结果
  private combineResults(results: FilterResult[], memory: MemoryData): FilterResult {
    if (results.length === 0) {
      return {
        action: 'accept',
        confidence: 1.0,
        reasons: ['No rules matched, accepting by default']
      };
    }

    // 按优先级排序（reject > modify > accept）
    const priorityOrder = { 'reject': 3, 'modify': 2, 'accept': 1 };
    results.sort((a, b) => priorityOrder[b.action] - priorityOrder[a.action]);

    const topResult = results[0];
    const allReasons = results.flatMap(r => r.reasons);
    const avgConfidence = results.reduce((sum, r) => sum + r.confidence, 0) / results.length;

    // 如果有拒绝规则且置信度足够高，直接拒绝
    if (topResult.action === 'reject' && topResult.confidence > 0.7) {
      return {
        action: 'reject',
        confidence: topResult.confidence,
        reasons: allReasons
      };
    }

    // 如果有修改规则，应用修改
    const modifyResults = results.filter(r => r.action === 'modify');
    if (modifyResults.length > 0) {
      const modifiedMemory = this.applyModifications(memory, modifyResults);
      return {
        action: 'modify',
        confidence: avgConfidence,
        reasons: allReasons,
        modifiedMemory
      };
    }

    // 默认接受
    return {
      action: 'accept',
      confidence: avgConfidence,
      reasons: allReasons
    };
  }

  // 应用修改
  private applyModifications(memory: MemoryData, modifyResults: FilterResult[]): MemoryData {
    let modifiedMemory = { ...memory };

    for (const result of modifyResults) {
      // 这里可以根据具体的修改规则来处理
      // 例如：截断内容、添加标签、调整优先级等
      if (result.reasons.some(r => r.includes('too long'))) {
        const content = this.extractTextContent(modifiedMemory.content);
        if (content.length > 1000) {
          modifiedMemory.content = content.substring(0, 1000) + '...';
        }
      }

      if (result.reasons.some(r => r.includes('Low quality'))) {
        modifiedMemory.metadata = {
          ...modifiedMemory.metadata,
          quality: 'low',
          filtered: true
        };
      }
    }

    return modifiedMemory;
  }

  // 更新内部状态
  private updateInternalState(memory: MemoryData, result: FilterResult) {
    if (result.action !== 'reject') {
      // 添加到最近记忆列表
      this.recentMemories.push(memory);
      
      // 更新内容哈希计数
      const contentHash = this.generateContentHash(memory.content);
      const currentCount = this.contentHashes.get(contentHash) || 0;
      this.contentHashes.set(contentHash, currentCount + 1);

      // 限制列表大小
      if (this.recentMemories.length > 100) {
        this.recentMemories.shift();
      }
    }
  }

  // 提取文本内容
  private extractTextContent(content: any): string {
    if (typeof content === 'string') {
      return content;
    }
    if (typeof content === 'object') {
      return JSON.stringify(content);
    }
    return String(content);
  }

  // 生成内容哈希
  private generateContentHash(content: any): string {
    const text = this.extractTextContent(content);
    // 简单的哈希函数
    let hash = 0;
    for (let i = 0; i < text.length; i++) {
      const char = text.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // 转换为32位整数
    }
    return hash.toString();
  }

  // 计算文本相似度
  private calculateSimilarity(text1: string, text2: string): number {
    // 使用简单的Jaccard相似度
    const words1 = new Set(text1.toLowerCase().split(/\s+/));
    const words2 = new Set(text2.toLowerCase().split(/\s+/));
    
    const intersection = new Set([...words1].filter(x => words2.has(x)));
    const union = new Set([...words1, ...words2]);
    
    return intersection.size / union.size;
  }

  // 分析内容质量
  private analyzeContentQuality(content: string): number {
    let score = 0.5; // 基础分数

    // 长度因子
    if (content.length > 50) score += 0.1;
    if (content.length > 200) score += 0.1;

    // 结构因子
    if (content.includes('\n')) score += 0.1; // 有换行
    if (/[.!?]/.test(content)) score += 0.1; // 有标点
    if (/[A-Z]/.test(content)) score += 0.05; // 有大写字母

    // 关键词权重
    for (const [keyword, weight] of this.keywordWeights) {
      if (content.toLowerCase().includes(keyword)) {
        score += weight;
      }
    }

    // 代码特征
    if (/function|class|import|export|const|let|var/.test(content)) {
      score += 0.2; // 包含代码关键词
    }

    return Math.min(score, 1.0);
  }

  // 清理过期记忆
  private cleanupOldMemories(currentTime: number) {
    const cutoffTime = currentTime - this.config.frequencyWindow;
    this.recentMemories = this.recentMemories.filter(memory => {
      const memoryTime = new Date(memory.timestamp).getTime();
      return memoryTime > cutoffTime;
    });
  }

  // 初始化默认规则
  private initializeDefaultRules() {
    this.rules = [
      {
        id: 'reject_empty_content',
        name: 'Reject Empty Content',
        type: 'content',
        condition: { minLength: 5 },
        action: 'reject',
        priority: 10,
        enabled: true
      },
      {
        id: 'reject_low_quality',
        name: 'Reject Low Quality Content',
        type: 'content',
        condition: { minQuality: 0.3 },
        action: 'reject',
        priority: 8,
        enabled: true
      },
      {
        id: 'limit_duplicates',
        name: 'Limit Duplicate Content',
        type: 'frequency',
        condition: { maxDuplicates: 3 },
        action: 'reject',
        priority: 7,
        enabled: true
      },
      {
        id: 'reject_similar',
        name: 'Reject Similar Content',
        type: 'similarity',
        condition: { threshold: 0.9 },
        action: 'reject',
        priority: 6,
        enabled: true
      },
      {
        id: 'truncate_long_content',
        name: 'Truncate Long Content',
        type: 'content',
        condition: { maxLength: 5000 },
        action: 'modify',
        priority: 5,
        enabled: true
      }
    ];
  }

  // 初始化关键词权重
  private initializeKeywordWeights() {
    this.keywordWeights = new Map([
      ['error', 0.3],
      ['bug', 0.3],
      ['fix', 0.2],
      ['implement', 0.2],
      ['create', 0.15],
      ['update', 0.15],
      ['delete', 0.15],
      ['function', 0.1],
      ['class', 0.1],
      ['method', 0.1],
      ['variable', 0.05],
      ['test', 0.1],
      ['debug', 0.2]
    ]);
  }

  // 添加自定义规则
  public addRule(rule: FilterRule) {
    this.rules.push(rule);
    this.rules.sort((a, b) => b.priority - a.priority);
    this.logger.info(`Added filter rule: ${rule.name}`);
  }

  // 移除规则
  public removeRule(ruleId: string) {
    this.rules = this.rules.filter(rule => rule.id !== ruleId);
    this.logger.info(`Removed filter rule: ${ruleId}`);
  }

  // 获取统计信息
  public getStats() {
    return {
      rulesCount: this.rules.length,
      enabledRulesCount: this.rules.filter(r => r.enabled).length,
      recentMemoriesCount: this.recentMemories.length,
      contentHashesCount: this.contentHashes.size,
      config: this.config
    };
  }

  // 清理资源
  public cleanup() {
    this.recentMemories = [];
    this.contentHashes.clear();
    this.logger.info('IntelligentFilter cleaned up');
  }
}