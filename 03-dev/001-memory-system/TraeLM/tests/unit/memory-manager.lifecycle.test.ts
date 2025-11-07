import { KnowledgeGraph } from '../../src/services/knowledge-graph/graph';
import { MemoryManager } from '../../src/services/knowledge-graph/memory';
import { Memory, MemoryType } from '../../src/types/base';

describe('MemoryManager 生命周期与清理逻辑', () => {
  let graph: KnowledgeGraph;
  let mm: MemoryManager;

  beforeEach(() => {
    graph = new KnowledgeGraph();
    mm = new MemoryManager(graph, { enableAutoCleanup: false });
  });

  afterEach(async () => {
    await mm.destroy();
  });

  test('过期记忆清理 cleanupExpiredMemories', () => {
    const m: Memory = {
      id: 'expire-1',
      content: 'This memory is expired',
      type: MemoryType.EPISODIC,
      importance: 0.2,
      createdAt: new Date(),
      expiresAt: new Date(Date.now() - 1000),
    };
    mm.storeMemory(m);
    expect(mm.getAllMemories().length).toBe(1);
    const removed = mm.cleanupExpiredMemories();
    expect(removed).toBe(1);
    expect(mm.getAllMemories().length).toBe(0);
  });

  test('低重要性记忆清理 cleanupLowImportanceMemories', () => {
    const m: Memory = {
      id: 'lowimp-1',
      content: 'Low importance memory',
      type: MemoryType.SEMANTIC,
      importance: 0.01,
      createdAt: new Date(),
    };
    mm.storeMemory(m);
    const removed = mm.cleanupLowImportanceMemories(0.05, 10);
    expect(removed).toBe(1);
    expect(mm.getAllMemories().length).toBe(0);
  });

  test('记忆合并 mergeMemories 会删除旧记忆并生成新记忆', () => {
    const m1: Memory = {
      id: 'merge-1',
      content: 'The weather is sunny today',
      type: MemoryType.SEMANTIC,
      importance: 0.4,
      tags: ['weather'],
      createdAt: new Date(),
    };
    const m2: Memory = {
      id: 'merge-2',
      content: 'Today is a good day with sunshine',
      type: MemoryType.SEMANTIC,
      importance: 0.5,
      tags: ['weather'],
      createdAt: new Date(),
    };

    mm.storeMemory(m1);
    mm.storeMemory(m2);

    let mergedEvent = false;
    mm.on('memoriesMerged', () => {
      mergedEvent = true;
    });

    const mergedId = mm.mergeMemories('merge-1', 'merge-2', {
      summary: 'Merged: sunny day',
      importance: 0.6,
    });
    expect(mergedId).toMatch(/^merged_/);
    expect(mm.getMemory('merge-1')).toBeUndefined();
    expect(mm.getMemory('merge-2')).toBeUndefined();
    const merged = mm.getMemory(mergedId)!;
    expect(merged).toBeDefined();
    expect(merged.summary).toContain('Merged');
    expect(mergedEvent).toBe(true);
  });

  test('相似记忆查找 findSimilarMemories 与相关记忆 getRelatedMemories', () => {
    const base: Memory = {
      id: 'base-1',
      content: 'AI assistants help with coding and testing',
      type: MemoryType.SEMANTIC,
      importance: 0.6,
      createdAt: new Date(),
    };
    const sim1: Memory = {
      id: 'sim-1',
      content: 'Coding help from AI tools is useful',
      type: MemoryType.SEMANTIC,
      importance: 0.5,
      createdAt: new Date(),
    };
    const sim2: Memory = {
      id: 'sim-2',
      content: 'Testing pipelines can be improved by automation',
      type: MemoryType.SEMANTIC,
      importance: 0.4,
      createdAt: new Date(),
    };

    mm.storeMemory(base);
    mm.storeMemory(sim1);
    mm.storeMemory(sim2);

    const similar = mm.findSimilarMemories('coding help AI', 0.1);
    expect(similar.length).toBeGreaterThanOrEqual(1);
    expect(similar.map(m => m.id)).toEqual(expect.arrayContaining(['sim-1']));

    const related = mm.getRelatedMemories('base-1', { type: MemoryType.SEMANTIC }, 0.1);
    expect(related.length).toBeGreaterThanOrEqual(1);
    expect(related.map(m => m.id)).toEqual(expect.arrayContaining(['sim-1']));
  });
});