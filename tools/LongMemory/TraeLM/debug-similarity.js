const { MemoryManager } = require('./dist/src/services/knowledge-graph/memory');
const { KnowledgeGraphManager } = require('./dist/src/services/knowledge-graph/manager');
const { KnowledgeGraph } = require('./dist/src/services/knowledge-graph/graph');

async function testSimilarity() {
  console.log('开始测试相似性计算...');
  
  // 创建知识图谱
  const graph = new KnowledgeGraph();
  
  // 创建记忆管理器（不需要KnowledgeGraphManager）
  const memoryManager = new MemoryManager(graph);
  
  // 创建测试记忆
  const baseMemory = {
    id: 'base',
    content: 'AI技术在现代软件开发中的应用',
    type: 'semantic',
    importance: 0.8,
    tags: ['AI', '软件开发', '技术'],
    metadata: {
      category: 'technology',
      source: 'discussion'
    }
  };
  
  const sim1Memory = {
    id: 'sim1',
    content: '人工智能在软件工程中的实际运用',
    type: 'semantic',
    importance: 0.7,
    tags: ['人工智能', '软件工程', '应用'],
    metadata: {
      category: 'technology',
      source: 'article'
    }
  };
  
  // 存储记忆
  console.log('存储记忆...');
  await memoryManager.storeMemory(baseMemory);
  await memoryManager.storeMemory(sim1Memory);
  
  // 测试相似性查找
  console.log('测试getRelatedMemories...');
  const relatedMemories = await memoryManager.getRelatedMemories('base', {
    type: 'semantic',
    minScore: 0.1,
    limit: 10
  });
  
  console.log('相关记忆结果:', relatedMemories);
  
  // 测试findSimilarMemories
  console.log('测试findSimilarMemories...');
  const similarMemories = await memoryManager.findSimilarMemories(baseMemory, {
    minScore: 0.1,
    limit: 10
  });
  
  console.log('相似记忆结果:', similarMemories);
}

testSimilarity().catch(console.error);