import { EventEmitter } from 'events';
import type { Agent, Memory, PerformanceMetrics, RetrievalQuery, EnhancementContext, EnhancementResult } from '../../types/base';
import { AgentType, AgentStatus } from '../../types/base';
import { MemoryRetriever } from './retriever';

export interface LearningPattern {
  id: string;
  pattern: string;
  frequency: number;
  successRate: number;
  lastUsed: Date;
  contexts: string[];
}

export class AgentEnhancer extends EventEmitter {
  private memoryRetriever: MemoryRetriever;
  private learningPatterns: Map<string, LearningPattern>;
  private enhancementHistory: Map<string, EnhancementResult[]>;
  private performanceBaseline: Map<string, PerformanceMetrics>;

  constructor(
    memoryRetriever: MemoryRetriever
  ) {
    super();
    this.memoryRetriever = memoryRetriever;
    this.learningPatterns = new Map();
    this.enhancementHistory = new Map();
    this.performanceBaseline = new Map();
  }

  public async enhanceAgent(agent: Agent, context: EnhancementContext): Promise<EnhancementResult> {
    const startTime = Date.now();
    
    try {
      // 构建检索查询
      const query = this.buildRetrievalQuery(agent, context);
      
      // 检索相关记忆
      const retrievalResult = await this.memoryRetriever.retrieve(query);
      
      // 分析和应用记忆
      const enhancedAgent = await this.applyMemoriesToAgent(agent, retrievalResult.memories, context);
      
      // 计算性能提升
      const performanceImprovement = this.calculatePerformanceImprovement(agent, enhancedAgent);
      
      // 更新学习模式
      await this.updateLearningPatterns(agent, retrievalResult.memories, context, performanceImprovement);
      
      const result: EnhancementResult = {
        enhancedAgent,
        appliedMemories: retrievalResult.memories,
        relatedKnowledge: retrievalResult.relatedNodes,
        performanceImprovement,
        enhancementTime: Date.now() - startTime
      };

      // 记录增强历史
      this.recordEnhancementHistory(agent.id, result);
      
      this.emit('agentEnhanced', { agent: agent.id, result });
      return result;
      
    } catch (error) {
      this.emit('enhancementError', { agent: agent.id, context, error });
      throw error;
    }
  }

  private buildRetrievalQuery(agent: Agent, context: EnhancementContext): RetrievalQuery {
    const query: RetrievalQuery = {
      limit: 20,
      includeRelated: true,
      semanticSearch: true
    };

    // 基于智能体类型构建查询
    switch (agent.type) {
      case AgentType.RULE_PROCESSOR:
        query.tags = ['rule', 'processing', 'logic'];
        break;
      case AgentType.MEMORY_MANAGER:
        query.tags = ['memory', 'storage', 'retrieval'];
        break;
      case AgentType.KNOWLEDGE_CURATOR:
        query.tags = ['knowledge', 'curation', 'organization'];
        break;
      case AgentType.TASK_EXECUTOR:
        query.tags = ['task', 'execution', 'workflow'];
        break;
      case AgentType.PERFORMANCE_MONITOR:
        query.tags = ['performance', 'monitoring', 'metrics'];
        break;
    }

    // 添加上下文信息
    if (context.currentTask) {
      query.text = context.currentTask;
      query.tags?.push('task');
    }

    if (context.userInput) {
      query.text = (query.text ? query.text + ' ' : '') + context.userInput;
    }

    if (context.domain) {
      query.context = { domain: context.domain };
      query.tags?.push(context.domain);
    }

    if (context.sessionId) {
      query.context = { ...query.context, sessionId: context.sessionId };
    }

    // 基于历史性能调整查询
    const history = this.enhancementHistory.get(agent.id);
    if (history && history.length > 0) {
      const successfulPatterns = history
        .filter(h => h.performanceImprovement > 0)
        .flatMap(h => h.appliedMemories.flatMap(m => m.tags || []));
      
      if (successfulPatterns.length > 0) {
        query.tags = [...(query.tags || []), ...successfulPatterns];
      }
    }

    return query;
  }

  private async applyMemoriesToAgent(agent: Agent, memories: Memory[], context: EnhancementContext): Promise<Agent> {
    const enhancedAgent: Agent = {
      ...agent,
      status: AgentStatus.ENHANCED,
      lastUpdated: new Date()
    };

    // 基于记忆更新智能体配置
    for (const memory of memories) {
      await this.applyMemoryToAgent(enhancedAgent, memory, context);
    }

    // 应用学习模式
    await this.applyLearningPatterns(enhancedAgent, context);

    return enhancedAgent;
  }

  private async applyMemoryToAgent(agent: Agent, memory: Memory, context: EnhancementContext): Promise<void> {
    // 根据记忆类型和内容更新智能体
    switch (memory.type) {
      case 'procedural':
        await this.applyProceduralMemory(agent, memory, context);
        break;
      case 'semantic':
        await this.applySemanticMemory(agent, memory, context);
        break;
      case 'episodic':
        await this.applyEpisodicMemory(agent, memory, context);
        break;
      case 'working':
        await this.applyWorkingMemory(agent, memory, context);
        break;
    }
  }

  private async applyProceduralMemory(agent: Agent, memory: Memory, _context: EnhancementContext): Promise<void> {
    // 程序性记忆：更新智能体的处理流程和方法
    if (memory.content.includes('workflow') || memory.content.includes('process')) {
      // 提取工作流程信息并更新智能体配置
      const workflowPatterns = this.extractWorkflowPatterns(memory.content);
      agent.configuration = {
        ...agent.configuration,
        workflows: [...(agent.configuration.workflows || []), ...workflowPatterns]
      };
    }
  }

  private async applySemanticMemory(agent: Agent, memory: Memory, _context: EnhancementContext): Promise<void> {
    // 语义记忆：更新智能体的知识库和概念理解
    if (memory.tags && memory.tags.some(tag => ['concept', 'definition', 'knowledge'].includes(tag))) {
      const concepts = this.extractConcepts(memory.content);
      agent.configuration = {
        ...agent.configuration,
        knowledgeBase: [...(agent.configuration.knowledgeBase || []), ...concepts]
      };
    }
  }

  private async applyEpisodicMemory(agent: Agent, memory: Memory, context: EnhancementContext): Promise<void> {
    // 情景记忆：基于历史经验调整智能体行为
    if (memory.context && memory.context.task === context.currentTask) {
      // 如果是相同任务的历史经验，调整处理策略
      const strategies = this.extractStrategies(memory.content);
      agent.configuration = {
        ...agent.configuration,
        strategies: [...(agent.configuration.strategies || []), ...strategies]
      };
    }
  }

  private async applyWorkingMemory(agent: Agent, memory: Memory, context: EnhancementContext): Promise<void> {
    // 工作记忆：更新当前任务相关的临时信息
    if (memory.context && memory.context.sessionId === context.sessionId) {
      agent.configuration = {
        ...agent.configuration,
        currentContext: {
          ...agent.configuration.currentContext,
          workingMemory: memory.content
        }
      };
    }
  }

  private async applyLearningPatterns(agent: Agent, context: EnhancementContext): Promise<void> {
    // 应用已学习的模式
    for (const [, pattern] of Array.from(this.learningPatterns)) {
      if (this.isPatternApplicable(pattern, context)) {
        await this.applyPattern(agent, pattern);
      }
    }
  }

  private isPatternApplicable(pattern: LearningPattern, context: EnhancementContext): boolean {
    // 检查模式是否适用于当前上下文
    if (pattern.successRate < 0.5) return false; // 成功率太低
    
    const daysSinceLastUsed = (Date.now() - pattern.lastUsed.getTime()) / (1000 * 60 * 60 * 24);
    if (daysSinceLastUsed > 30) return false; // 太久没用过
    
    // 检查上下文匹配
    if (context.domain && !pattern.contexts.includes(context.domain)) return false;
    if (context.currentTask && !pattern.contexts.some(ctx => context.currentTask!.includes(ctx))) return false;
    
    return true;
  }

  private async applyPattern(agent: Agent, pattern: LearningPattern): Promise<void> {
    // 应用学习模式到智能体
    agent.configuration = {
      ...agent.configuration,
      learnedPatterns: [...(agent.configuration.learnedPatterns || []), pattern.pattern]
    };
    
    // 更新模式使用统计
    pattern.lastUsed = new Date();
    pattern.frequency++;
  }

  private calculatePerformanceImprovement(originalAgent: Agent, enhancedAgent: Agent): number {
    // 计算性能提升（简化版本）
    const baseline = this.performanceBaseline.get(originalAgent.id);
    if (!baseline) return 0;
    
    // 基于配置复杂度和历史表现计算改进
    const configComplexity = Object.keys(enhancedAgent.configuration).length;
    const originalComplexity = Object.keys(originalAgent.configuration).length;
    
    const complexityImprovement = (configComplexity - originalComplexity) / originalComplexity;
    
    // 结合历史成功率
    const history = this.enhancementHistory.get(originalAgent.id);
    const historicalSuccess = history ? 
      history.reduce((sum, h) => sum + h.performanceImprovement, 0) / history.length : 0;
    
    return Math.max(0, Math.min(1, complexityImprovement * 0.7 + historicalSuccess * 0.3));
  }

  private async updateLearningPatterns(
    agent: Agent, 
    memories: Memory[], 
    context: EnhancementContext, 
    performance: number
  ): Promise<void> {
    // 从成功的增强中学习模式
    if (performance > 0.1) { // 只从有效的改进中学习
      for (const memory of memories) {
        const patternId = `${agent.type}_${memory.type}_${(memory.tags || []).join('_')}`;
        
        let pattern = this.learningPatterns.get(patternId);
        if (!pattern) {
          pattern = {
            id: patternId,
            pattern: memory.content.substring(0, 100), // 提取模式摘要
            frequency: 0,
            successRate: 0,
            lastUsed: new Date(),
            contexts: []
          };
          this.learningPatterns.set(patternId, pattern);
        }
        
        // 更新模式统计
        pattern.frequency++;
        pattern.successRate = (pattern.successRate + performance) / 2; // 移动平均
        pattern.lastUsed = new Date();
        
        // 添加上下文
        if (context.domain && !pattern.contexts.includes(context.domain)) {
          pattern.contexts.push(context.domain);
        }
        if (context.currentTask && !pattern.contexts.includes(context.currentTask)) {
          pattern.contexts.push(context.currentTask);
        }
      }
    }
  }

  private recordEnhancementHistory(agentId: string, result: EnhancementResult): void {
    if (!this.enhancementHistory.has(agentId)) {
      this.enhancementHistory.set(agentId, []);
    }
    
    const history = this.enhancementHistory.get(agentId)!;
    history.push(result);
    
    // 保持历史记录在合理范围内
    if (history.length > 100) {
      history.splice(0, history.length - 100);
    }
  }

  private extractWorkflowPatterns(content: string): string[] {
    // 简化的工作流程模式提取
    const patterns: string[] = [];
    const workflowKeywords = ['step', 'process', 'workflow', 'procedure'];
    
    for (const keyword of workflowKeywords) {
      if (content.toLowerCase().includes(keyword)) {
        patterns.push(`${keyword}_pattern`);
      }
    }
    
    return patterns;
  }

  private extractConcepts(content: string): string[] {
    // 简化的概念提取
    const concepts: string[] = [];
    const words = content.split(/\s+/);
    
    // 提取名词性概念（简化版本）
    for (const word of words) {
      if (word.length > 3 && /^[A-Z]/.test(word)) {
        concepts.push(word.toLowerCase());
      }
    }
    
    return Array.from(new Set(concepts)); // 去重
  }

  private extractStrategies(content: string): string[] {
    // 简化的策略提取
    const strategies: string[] = [];
    const strategyKeywords = ['approach', 'method', 'strategy', 'technique'];
    
    for (const keyword of strategyKeywords) {
      if (content.toLowerCase().includes(keyword)) {
        strategies.push(`${keyword}_based`);
      }
    }
    
    return strategies;
  }

  public async setPerformanceBaseline(agentId: string, metrics: PerformanceMetrics): Promise<void> {
    this.performanceBaseline.set(agentId, metrics);
    this.emit('baselineSet', { agentId, metrics });
  }

  public getLearningPatterns(): LearningPattern[] {
    return Array.from(this.learningPatterns.values());
  }

  public getEnhancementHistory(agentId: string): EnhancementResult[] {
    return this.enhancementHistory.get(agentId) || [];
  }

  public getStats() {
    return {
      learningPatternsCount: this.learningPatterns.size,
      enhancedAgentsCount: this.enhancementHistory.size,
      totalEnhancements: Array.from(this.enhancementHistory.values())
        .reduce((sum, history) => sum + history.length, 0),
      averagePerformanceImprovement: this.calculateAverageImprovement()
    };
  }

  private calculateAverageImprovement(): number {
    const allResults = Array.from(this.enhancementHistory.values()).flat();
    if (allResults.length === 0) return 0;
    
    return allResults.reduce((sum, result) => sum + result.performanceImprovement, 0) / allResults.length;
  }

  public destroy(): void {
    this.learningPatterns.clear();
    this.enhancementHistory.clear();
    this.performanceBaseline.clear();
    this.removeAllListeners();
  }
}