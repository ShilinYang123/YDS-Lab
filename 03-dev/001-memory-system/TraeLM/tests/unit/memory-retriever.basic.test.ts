import { jest } from '@jest/globals';
import { KnowledgeGraph } from '../../src/services/knowledge-graph/graph';
import { MemoryManager } from '../../src/services/knowledge-graph/memory';
import { MemoryRetriever, RetrievalStrategy } from '../../src/services/memory-retrieval/retriever';
import { MemoryType, Memory, KnowledgeNode, RetrievalQuery } from '../../src/types/base';

describe('MemoryRetriever 基础检索与缓存', () => {
  let graph: KnowledgeGraph;
  let mm: MemoryManager;
  let retriever: MemoryRetriever;

  beforeEach(() => {
    jest.useFakeTimers();
    graph = new KnowledgeGraph();
    mm = new MemoryManager(graph, { enableAutoCleanup: false });
    retriever = new MemoryRetriever(mm, graph);
  });

  afterEach(async () => {
    retriever.destroy();
    await mm.destroy();
    jest.useRealTimers();
  });

  test('检索返回记忆与相关节点，并计算置信度', async () => {
    const node: KnowledgeNode = {
      id: 'topic_ai',
      type: 'topic',
      label: 'AI Topic',
      content: 'AI topic node',
      properties: {},
      createdAt: new Date(),
      updatedAt: new Date(),
      tags: ['ai'],
    };
    graph.addNode(node);

    const m1: Memory = {
      id: 'mr-1',
      content: 'AI assistants can help with coding tasks',
      type: MemoryType.SEMANTIC,
      importance: 0.7,
      createdAt: new Date(),
      context: { domain: 'dev', sessionId: 's1' },
      knowledgeLinks: ['topic_ai'],
    };
    const m2: Memory = {
      id: 'mr-2',
      content: 'Using automation improves testing pipelines',
      type: MemoryType.SEMANTIC,
      importance: 0.6,
      createdAt: new Date(),
      context: { domain: 'dev', sessionId: 's2' },
    };
    mm.storeMemory(m1);
    mm.storeMemory(m2);

    const query: RetrievalQuery = {
      type: MemoryType.SEMANTIC,
      text: 'AI coding help',
      context: { domain: 'dev' },
      includeRelated: true,
      limit: 5,
    };

    const result = await retriever.retrieve(query);
    expect(result.memories.length).toBeGreaterThanOrEqual(1);
    expect(result.relatedNodes.map(n => n.id)).toEqual(expect.arrayContaining(['topic_ai']));
    expect(result.totalResults).toBeGreaterThanOrEqual(2);
    expect(result.confidence).toBeGreaterThan(0);
  });

  test('缓存命中 cacheHit 事件与清理', async () => {
    const m: Memory = {
      id: 'mr-cache',
      content: 'Cache works with same query',
      type: MemoryType.SEMANTIC,
      importance: 0.5,
      createdAt: new Date(),
      context: { domain: 'qa' },
    };
    mm.storeMemory(m);

    const query: RetrievalQuery = { text: 'Cache query', type: MemoryType.SEMANTIC, limit: 3 };

    let cacheHit = false;
    retriever.on('cacheHit', () => { cacheHit = true; });

    await retriever.retrieve(query);
    const result2 = await retriever.retrieve(query);
    expect(cacheHit).toBe(true);
    expect(result2.memories.length).toBeGreaterThanOrEqual(0);

    let cacheCleared = false;
    retriever.on('cacheCleared', () => { cacheCleared = true; });
    retriever.clearCache();
    expect(cacheCleared).toBe(true);
    expect(retriever.getStats().cacheSize).toBe(0);
  });

  test('自定义策略 add/removeStrategy 生效', async () => {
    const m1: Memory = {
      id: 'mr-strat-1',
      content: 'strategy memory one',
      type: MemoryType.SEMANTIC,
      importance: 0.3,
      createdAt: new Date(),
      context: { domain: 'custom' },
    };
    const m2: Memory = {
      id: 'mr-strat-2',
      content: 'strategy memory two',
      type: MemoryType.SEMANTIC,
      importance: 0.9,
      createdAt: new Date(),
      context: { domain: 'custom' },
    };
    mm.storeMemory(m1);
    mm.storeMemory(m2);

    const strat: RetrievalStrategy = {
      name: 'alwaysTop',
      weight: 1.0,
      execute: async (_q, memories) => {
        // 将 id 为 mr-strat-1 的记忆放在最前
        const found = memories.find(m => m.id === 'mr-strat-1');
        return found ? [found, ...memories.filter(m => m.id !== 'mr-strat-1')] : memories;
      }
    };

    retriever.addStrategy(strat);
    expect(retriever.getStats().strategies).toEqual(expect.arrayContaining(['textSimilarity', 'contextMatch', 'temporalRelevance', 'importance', 'alwaysTop']));

    const result = await retriever.retrieve({ type: MemoryType.SEMANTIC, limit: 5 });
    expect(result.memories).toHaveLength(2);
    expect(result.memories[0]!.id).toBe('mr-strat-1');

    const removed = retriever.removeStrategy('alwaysTop');
    expect(removed).toBe(true);
    expect(retriever.getStats().strategies).not.toContain('alwaysTop');
  });
});