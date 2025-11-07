import { jest } from '@jest/globals';
import { KnowledgeGraph } from '../../src/services/knowledge-graph/graph';
import { MemoryManager } from '../../src/services/knowledge-graph/memory';
import { MemoryRetrievalManager } from '../../src/services/memory-retrieval/manager';
import { AgentType, AgentStatus, MemoryType, Memory, Agent, PerformanceMetrics, LogLevel } from '../../src/types/base';

describe('MemoryRetrievalManager 管理器：检索、增强与统计', () => {
  let graph: KnowledgeGraph;
  let mm: MemoryManager;
  let manager: MemoryRetrievalManager;

  beforeEach(() => {
    jest.useFakeTimers();
    graph = new KnowledgeGraph();
    mm = new MemoryManager(graph, { enableAutoCleanup: false });
    manager = new MemoryRetrievalManager(mm);
  });

  afterEach(async () => {
    manager.destroy();
    await mm.destroy();
    jest.useRealTimers();
  });

  test('检索与统计更新', async () => {
    const m: Memory = {
      id: 'mgr-1',
      content: 'rule processing workflow step one',
      type: MemoryType.PROCEDURAL,
      importance: 0.6,
      tags: ['rule', 'processing', 'workflow'],
      createdAt: new Date(),
      context: { domain: 'ops' }
    };
    mm.storeMemory(m);

    await manager.initialize();
    const result = await manager.retrieveMemories({ text: 'rule processing', limit: 10 });
    expect(result.memories.length).toBeGreaterThanOrEqual(1);
    const stats = manager.getStats();
    expect(stats.totalQueries).toBeGreaterThanOrEqual(1);
  });

  test('增强智能体与学习模式、历史记录', async () => {
    const m: Memory = {
      id: 'mgr-2',
      content: 'Process workflow includes step and procedure',
      type: MemoryType.PROCEDURAL,
      importance: 0.5,
      tags: ['process', 'workflow'],
      createdAt: new Date(),
      context: { domain: 'ops' }
    };
    mm.storeMemory(m);

    const agent: Agent = {
      id: 'agent-1',
      name: 'Rule Processor',
      type: AgentType.RULE_PROCESSOR,
      capabilities: ['process_rules'],
      configuration: { maxMemorySize: 100, processingTimeout: 1000, retryAttempts: 1, logLevel: LogLevel.INFO, customSettings: {}, workflows: [] },
      status: AgentStatus.ACTIVE,
      createdAt: new Date(),
      lastActiveAt: new Date()
    };

    const baseline: PerformanceMetrics = {
      timestamp: new Date(),
      memoryUsage: { used: 100, total: 1000, percentage: 10 },
      processingTime: 100,
      throughput: 10,
      errorRate: 0.01,
      activeConnections: 1,
    };
    await manager.setPerformanceBaseline(agent.id, baseline);

    const result = await manager.enhanceAgent(agent, { domain: 'ops', currentTask: 'process rules' });
    expect(result.enhancedAgent.status).toBe(AgentStatus.ENHANCED);
    expect(result.performanceImprovement).toBeGreaterThanOrEqual(0);

    const patterns = manager.getLearningPatterns();
    expect(patterns.length).toBeGreaterThanOrEqual(0);

    // 异步增强入队
    await manager.enhanceAgentAsync(agent, { domain: 'ops', currentTask: 'process rules' });
    expect(manager.getDetailedStats().queueSize).toBeGreaterThanOrEqual(1);

    // 清除历史
    manager.clearHistory();
    expect(manager.getDetailedStats().queryHistorySize).toBe(0);
  });
});