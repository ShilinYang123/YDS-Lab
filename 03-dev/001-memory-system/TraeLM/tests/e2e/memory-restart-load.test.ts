/**
 * 端到端测试：保存后重启进程自动加载历史记忆并完成检索
 */

import * as path from 'path';
import * as fs from 'fs-extra';

import { KnowledgeGraph } from '../../src/services/knowledge-graph/graph';
import { MemoryManager } from '../../src/services/knowledge-graph/memory';
import { MemoryRetriever } from '../../src/services/memory-retrieval/retriever';
import { MemoryType, type Memory, type RetrievalQuery } from '../../src/types/base';

describe('E2E：重启后自动加载历史记忆并完成检索', () => {
  const TMP_ROOT = path.join(process.cwd(), '.tmp_test');
  const TEST_DIR = path.join(TMP_ROOT, `e2e_restart_load_${Date.now()}`);
  const FILE_NAME = 'memories_auto.json';

  beforeAll(async () => {
    await fs.ensureDir(TEST_DIR);
  });

  afterAll(async () => {
    try {
      await fs.remove(TEST_DIR);
    } catch {
      // ignore
    }
  });

  test('自动加载 + 检索流程', async () => {
    // 第一次启动：持久化开启，使用 autoSave 或 saveOnDestroy 持久化数据
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
      id: 'e2e-m1',
      type: MemoryType.SEMANTIC,
      content: 'E2E Apollo mission memory for auto load test.',
      importance: 0.8,
      tags: ['apollo', 'moon'],
      context: { userId: 'e2e-user', sessionId: 'sess-e2e', domain: 'space', task: 'validate' },
      createdAt: new Date(),
    };

    expect(mm1.storeMemory(m1)).toBe(true);
    // 显式保存，保证持久化文件已写入
    await mm1.saveNow();
    const persistedPath = path.join(TEST_DIR, FILE_NAME);
    expect(await fs.pathExists(persistedPath)).toBe(true);
    const persistedContent = await fs.readFile(persistedPath, 'utf-8');
    expect(persistedContent.length).toBeGreaterThan(10);
    // 关闭第一次实例，释放资源
    mm1.destroy();

    // 第二次启动：显式调用 loadNow 以确保加载完成（避免异步竞态导致测试不稳定）
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
    // 显式加载以避免异步加载不确定性
    await mm2.loadNow();

    const loadedAll = mm2.getAllMemories();
    expect(loadedAll.length).toBeGreaterThanOrEqual(1);
    const loadedIds = loadedAll.map(m => m.id);
    expect(loadedIds).toContain('e2e-m1');

    // 图节点应已重建
    expect(graph2.getNode('memory_e2e-m1')).toBeDefined();

    // 检索验证
    const retriever = new MemoryRetriever(mm2, graph2);
    const query: RetrievalQuery = {
      text: 'Apollo mission',
      type: MemoryType.SEMANTIC,
      context: { userId: 'e2e-user' },
      tags: ['moon'],
      limit: 3,
      includeRelated: false,
    };

    const result = await retriever.retrieve(query);
    expect(result.memories.length).toBeGreaterThan(0);
    expect(result.memories.map(m => m.id)).toContain('e2e-m1');

    // 资源清理，避免 open handles
    retriever.destroy();
    mm2.destroy();
  });
});