import { KnowledgeGraph } from '../../src/services/knowledge-graph/graph';
import { KnowledgeNode, KnowledgeEdge } from '../../src/types/base';

describe('KnowledgeGraph 节点与边管理、搜索', () => {
  let graph: KnowledgeGraph;

  beforeEach(() => {
    graph = new KnowledgeGraph();
  });

  test('add/update/remove 节点与类型索引', () => {
    const node: KnowledgeNode = {
      id: 'n1',
      type: 'concept',
      label: 'AI',
      content: 'Artificial Intelligence',
      createdAt: new Date(),
      updatedAt: new Date(),
      tags: ['ai', 'technology'],
      properties: { level: 'base' },
    };
    expect(graph.addNode(node)).toBe(true);
    expect(graph.getNode('n1')).toBeDefined();
    expect(graph.getNodesByType('concept').map(n => n.id)).toContain('n1');

    // 更新节点类型与属性
    const ok = graph.updateNode('n1', { type: 'topic', properties: { level: 'advanced' }, label: 'AI-Topic' });
    expect(ok).toBe(true);
    expect(graph.getNodesByType('concept').map(n => n.id)).not.toContain('n1');
    expect(graph.getNodesByType('topic').map(n => n.id)).toContain('n1');
    const n1 = graph.getNode('n1')!;
    expect(n1.properties.level).toBe('advanced');

    // 删除节点
    expect(graph.removeNode('n1')).toBe(true);
    expect(graph.getNode('n1')).toBeUndefined();
  });

  test('边的 add/update/remove 与邻接表维护', () => {
    const a: KnowledgeNode = { id: 'a', type: 'entity', label: 'A', content: 'A', createdAt: new Date(), updatedAt: new Date(), properties: {} };
    const b: KnowledgeNode = { id: 'b', type: 'entity', label: 'B', content: 'B', createdAt: new Date(), updatedAt: new Date(), properties: {} };
    graph.addNode(a);
    graph.addNode(b);

    const edge: KnowledgeEdge = {
      id: 'e1',
      type: 'relates_to',
      sourceId: 'a',
      targetId: 'b',
      weight: 0.8,
      properties: { note: 'A->B' },
      createdAt: new Date(),
      updatedAt: new Date(),
    };

    expect(graph.addEdge(edge)).toBe(true);
    expect(graph.getAllEdges().map(e => e.id)).toContain('e1');
    expect(graph.getEdgesByType('relates_to').map(e => e.id)).toContain('e1');

    // 更新边类型与权重
    const ok = graph.updateEdge('e1', { type: 'follows', weight: 0.9 });
    expect(ok).toBe(true);
    expect(graph.getEdgesByType('relates_to').map(e => e?.id)).not.toContain('e1');
    expect(graph.getEdgesByType('follows').map(e => e.id)).toContain('e1');

    // 删除边
    expect(graph.removeEdge('e1')).toBe(true);
    expect(graph.getAllEdges().map(e => e.id)).not.toContain('e1');
  });

  test('searchNodes 支持类型、标签、属性、文本与时间范围、排序与限制', () => {
    const now = Date.now();
    const n1: KnowledgeNode = {
      id: 's1', type: 'topic', label: 'AI Basics', content: 'Intro', createdAt: new Date(now - 10000), updatedAt: new Date(), tags: ['ai'], properties: { level: 'basic' }
    };
    const n2: KnowledgeNode = {
      id: 's2', type: 'topic', label: 'AI Advanced', content: 'Deep', createdAt: new Date(now - 5000), updatedAt: new Date(), tags: ['ai','deep'], properties: { level: 'advanced' }
    };
    const n3: KnowledgeNode = {
      id: 's3', type: 'concept', label: 'ML', content: 'Machine Learning', createdAt: new Date(now - 2000), updatedAt: new Date(), tags: ['ml'], properties: { level: 'basic' }
    };
    graph.addNode(n1);
    graph.addNode(n2);
    graph.addNode(n3);

    let results = graph.searchNodes({ type: 'topic', tags: ['ai'], properties: { level: 'advanced' } });
    expect(results.map(n => n.id)).toEqual(['s2']);

    // 文本搜索与时间过滤
    results = graph.searchNodes({ text: 'ai', createdAfter: new Date(now - 8000), sortBy: 'createdAt', sortOrder: 'asc' });
    expect(results.map(n => n.id)).toEqual(['s2']);

    // 限制数量
    results = graph.searchNodes({ type: 'topic', limit: 1, sortBy: 'label', sortOrder: 'desc' });
    expect(results.length).toBe(1);
  });
});