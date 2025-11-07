/**
 * 长期记忆持久化与检索集成测试
 *
 * 验证 MemoryManager 的持久化保存/加载、索引构建，以及通过 MemoryRetriever 的检索流程。
 */

import * as path from 'path';
import * as fs from 'fs-extra';

import { KnowledgeGraph } from '../../src/services/knowledge-graph/graph';
import { MemoryManager } from '../../src/services/knowledge-graph/memory';
import { MemoryRetriever } from '../../src/services/memory-retrieval/retriever';
import { MemoryType, type Memory, type RetrievalQuery } from '../../src/types/base';

describe('长期记忆持久化与检索（MemoryManager + MemoryRetriever）', () => {
  const TMP_ROOT = path.join(process.cwd(), '.tmp_test');
  const TEST_DIR = path.join(TMP_ROOT, `memory_persistence_${Date.now()}`);
  const FILE_NAME = 'memories.json';

  beforeAll(async () => {
    await fs.ensureDir(TEST_DIR);
  });

  afterAll(async () => {
    // 清理测试目录
    try {
      await fs.remove(TEST_DIR);
    } catch {
      // ignore
    }
  });

  test('保存到文件后，重建并加载能恢复记忆与索引；检索流程正常', async () => {
    // 1) 初始化第一阶段的图谱与内存管理器（持久化开启，手动保存）
    const graph1 = new KnowledgeGraph();
    const mm1 = new MemoryManager(graph1, {
      persistence: {
        enabled: true,
        dir: TEST_DIR,
        fileName: FILE_NAME,
        autoSave: false,
        saveOnDestroy: false
      }
    });

    const m1: Memory = {
      id: 'm1',
      type: MemoryType.SEMANTIC,
      content: 'Apollo 11 landed on the Moon in 1969. Neil Armstrong was the first person to walk on the Moon.',
      importance: 0.7,
      tags: ['apollo', 'moon', 'history'],
      context: { userId: 'test-user', sessionId: 'sess-1', domain: 'space', task: 'research' },
      createdAt: new Date()
    };

    const m2: Memory = {
      id: 'm2',
      type: MemoryType.EPISODIC,
      content: 'User wrote a note about lunar geology and Mare Tranquillitatis.',
      importance: 0.5,
      tags: ['moon', 'note'],
      context: { userId: 'test-user', sessionId: 'sess-1', domain: 'space', task: 'note-taking' },
      createdAt: new Date()
    };

    const m3: Memory = {
      id: 'm3',
      type: MemoryType.PROCEDURAL,
      content: 'Steps to analyze lunar samples: prepare specimens, run spectroscopy, document results.',
      importance: 0.6,
      tags: ['procedure', 'lunar', 'samples'],
      context: { userId: 'another-user', sessionId: 'sess-2', domain: 'lab', task: 'analysis' },
      createdAt: new Date()
    };

    expect(mm1.storeMemory(m1)).toBe(true);
    expect(mm1.storeMemory(m2)).toBe(true);
    expect(mm1.storeMemory(m3)).toBe(true);

    // 基础统计与图节点验证
    const stats1 = mm1.getStats();
    expect(stats1.totalMemories).toBe(3);
    expect(stats1.indexSize).toBeGreaterThan(0); // 关键词索引应已构建
    expect(graph1.getNode('memory_m1')).toBeDefined();
    expect(graph1.getNode('memory_m2')).toBeDefined();
    expect(graph1.getNode('memory_m3')).toBeDefined();

    // 保存到持久化文件
    await mm1.saveNow();
    const persistedPath = path.join(TEST_DIR, FILE_NAME);
    const exists = await fs.pathExists(persistedPath);
    expect(exists).toBe(true);
    const persistedContent = await fs.readFile(persistedPath, 'utf-8');
    expect(persistedContent.length).toBeGreaterThan(10);

    // 2) 重建第二阶段的图谱与内存管理器，并从文件加载
    const graph2 = new KnowledgeGraph();
    const mm2 = new MemoryManager(graph2, {
      persistence: {
        enabled: true,
        dir: TEST_DIR,
        fileName: FILE_NAME,
        autoSave: false,
        saveOnDestroy: false
      }
    });

    // 显式加载以保证同步
    await mm2.loadNow();

    const all2 = mm2.getAllMemories();
    expect(all2.length).toBe(3);
    const ids2 = all2.map(m => m.id).sort();
    expect(ids2).toEqual(['m1', 'm2', 'm3']);

    // 索引与图节点重建验证
    const stats2 = mm2.getStats();
    expect(stats2.totalMemories).toBe(3);
    expect(stats2.indexSize).toBeGreaterThan(0);
    expect(graph2.getNode('memory_m1')).toBeDefined();
    expect(graph2.getNode('memory_m2')).toBeDefined();
    expect(graph2.getNode('memory_m3')).toBeDefined();

    // 3) 使用 MemoryManager 的搜索接口验证上下文、标签、文本与关键词过滤
    const byContext = mm2.searchMemories({ context: { userId: 'test-user' } });
    expect(byContext.map(m => m.id).sort()).toEqual(['m1', 'm2']);

    const byTags = mm2.searchMemories({ tags: ['apollo'] });
    expect(byTags.map(m => m.id)).toContain('m1');

    const byText = mm2.searchMemories({ text: 'lunar geology' });
    expect(byText.map(m => m.id)).toContain('m2');

    const byKeywords = mm2.searchMemories({ keywords: ['spectroscopy', 'samples'] });
    expect(byKeywords.map(m => m.id)).toContain('m3');

    // 4) 使用 MemoryRetriever 验证检索流程与策略合并
    const retriever = new MemoryRetriever(mm2, graph2);

    const query: RetrievalQuery = {
      text: 'Apollo mission moon landing',
      type: MemoryType.SEMANTIC,
      context: { userId: 'test-user' },
      tags: ['moon'],
      limit: 5,
      includeRelated: false
    };

    const result = await retriever.retrieve(query);
    expect(result.memories.length).toBeGreaterThan(0);
    const resultIds = result.memories.map(m => m.id);
    expect(resultIds).toContain('m1'); // 与文本与标签最相关的应该包含 m1
    expect(result.totalResults).toBeGreaterThan(0);
    expect(result.confidence).toBeGreaterThan(0);

    // 验证缓存与统计
    const cached = await retriever.retrieve(query);
    expect(cached.memories.map(m => m.id)).toEqual(resultIds);
    const rStats = retriever.getStats();
    expect(rStats.strategiesCount).toBeGreaterThan(0);

    // 清理资源，避免 Jest 退出延迟（定时器与事件监听）
    retriever.destroy();
    mm1.destroy();
    mm2.destroy();
  });
});