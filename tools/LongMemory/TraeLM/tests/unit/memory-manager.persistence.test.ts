import * as path from 'path';
import * as fs from 'fs-extra';
import { KnowledgeGraph } from '../../src/services/knowledge-graph/graph';
import { MemoryManager } from '../../src/services/knowledge-graph/memory';
import { Memory, MemoryType } from '../../src/types/base';

describe('MemoryManager 持久化：saveNow/loadNow', () => {
  const TEST_DIR = path.join(process.cwd(), '.tmp_test', 'unit_persist');
  const FILE_NAME = 'unit_memories.json';
  const FILE_PATH = path.join(TEST_DIR, FILE_NAME);

  beforeAll(async () => {
    await fs.ensureDir(TEST_DIR);
    await fs.remove(FILE_PATH).catch(() => {});
  });

  afterAll(async () => {
    await fs.remove(FILE_PATH).catch(() => {});
  });

  test('保存后重启并加载，索引与图节点重建', async () => {
    const graph1 = new KnowledgeGraph();
    const mm1 = new MemoryManager(graph1, {
      enableAutoCleanup: false,
      persistence: {
        enabled: true,
        dir: TEST_DIR,
        fileName: FILE_NAME,
        autoSave: false,
        saveOnDestroy: false,
      },
    });

    const m1: Memory = {
      id: 'unit-m1',
      content: 'Persistent memory: jest unit test',
      summary: 'unit test memory',
      type: MemoryType.LONG_TERM,
      importance: 0.7,
      tags: ['unit', 'persist'],
      context: { domain: 'test', sessionId: 'u1' },
      createdAt: new Date(),
    };
    const m2: Memory = {
      id: 'unit-m2',
      content: 'Another memory will be persisted and reloaded',
      type: MemoryType.SEMANTIC,
      importance: 0.6,
      tags: ['unit', 'reload'],
      context: { domain: 'test', sessionId: 'u2' },
      createdAt: new Date(),
    };

    expect(mm1.storeMemory(m1)).toBe(true);
    expect(mm1.storeMemory(m2)).toBe(true);

    await mm1.saveNow();
    expect(await fs.pathExists(FILE_PATH)).toBe(true);

    // 关闭第一次实例
    await mm1.destroy();

    // 第二次启动并显式加载
    const graph2 = new KnowledgeGraph();
    const mm2 = new MemoryManager(graph2, {
      enableAutoCleanup: false,
      persistence: {
        enabled: true,
        dir: TEST_DIR,
        fileName: FILE_NAME,
        autoSave: false,
        saveOnDestroy: false,
      },
    });
    await mm2.loadNow();

    const loaded = mm2.getAllMemories();
    expect(loaded.length).toBeGreaterThanOrEqual(2);
    const ids = loaded.map(m => m.id);
    expect(ids).toEqual(expect.arrayContaining(['unit-m1', 'unit-m2']));

    // 日期反序列化
    const lm1 = mm2.getMemory('unit-m1')!;
    expect(lm1.createdAt instanceof Date).toBe(true);
    // 索引与图重建
    const stats = mm2.getStats();
    expect(stats.indexSize).toBeGreaterThan(0);
    expect(graph2.getNode('memory_unit-m1')).toBeDefined();
    expect(graph2.getNode('memory_unit-m2')).toBeDefined();

    await mm2.destroy();
  });
});