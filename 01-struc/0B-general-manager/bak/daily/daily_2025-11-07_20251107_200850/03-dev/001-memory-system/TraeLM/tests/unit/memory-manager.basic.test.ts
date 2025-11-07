import { KnowledgeGraph } from '../../src/services/knowledge-graph/graph';
import { MemoryManager } from '../../src/services/knowledge-graph/memory';
import { Memory, MemoryType } from '../../src/types/base';

describe('MemoryManager 基础功能', () => {
  let graph: KnowledgeGraph;
  let mm: MemoryManager;

  beforeAll(() => {
    graph = new KnowledgeGraph();
    mm = new MemoryManager(graph, { enableAutoCleanup: false });
  });

  afterAll(async () => {
    await mm.destroy();
  });

  test('存储、更新、删除与查询', () => {
    const m1: Memory = {
      id: 'u1',
      content: 'Learn Jest and write unit tests for memory manager',
      type: MemoryType.SEMANTIC,
      importance: 0.6,
      tags: ['test', 'jest'],
      context: { sessionId: 's1', projectId: 'p1' },
      createdAt: new Date(),
    };

    const m2: Memory = {
      id: 'u2',
      content: 'Finish sprint tasks and update project board',
      type: MemoryType.EPISODIC,
      importance: 0.5,
      tags: ['task', 'sprint'],
      context: { sessionId: 's2', projectId: 'p1' },
      createdAt: new Date(),
    };

    const m3: Memory = {
      id: 'u3',
      content: 'Code style rules and linting guidelines',
      type: MemoryType.LONG_TERM,
      importance: 0.8,
      tags: ['style', 'lint'],
      context: { projectId: 'p2' },
      createdAt: new Date(),
    };

    expect(mm.storeMemory(m1)).toBe(true);
    expect(mm.storeMemory(m2)).toBe(true);
    expect(mm.storeMemory(m3)).toBe(true);

    // 所有记忆
    const all = mm.getAllMemories();
    expect(all.length).toBe(3);

    // 按类型查询
    const semantic = mm.getMemoriesByType(MemoryType.SEMANTIC);
    expect(semantic.map(m => m.id)).toContain('u1');

    // search: tags
    const tagSearch = mm.searchMemories({ tags: ['jest'] });
    expect(tagSearch.map(m => m.id)).toContain('u1');

    // search: context
    const ctxSearch = mm.searchMemories({ context: { sessionId: 's1' } });
    expect(ctxSearch.map(m => m.id)).toContain('u1');

    // search: text
    const textSearch = mm.searchMemories({ text: 'unit tests' });
    expect(textSearch.map(m => m.id)).toContain('u1');

    // search: keywords（由索引抽取与标签索引）
    const keywordSearch = mm.searchMemories({ keywords: ['learn', 'jest'] });
    expect(keywordSearch.map(m => m.id)).toContain('u1');

    // 更新：类型、内容、标签与上下文
    const updated = mm.updateMemory('u1', {
      type: MemoryType.LONG_TERM,
      content: m1.content + ' with more details and examples',
      tags: [...(m1.tags || []), 'unit'],
      context: { ...m1.context, taskId: 't1' },
    });
    expect(updated).toBe(true);
    const longTerm = mm.getMemoriesByType(MemoryType.LONG_TERM);
    expect(longTerm.map(m => m.id)).toContain('u1');
    const tagUnitSearch = mm.searchMemories({ tags: ['unit'] });
    expect(tagUnitSearch.map(m => m.id)).toContain('u1');

    // 删除及图节点同步移除
    const removed = mm.removeMemory('u2');
    expect(removed).toBe(true);
    const afterRemoveAll = mm.getAllMemories();
    expect(afterRemoveAll.length).toBe(2);
    // 图谱节点应已删除
    const nodeAfterRemove = graph.getNode('memory_u2');
    expect(nodeAfterRemove).toBeUndefined();

    // 统计信息
    const stats = mm.getStats();
    expect(stats.totalMemories).toBe(2);
    expect(stats.indexSize).toBeGreaterThan(0);
    expect(Object.values(stats.typeStats).reduce((a, b) => a + b, 0)).toBe(2);
  });
});