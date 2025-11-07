/**
 * MemoryRetrievalManager 单元测试
 * 
 * @description 测试记忆检索管理器的各种功能
 * @author 高级软件专家
 */

import { MemoryRetrievalManager } from '../../../../src/services/memory-retrieval/manager';
import { ConfigurationManager } from '../../../../src/config/manager';
import { MemoryType } from '../../../../src/types/base';
import type { 
  RetrievalQuery, 
  EnhancementContext,
  Agent,
  Memory,
  RetrievalResult
} from '../../../../src/types/base';

// 扩展的增强上下文接口，用于测试
interface ExtendedEnhancementContext extends EnhancementContext {
  agent?: Agent;
  task?: {
    type: string;
    description: string;
    requirements?: string[];
  };
  environment?: {
    userId?: string;
    sessionId?: string;
    urgency?: string;
    stakeholderMeeting?: string;
  };
}

describe('MemoryRetrievalManager', () => {
  let retrievalManager: MemoryRetrievalManager;
  let configManager: ConfigurationManager;
  let testAgent: Agent;

  beforeEach(async () => {
    configManager = new ConfigurationManager();
    await configManager.initialize();
    
    retrievalManager = new MemoryRetrievalManager(configManager);
    await retrievalManager.initialize();

    // 定义测试智能体
    testAgent = {
      id: 'agent1',
      name: 'Test Agent',
      type: 'assistant',
      capabilities: ['reasoning', 'planning'],
      knowledge: {
        facts: [],
        rules: [],
        procedures: []
      },
      memory: {
        working: [],
        episodic: [],
        semantic: [],
        procedural: []
      },
      performance: {
        successRate: 0.7,
        averageResponseTime: 1000,
        taskCompletionRate: 0.8
      },
      metadata: {
        version: '1.0.0',
        lastUpdated: new Date()
      }
    } as any;
  });

  afterEach(async () => {
    await retrievalManager.destroy();
    await configManager.destroy();
  });

  describe('记忆检索', () => {
    beforeEach(async () => {
      // 添加测试记忆
      const memories: Memory[] = [
        {
          id: 'mem1',
          type: 'episodic',
          content: 'User completed task A successfully',
          context: {
            userId: 'user1',
            taskType: 'A',
            outcome: 'success'
          },
          importance: 0.8,
          createdAt: new Date('2024-01-01'),
          updatedAt: new Date('2024-01-01'),
          metadata: {
            tags: ['task', 'success'],
            source: 'system'
          }
        },
        {
          id: 'mem2',
          type: 'semantic',
          content: 'Task A requires careful planning',
          context: {
            taskType: 'A',
            domain: 'planning'
          },
          importance: 0.6,
          createdAt: new Date('2024-01-02'),
          updatedAt: new Date('2024-01-02'),
          metadata: {
            tags: ['task', 'planning'],
            source: 'knowledge'
          }
        },
        {
          id: 'mem3',
          type: 'procedural',
          content: 'Steps for task A: 1. Analyze, 2. Plan, 3. Execute',
          context: {
            taskType: 'A',
            domain: 'procedure'
          },
          importance: 0.9,
          createdAt: new Date('2024-01-03'),
          updatedAt: new Date('2024-01-03'),
          metadata: {
            tags: ['task', 'procedure'],
            source: 'experience'
          }
        }
      ];

      for (const memory of memories) {
        await retrievalManager.storeMemory(memory);
      }
    });

    test('应该能够基于查询检索记忆', async () => {
      const query: RetrievalQuery = {
        text: 'task A completion',
        context: {
          userId: 'user1',
          taskType: 'A'
        },
        filters: {
          type: ['episodic', 'procedural']
        },
        limit: 10
      };

      const result = await retrievalManager.retrieveMemories(query);
      
      expect(result.memories.length).toBeGreaterThan(0);
      expect(result.confidence).toBeGreaterThan(0);
      
      // 应该包含相关的记忆
      const memoryIds = result.memories.map(m => m.id);
      expect(memoryIds).toContain('mem1'); // episodic memory
      expect(memoryIds).toContain('mem3'); // procedural memory
    });

    test('应该能够按重要性排序检索结果', async () => {
      const query: RetrievalQuery = {
        text: 'task A',
        context: {},
        sortBy: 'importance',
        limit: 10
      };

      const result = await retrievalManager.retrieveMemories(query);
      
      expect(result.memories.length).toBe(3);
      
      // 应该按重要性降序排列
      for (let i = 0; i < result.memories.length - 1; i++) {
        expect(result.memories[i].importance).toBeGreaterThanOrEqual(
          result.memories[i + 1].importance
        );
      }
    });

    test('应该能够按时间排序检索结果', async () => {
      const query: RetrievalQuery = {
        text: 'task',
        context: {},
        sortBy: 'recency',
        limit: 10
      };

      const result = await retrievalManager.retrieveMemories(query);
      
      expect(result.memories.length).toBe(3);
      
      // 应该按时间降序排列（最新的在前）
      for (let i = 0; i < result.memories.length - 1; i++) {
        expect(result.memories[i].createdAt.getTime()).toBeGreaterThanOrEqual(
          result.memories[i + 1].createdAt.getTime()
        );
      }
    });

    test('应该能够使用过滤器', async () => {
      const query: RetrievalQuery = {
        text: 'task',
        context: {},
        filters: {
          type: ['semantic'],
          'metadata.tags': ['planning']
        },
        limit: 10
      };

      const result = await retrievalManager.retrieveMemories(query);
      
      expect(result.memories.length).toBe(1);
      expect(result.memories[0].id).toBe('mem2');
      expect(result.memories[0].type).toBe('semantic');
    });
  });

  describe('智能体增强', () => {
    test('应该能够增强智能体', async () => {
      const context: ExtendedEnhancementContext = {
        agent: testAgent,
        task: {
          type: 'A',
          description: 'Complete task A',
          requirements: ['planning', 'execution']
        },
        environment: {
          userId: 'user1',
          sessionId: 'session1'
        }
      };

      const result = await retrievalManager.enhanceAgent(context);
      
      expect(result.success).toBe(true);
      expect(result.enhancedAgent).toBeDefined();
      expect(result.appliedMemories.length).toBeGreaterThan(0);
      expect(result.performanceImprovement).toBeGreaterThan(0);
      
      // 验证智能体被增强
      const enhancedAgent = result.enhancedAgent!;
      expect(enhancedAgent.memory.episodic.length).toBeGreaterThan(0);
      expect(enhancedAgent.memory.procedural.length).toBeGreaterThan(0);
    });

    test('应该能够异步增强智能体', async () => {
      const context: ExtendedEnhancementContext = {
        agent: testAgent,
        task: {
          type: 'A',
          description: 'Complete task A asynchronously',
          requirements: ['planning']
        },
        environment: {
          userId: 'user1'
        }
      };

      const enhancementId = await retrievalManager.enhanceAgentAsync(context);
      
      expect(typeof enhancementId).toBe('string');
      expect(enhancementId.length).toBeGreaterThan(0);
      
      // 等待异步处理完成
      await new Promise(resolve => setTimeout(resolve, 100));
      
      const status = await retrievalManager.getEnhancementStatus(enhancementId);
      expect(['pending', 'processing', 'completed']).toContain(status.status);
    });

    test('应该能够获取增强状态', async () => {
      const context: ExtendedEnhancementContext = {
        agent: testAgent,
        task: {
          type: 'A',
          description: 'Status test task'
        },
        environment: {}
      };

      const enhancementId = await retrievalManager.enhanceAgentAsync(context);
      const status = await retrievalManager.getEnhancementStatus(enhancementId);
      
      expect(status.id).toBe(enhancementId);
      expect(['pending', 'processing', 'completed', 'failed']).toContain(status.status);
      expect(status.createdAt).toBeDefined();
    });

    test('应该能够取消增强任务', async () => {
      const context: ExtendedEnhancementContext = {
        agent: testAgent,
        task: {
          type: 'A',
          description: 'Cancellation test task'
        },
        environment: {}
      };

      const enhancementId = await retrievalManager.enhanceAgentAsync(context);
      const cancelled = await retrievalManager.cancelEnhancement(enhancementId);
      
      expect(cancelled).toBe(true);
      
      const status = await retrievalManager.getEnhancementStatus(enhancementId);
      expect(status.status).toBe('cancelled');
    });
  });

  describe('相似记忆搜索', () => {
    beforeEach(async () => {
      const memories: Memory[] = [
        {
          id: 'sim1',
          type: MemoryType.EPISODIC,
          content: 'User solved math problem using algebra',
          context: { domain: 'math', method: 'algebra' },
          importance: 0.7,
          createdAt: new Date(),
          updatedAt: new Date(),
          metadata: { tags: ['math', 'algebra'] }
        },
        {
          id: 'sim2',
          type: MemoryType.EPISODIC,
          content: 'User solved math problem using geometry',
          context: { domain: 'math', method: 'geometry' },
          importance: 0.6,
          createdAt: new Date(),
          updatedAt: new Date(),
          metadata: { tags: ['math', 'geometry'] }
        },
        {
          id: 'sim3',
          type: MemoryType.EPISODIC,
          content: 'User completed programming task',
          context: { domain: 'programming', language: 'javascript' },
          importance: 0.8,
          createdAt: new Date(),
          updatedAt: new Date(),
          metadata: { tags: ['programming', 'javascript'] }
        }
      ];

      for (const memory of memories) {
        await retrievalManager.storeMemory(memory);
      }
    });

    test('应该能够找到相似记忆', async () => {
      const targetMemory: Memory = {
        id: 'target',
        type: MemoryType.EPISODIC,
        content: 'User needs help with math problem',
        context: { domain: 'math' },
        importance: 0.5,
        createdAt: new Date(),
        updatedAt: new Date(),
        metadata: { tags: ['math', 'help'] }
      };

      const similarMemories = await retrievalManager.findSimilarMemories(
        targetMemory,
        { limit: 5, threshold: 0.1 }
      );

      expect(similarMemories.length).toBeGreaterThan(0);
      
      // 数学相关的记忆应该有更高的相似度
      const mathMemories = similarMemories.filter(
        sm => sm.memory.context?.domain === 'math'
      );
      expect(mathMemories.length).toBeGreaterThan(0);
      
      // 相似度应该在合理范围内
      for (const sm of similarMemories) {
        expect(sm.similarity).toBeGreaterThan(0);
        expect(sm.similarity).toBeLessThanOrEqual(1);
      }
    });

    test('应该能够设置相似度阈值', async () => {
      const targetMemory: Memory = {
        id: 'target',
        type: MemoryType.EPISODIC,
        content: 'Programming challenge',
        context: { domain: 'programming' },
        importance: 0.5,
        createdAt: new Date(),
        updatedAt: new Date(),
        metadata: { tags: ['programming'] }
      };

      const highThreshold = await retrievalManager.findSimilarMemories(
        targetMemory,
        { limit: 10, threshold: 0.8 }
      );

      const lowThreshold = await retrievalManager.findSimilarMemories(
        targetMemory,
        { limit: 10, threshold: 0.1 }
      );

      expect(lowThreshold.length).toBeGreaterThanOrEqual(highThreshold.length);
    });
  });

  describe('记忆推荐', () => {
    test('应该能够为智能体推荐记忆', async () => {
      const recommendations = await retrievalManager.recommendMemories(
        testAgent,
        { limit: 5 }
      );

      expect(Array.isArray(recommendations)).toBe(true);
      
      for (const rec of recommendations) {
        expect(rec.memory).toBeDefined();
        expect(rec.relevance).toBeGreaterThan(0);
        expect(rec.relevance).toBeLessThanOrEqual(1);
        expect(rec.reason).toBeDefined();
      }
    });

    test('应该能够基于任务推荐记忆', async () => {
      const task = {
        type: 'A',
        description: 'Complete task A with planning',
        requirements: ['planning', 'execution']
      };

      const recommendations = await retrievalManager.recommendMemories(
        testAgent as any,
        { limit: 5, task }
      );

      expect(recommendations.length).toBeGreaterThan(0);
      
      // 推荐应该与任务相关
      const taskRelated = recommendations.filter(
        rec => rec.memory.context?.['taskType'] === 'A' ||
               rec.memory.metadata?.['tags']?.includes('planning')
      );
      expect(taskRelated.length).toBeGreaterThan(0);
    });
  });

  describe('查询模式分析', () => {
    test('应该能够分析查询模式', async () => {
      // 执行多个查询
      const queries = [
        { text: 'task A', context: { userId: 'user1' } },
        { text: 'task A planning', context: { userId: 'user1' } },
        { text: 'task B', context: { userId: 'user2' } },
        { text: 'task A execution', context: { userId: 'user1' } }
      ];

      for (const query of queries) {
        await retrievalManager.retrieveMemories(query);
      }

      const patterns = await retrievalManager.analyzeQueryPatterns({
        timeRange: {
          start: new Date(Date.now() - 24 * 60 * 60 * 1000), // 24小时前
          end: new Date()
        }
      });

      expect(patterns.totalQueries).toBe(4);
      expect(patterns.uniqueUsers).toBeGreaterThan(0);
      expect(patterns.commonTerms.length).toBeGreaterThan(0);
      expect(patterns.queryFrequency).toBeDefined();
    });

    test('应该能够获取热门查询', async () => {
      // 执行重复查询
      const popularQuery = { text: 'popular task', context: {} };
      
      for (let i = 0; i < 5; i++) {
        await retrievalManager.retrieveMemories(popularQuery);
      }

      const patterns = await retrievalManager.analyzeQueryPatterns({
        timeRange: {
          start: new Date(Date.now() - 60 * 60 * 1000), // 1小时前
          end: new Date()
        }
      });

      expect(patterns.popularQueries.length).toBeGreaterThan(0);
      
      const topQuery = patterns.popularQueries[0];
      expect(topQuery?.query).toContain('popular task');
      expect(topQuery?.count).toBeGreaterThanOrEqual(5);
    });
  });

  describe('增强模式记录', () => {
    test('应该能够记录成功的增强模式', async () => {
      const pattern = {
        agentType: 'assistant',
        taskType: 'A',
        memoryTypes: ['episodic', 'procedural'],
        context: { domain: 'planning' },
        outcome: {
          success: true,
          performanceImprovement: 0.2,
          executionTime: 500
        }
      };

      await retrievalManager.recordEnhancementPattern(pattern);

      const patterns = await retrievalManager.getEnhancementPatterns({
        agentType: 'assistant',
        taskType: 'A'
      });

      expect(patterns.length).toBeGreaterThan(0);
      
      const recordedPattern = patterns.find(
        p => p.agentType === 'assistant' && p.taskType === 'A'
      );
      expect(recordedPattern).toBeDefined();
      expect(recordedPattern!.outcome.success).toBe(true);
    });

    test('应该能够基于历史模式优化增强', async () => {
      // 记录多个成功模式
      const patterns = [
        {
          agentType: 'assistant',
          taskType: 'A',
          memoryTypes: ['procedural'],
          context: { domain: 'planning' },
          outcome: { success: true, performanceImprovement: 0.3 }
        },
        {
          agentType: 'assistant',
          taskType: 'A',
          memoryTypes: ['episodic', 'procedural'],
          context: { domain: 'planning' },
          outcome: { success: true, performanceImprovement: 0.5 }
        }
      ];

      for (const pattern of patterns) {
        await retrievalManager.recordEnhancementPattern(pattern);
      }

      const optimization = await retrievalManager.optimizeEnhancement({
        agentType: 'assistant',
        taskType: 'A',
        context: { domain: 'planning' }
      });

      expect(optimization.recommendedMemoryTypes).toBeDefined();
      expect(optimization.expectedImprovement).toBeGreaterThan(0);
      expect(optimization.confidence).toBeGreaterThan(0);
    });
  });

  describe('统计和监控', () => {
    test('应该提供检索统计信息', async () => {
      // 执行一些检索操作
      await retrievalManager.retrieveMemories({ text: 'test', context: {} });
      await retrievalManager.retrieveMemories({ text: 'another test', context: {} });

      const stats = retrievalManager.getStats();
      
      expect(stats.totalQueries).toBeGreaterThanOrEqual(2);
      expect(stats.totalMemories).toBeGreaterThan(0);
      expect(stats.averageRetrievalTime).toBeGreaterThan(0);
      expect(stats.cacheHitRate).toBeGreaterThanOrEqual(0);
      expect(stats.enhancementQueue.pending).toBeGreaterThanOrEqual(0);
    });

    test('应该跟踪性能指标', async () => {
      const startTime = Date.now();
      
      await retrievalManager.retrieveMemories({
        text: 'performance test',
        context: {},
        limit: 10
      });

      const endTime = Date.now();
      const executionTime = endTime - startTime;

      const stats = retrievalManager.getStats();
      expect(stats.averageRetrievalTime).toBeGreaterThan(0);
      expect(stats.averageRetrievalTime).toBeLessThan(executionTime * 2);
    });
  });

  describe('错误处理', () => {
    test('应该处理无效的检索查询', async () => {
      const invalidQuery = {
        text: '',
        context: null as any,
        limit: -1
      };

      await expect(
        retrievalManager.retrieveMemories(invalidQuery)
      ).rejects.toThrow();
    });

    test('应该处理增强失败', async () => {
      const invalidContext: ExtendedEnhancementContext = {
        agent: null as any,
        task: {
          type: 'invalid',
          description: 'Invalid task'
        },
        environment: {}
      };

      const result = await retrievalManager.enhanceAgent(invalidContext);
      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
    });

    test('应该处理不存在的增强任务', async () => {
      const status = await retrievalManager.getEnhancementStatus('non-existent-id');
      expect(status.status).toBe('not_found');
    });

    test('应该处理记忆存储错误', async () => {
      const invalidMemory = {
        id: '',
        type: 'invalid' as any,
        content: null as any,
        context: {},
        importance: -1,
        createdAt: new Date(),
        updatedAt: new Date(),
        metadata: {}
      };

      await expect(
        retrievalManager.storeMemory(invalidMemory)
      ).rejects.toThrow();
    });
  });
});