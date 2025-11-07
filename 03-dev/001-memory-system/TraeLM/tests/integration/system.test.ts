/**
 * 长期记忆系统集成测试
 * 
 * @description 测试整个长期记忆系统的集成功能
 * @author 高级软件专家
 */

import { LongTermMemorySystem } from '../../src';
import type { 
  Agent, 
  Memory, 
  Rule, 
  KnowledgeNode,
  EnhancementContext 
} from '../../src/types/base';

describe('长期记忆系统集成测试', () => {
  let memorySystem: LongTermMemorySystem;

  beforeAll(async () => {
    memorySystem = new LongTermMemorySystem();
    await memorySystem.initialize();
  });

  afterAll(async () => {
    await memorySystem.destroy();
  });

  describe('系统初始化和配置', () => {
    test('应该成功初始化所有组件', async () => {
      expect(memorySystem.isInitialized()).toBe(true);
      
      // 验证各个管理器都已初始化
      const configManager = memorySystem.getConfigurationManager();
      const ruleManager = memorySystem.getRuleManager();
      const graphManager = memorySystem.getKnowledgeGraphManager();
      const retrievalManager = memorySystem.getMemoryRetrievalManager();
      
      expect(configManager).toBeDefined();
      expect(ruleManager).toBeDefined();
      expect(graphManager).toBeDefined();
      expect(retrievalManager).toBeDefined();
    });

    test('应该能够获取系统统计信息', async () => {
      const stats = await memorySystem.getSystemStats();
      
      expect(stats.rules).toBeDefined();
      expect(stats.knowledge).toBeDefined();
      expect(stats.memories).toBeDefined();
      expect(stats.performance).toBeDefined();
      expect(stats.uptime).toBeGreaterThan(0);
    });

    test('应该能够更新系统配置', async () => {
      const newConfig = {
        memory: {
          maxSize: 2000,
          retentionDays: 60
        },
        performance: {
          enableMonitoring: true,
          metricsInterval: 30000
        }
      };

      await memorySystem.updateConfiguration(newConfig);
      
      const configManager = memorySystem.getConfigurationManager();
      const config = configManager.getConfig();
      
      expect(config.memory.maxSize).toBe(2000);
      expect(config.memory.retentionDays).toBe(60);
    });
  });

  describe('端到端记忆管理流程', () => {
    let testAgent: Agent;
    let testMemories: Memory[];

    beforeEach(() => {
      testAgent = {
        id: 'integration-agent',
        name: 'Integration Test Agent',
        type: 'assistant',
        capabilities: ['reasoning', 'planning', 'learning'],
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
          successRate: 0.75,
          averageResponseTime: 800,
          taskCompletionRate: 0.85
        },
        metadata: {
          version: '1.0.0',
          lastUpdated: new Date()
        }
      };

      testMemories = [
        {
          id: 'mem-integration-1',
          type: 'episodic',
          content: 'User successfully completed complex planning task',
          context: {
            userId: 'user123',
            taskType: 'planning',
            complexity: 'high',
            outcome: 'success'
          },
          importance: 0.9,
          createdAt: new Date('2024-01-01'),
          updatedAt: new Date('2024-01-01'),
          metadata: {
            tags: ['planning', 'success', 'complex'],
            source: 'user-interaction'
          }
        },
        {
          id: 'mem-integration-2',
          type: 'semantic',
          content: 'Complex planning tasks require breaking down into smaller steps',
          context: {
            domain: 'planning',
            concept: 'decomposition'
          },
          importance: 0.8,
          createdAt: new Date('2024-01-02'),
          updatedAt: new Date('2024-01-02'),
          metadata: {
            tags: ['planning', 'strategy', 'decomposition'],
            source: 'knowledge-base'
          }
        },
        {
          id: 'mem-integration-3',
          type: 'procedural',
          content: 'Planning procedure: 1. Analyze requirements, 2. Identify constraints, 3. Generate alternatives, 4. Evaluate options, 5. Select best approach',
          context: {
            domain: 'planning',
            procedure: 'systematic-planning'
          },
          importance: 0.85,
          createdAt: new Date('2024-01-03'),
          updatedAt: new Date('2024-01-03'),
          metadata: {
            tags: ['planning', 'procedure', 'systematic'],
            source: 'best-practices'
          }
        }
      ];
    });

    test('应该能够存储和检索记忆', async () => {
      // 存储记忆
      for (const memory of testMemories) {
        await memorySystem.storeMemory(memory);
      }

      // 检索记忆
      const retrievedMemories = await memorySystem.retrieveMemories({
        text: 'planning task',
        context: { domain: 'planning' },
        limit: 10
      });

      expect(retrievedMemories.length).toBeGreaterThan(0);
      
      const memoryIds = retrievedMemories.map(r => r.memory.id);
      expect(memoryIds).toContain('mem-integration-1');
      expect(memoryIds).toContain('mem-integration-2');
      expect(memoryIds).toContain('mem-integration-3');
    });

    test('应该能够增强智能体并提升性能', async () => {
      // 先存储记忆
      for (const memory of testMemories) {
        await memorySystem.storeMemory(memory);
      }

      const enhancementContext: EnhancementContext = {
        agent: testAgent,
        task: {
          type: 'planning',
          description: 'Create a comprehensive project plan',
          requirements: ['analysis', 'decomposition', 'scheduling']
        },
        environment: {
          userId: 'user123',
          sessionId: 'session456'
        }
      };

      const result = await memorySystem.enhanceAgent(enhancementContext);

      expect(result.success).toBe(true);
      expect(result.enhancedAgent).toBeDefined();
      expect(result.appliedMemories.length).toBeGreaterThan(0);
      expect(result.performanceImprovement).toBeGreaterThan(0);

      // 验证智能体记忆被更新
      const enhancedAgent = result.enhancedAgent!;
      expect(enhancedAgent.memory.episodic.length).toBeGreaterThan(0);
      expect(enhancedAgent.memory.semantic.length).toBeGreaterThan(0);
      expect(enhancedAgent.memory.procedural.length).toBeGreaterThan(0);

      // 验证性能指标改善
      expect(enhancedAgent.performance.successRate).toBeGreaterThan(testAgent.performance.successRate);
    });

    test('应该能够基于规则自动处理记忆', async () => {
      // 添加记忆处理规则
      const memoryRule: Omit<Rule, 'id' | 'createdAt' | 'updatedAt'> = {
        name: 'High Importance Memory Rule',
        description: 'Automatically promote high importance memories',
        category: 'memory-management',
        priority: 8,
        enabled: true,
        conditions: [{
          field: 'memory.importance',
          operator: 'gte',
          value: 0.8
        }],
        actions: [{
          type: 'promoteMemory',
          parameters: {
            targetType: 'long-term',
            boostFactor: 1.2
          }
        }],
        metadata: {
          automated: true
        }
      };

      const ruleManager = memorySystem.getRuleManager();
      await ruleManager.addRule(memoryRule);

      // 存储高重要性记忆
      const highImportanceMemory: Memory = {
        id: 'high-importance-mem',
        type: 'semantic',
        content: 'Critical system knowledge',
        context: { criticality: 'high' },
        importance: 0.95,
        createdAt: new Date(),
        updatedAt: new Date(),
        metadata: { tags: ['critical'] }
      };

      await memorySystem.storeMemory(highImportanceMemory);

      // 触发规则处理
      const ruleContext = {
        memory: highImportanceMemory,
        environment: 'production'
      };

      const ruleResults = await ruleManager.processEvent(ruleContext);
      expect(ruleResults.length).toBeGreaterThan(0);
      expect(ruleResults[0].success).toBe(true);
    });
  });

  describe('知识图谱集成', () => {
    test('应该能够将记忆转换为知识节点', async () => {
      const memory: Memory = {
        id: 'knowledge-mem',
        type: 'semantic',
        content: 'Machine learning is a subset of artificial intelligence',
        context: {
          domain: 'AI',
          concept: 'machine-learning'
        },
        importance: 0.8,
        createdAt: new Date(),
        updatedAt: new Date(),
        metadata: {
          tags: ['AI', 'ML', 'concept'],
          source: 'knowledge-base'
        }
      };

      await memorySystem.storeMemory(memory);

      // 将记忆转换为知识节点
      const graphManager = memorySystem.getKnowledgeGraphManager();
      
      const conceptNode: Omit<KnowledgeNode, 'id' | 'createdAt' | 'updatedAt'> = {
        type: 'concept',
        label: 'Machine Learning',
        properties: {
          definition: memory.content,
          domain: memory.context.domain,
          importance: memory.importance
        },
        metadata: {
          sourceMemoryId: memory.id,
          tags: memory.metadata.tags
        }
      };

      const nodeId = await graphManager.addNode(conceptNode);
      expect(typeof nodeId).toBe('string');

      // 验证节点创建成功
      const retrievedNode = await graphManager.getNode(nodeId);
      expect(retrievedNode).toBeDefined();
      expect(retrievedNode!.label).toBe('Machine Learning');
      expect(retrievedNode!.metadata.sourceMemoryId).toBe(memory.id);
    });

    test('应该能够基于知识图谱增强记忆检索', async () => {
      const graphManager = memorySystem.getKnowledgeGraphManager();
      
      // 创建相关概念节点
      const aiNode = await graphManager.addNode({
        type: 'concept',
        label: 'Artificial Intelligence',
        properties: { domain: 'technology' },
        metadata: {}
      });

      const mlNode = await graphManager.addNode({
        type: 'concept',
        label: 'Machine Learning',
        properties: { domain: 'technology' },
        metadata: {}
      });

      // 创建关系
      await graphManager.addEdge({
        sourceId: mlNode,
        targetId: aiNode,
        type: 'is_subset_of',
        label: 'Is Subset Of',
        properties: { strength: 0.9 },
        metadata: {}
      });

      // 存储相关记忆
      const memories = [
        {
          id: 'ai-mem-1',
          type: 'semantic' as const,
          content: 'AI systems can learn from data',
          context: { concept: 'artificial-intelligence' },
          importance: 0.7,
          createdAt: new Date(),
          updatedAt: new Date(),
          metadata: { tags: ['AI', 'learning'] }
        },
        {
          id: 'ml-mem-1',
          type: 'semantic' as const,
          content: 'Machine learning algorithms improve with experience',
          context: { concept: 'machine-learning' },
          importance: 0.8,
          createdAt: new Date(),
          updatedAt: new Date(),
          metadata: { tags: ['ML', 'algorithms'] }
        }
      ];

      for (const memory of memories) {
        await memorySystem.storeMemory(memory);
      }

      // 基于图谱关系检索相关记忆
      const retrievalResults = await memorySystem.retrieveMemories({
        text: 'machine learning',
        context: { expandWithGraph: true },
        limit: 10
      });

      expect(retrievalResults.length).toBeGreaterThan(0);
      
      // 应该包含直接相关和间接相关的记忆
      const memoryIds = retrievalResults.map(r => r.memory.id);
      expect(memoryIds).toContain('ml-mem-1');
      // 可能也包含AI相关记忆（通过图谱关系）
    });
  });

  describe('性能和扩展性测试', () => {
    test('应该能够处理大量记忆存储', async () => {
      const batchSize = 100;
      const memories: Memory[] = [];

      for (let i = 0; i < batchSize; i++) {
        memories.push({
          id: `batch-mem-${i}`,
          type: 'episodic',
          content: `Batch memory content ${i}`,
          context: {
            batchId: 'performance-test',
            index: i
          },
          importance: Math.random(),
          createdAt: new Date(),
          updatedAt: new Date(),
          metadata: {
            tags: ['batch', 'performance'],
            index: i
          }
        });
      }

      const startTime = Date.now();
      
      // 批量存储记忆
      for (const memory of memories) {
        await memorySystem.storeMemory(memory);
      }

      const endTime = Date.now();
      const totalTime = endTime - startTime;

      // 验证性能（应该在合理时间内完成）
      expect(totalTime).toBeLessThan(30000); // 30秒内完成
      
      // 验证存储成功
      const retrievalResults = await memorySystem.retrieveMemories({
        text: 'batch memory',
        context: { batchId: 'performance-test' },
        limit: batchSize
      });

      expect(retrievalResults.length).toBe(batchSize);
    });

    test('应该能够处理并发增强请求', async () => {
      const concurrentRequests = 10;
      const agents: Agent[] = [];

      // 创建多个测试智能体
      for (let i = 0; i < concurrentRequests; i++) {
        agents.push({
          id: `concurrent-agent-${i}`,
          name: `Concurrent Agent ${i}`,
          type: 'assistant',
          capabilities: ['reasoning'],
          knowledge: { facts: [], rules: [], procedures: [] },
          memory: { working: [], episodic: [], semantic: [], procedural: [] },
          performance: {
            successRate: 0.7,
            averageResponseTime: 1000,
            taskCompletionRate: 0.8
          },
          metadata: {
            version: '1.0.0',
            lastUpdated: new Date()
          }
        });
      }

      // 并发执行增强请求
      const enhancementPromises = agents.map(agent => 
        memorySystem.enhanceAgent({
          agent,
          task: {
            type: 'concurrent-test',
            description: `Concurrent enhancement test for ${agent.id}`
          },
          environment: {
            testId: 'concurrent-performance'
          }
        })
      );

      const startTime = Date.now();
      const results = await Promise.all(enhancementPromises);
      const endTime = Date.now();

      // 验证所有请求都成功处理
      expect(results.length).toBe(concurrentRequests);
      
      for (const result of results) {
        expect(result.success).toBe(true);
        expect(result.enhancedAgent).toBeDefined();
      }

      // 验证并发性能
      const totalTime = endTime - startTime;
      expect(totalTime).toBeLessThan(15000); // 15秒内完成
    });

    test('应该能够监控系统性能', async () => {
      // 执行一些操作来生成性能数据
      await memorySystem.storeMemory({
        id: 'perf-test-mem',
        type: 'episodic',
        content: 'Performance test memory',
        context: { test: 'performance' },
        importance: 0.5,
        createdAt: new Date(),
        updatedAt: new Date(),
        metadata: { tags: ['performance'] }
      });

      await memorySystem.retrieveMemories({
        text: 'performance test',
        context: {},
        limit: 5
      });

      // 获取性能统计
      const stats = await memorySystem.getSystemStats();
      
      expect(stats.performance.memoryOperations).toBeGreaterThan(0);
      expect(stats.performance.averageResponseTime).toBeGreaterThan(0);
      expect(stats.performance.systemLoad).toBeDefined();
      expect(stats.performance.memoryUsage).toBeDefined();
    });
  });

  describe('错误恢复和容错性', () => {
    test('应该能够从组件故障中恢复', async () => {
      // 模拟组件故障和恢复
      const configManager = memorySystem.getConfigurationManager();
      
      // 暂时禁用某个功能
      await configManager.updateConfig({
        features: {
          knowledgeGraph: false
        }
      });

      // 尝试执行需要知识图谱的操作
      const result = await memorySystem.retrieveMemories({
        text: 'test query',
        context: { expandWithGraph: true },
        limit: 5
      });

      // 应该能够降级处理（不使用知识图谱）
      expect(Array.isArray(result)).toBe(true);

      // 重新启用功能
      await configManager.updateConfig({
        features: {
          knowledgeGraph: true
        }
      });

      // 验证功能恢复
      const recoveredResult = await memorySystem.retrieveMemories({
        text: 'test query',
        context: { expandWithGraph: true },
        limit: 5
      });

      expect(Array.isArray(recoveredResult)).toBe(true);
    });

    test('应该能够处理无效数据输入', async () => {
      // 测试无效记忆数据
      const invalidMemory = {
        id: '',
        type: 'invalid' as any,
        content: null as any,
        context: undefined as any,
        importance: -1,
        createdAt: new Date(),
        updatedAt: new Date(),
        metadata: {}
      };

      await expect(
        memorySystem.storeMemory(invalidMemory)
      ).rejects.toThrow();

      // 测试无效查询
      const invalidQuery = {
        text: null as any,
        context: undefined as any,
        limit: -1
      };

      await expect(
        memorySystem.retrieveMemories(invalidQuery)
      ).rejects.toThrow();
    });

    test('应该能够处理资源限制', async () => {
      // 模拟内存限制
      const configManager = memorySystem.getConfigurationManager();
      await configManager.updateConfig({
        memory: {
          maxSize: 10, // 很小的限制
          retentionDays: 1
        }
      });

      // 尝试存储超出限制的记忆
      const memories: Memory[] = [];
      for (let i = 0; i < 20; i++) {
        memories.push({
          id: `limit-test-${i}`,
          type: 'episodic',
          content: `Memory ${i} for limit testing`,
          context: { test: 'limit' },
          importance: 0.5,
          createdAt: new Date(),
          updatedAt: new Date(),
          metadata: { tags: ['limit-test'] }
        });
      }

      // 系统应该能够处理限制（可能通过清理旧记忆）
      for (const memory of memories) {
        await memorySystem.storeMemory(memory);
      }

      // 验证系统仍然正常工作
      const stats = await memorySystem.getSystemStats();
      expect(stats.memories.total).toBeLessThanOrEqual(10);
    });
  });

  describe('数据一致性和完整性', () => {
    test('应该维护记忆和知识图谱的一致性', async () => {
      const memory: Memory = {
        id: 'consistency-test-mem',
        type: 'semantic',
        content: 'Test concept for consistency',
        context: { concept: 'test-concept' },
        importance: 0.7,
        createdAt: new Date(),
        updatedAt: new Date(),
        metadata: { tags: ['consistency'] }
      };

      // 存储记忆
      await memorySystem.storeMemory(memory);

      // 创建相关知识节点
      const graphManager = memorySystem.getKnowledgeGraphManager();
      const nodeId = await graphManager.addNode({
        type: 'concept',
        label: 'Test Concept',
        properties: {
          relatedMemoryId: memory.id
        },
        metadata: {
          sourceMemory: memory.id
        }
      });

      // 验证一致性
      const retrievedMemory = await memorySystem.retrieveMemories({
        text: 'test concept',
        context: {},
        limit: 1
      });

      const retrievedNode = await graphManager.getNode(nodeId);

      expect(retrievedMemory.length).toBe(1);
      expect(retrievedMemory[0].memory.id).toBe(memory.id);
      expect(retrievedNode!.metadata.sourceMemory).toBe(memory.id);
    });

    test('应该能够验证数据完整性', async () => {
      // 添加一些测试数据
      const testData = {
        memories: [
          {
            id: 'integrity-mem-1',
            type: 'episodic' as const,
            content: 'Integrity test memory 1',
            context: { test: 'integrity' },
            importance: 0.6,
            createdAt: new Date(),
            updatedAt: new Date(),
            metadata: { tags: ['integrity'] }
          }
        ],
        rules: [
          {
            name: 'Integrity Test Rule',
            description: 'Rule for integrity testing',
            category: 'test',
            priority: 5,
            enabled: true,
            conditions: [],
            actions: [],
            metadata: { test: 'integrity' }
          }
        ]
      };

      // 存储测试数据
      for (const memory of testData.memories) {
        await memorySystem.storeMemory(memory);
      }

      const ruleManager = memorySystem.getRuleManager();
      for (const rule of testData.rules) {
        await ruleManager.addRule(rule);
      }

      // 验证数据完整性
      const integrityCheck = await memorySystem.validateDataIntegrity();
      
      expect(integrityCheck.valid).toBe(true);
      expect(integrityCheck.errors.length).toBe(0);
      expect(integrityCheck.warnings.length).toBeGreaterThanOrEqual(0);
    });
  });
});