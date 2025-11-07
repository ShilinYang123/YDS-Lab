const { KnowledgeGraph } = require('./dist/src/services/knowledge-graph/graph');
const { MemoryManager } = require('./dist/src/services/knowledge-graph/memory');

async function testSimilarityDetailed() {
  console.log('开始详细测试相似性计算...');
  
  // 创建知识图谱和记忆管理器
  const knowledgeGraph = new KnowledgeGraph();
  const memoryManager = new MemoryManager(knowledgeGraph);

  const baseMemory = {
    id: 'base',
    content: '人工智能是一个快速发展的技术领域，包括机器学习、深度学习等多个分支。',
    type: 'semantic',
    importance: 0.8,
    tags: ['人工智能', '技术', '机器学习'],
    metadata: {
      category: 'technology',
      source: 'article'
    }
  };

  const sim1Memory = {
    id: 'sim1',
    content: '机器学习是人工智能的一个重要分支，通过算法让计算机从数据中学习。',
    type: 'semantic',
    importance: 0.7,
    tags: ['人工智能', '机器学习', '算法'],
    metadata: {
      category: 'technology',
      source: 'article'
    }
  };
  
  // 存储记忆
  console.log('存储记忆...');
  const stored1 = memoryManager.storeMemory(baseMemory);
  const stored2 = memoryManager.storeMemory(sim1Memory);
  console.log('存储结果:', { stored1, stored2 });
  
  // 检查记忆是否存储成功
  const allMemories = memoryManager.getAllMemories();
  console.log('所有记忆数量:', allMemories.length);
  console.log('记忆ID列表:', allMemories.map(m => m.id));
  
  // 手动测试相似性计算
  console.log('\n手动测试相似性计算...');
  const memory1 = memoryManager.getMemory('base');
  const memory2 = memoryManager.getMemory('sim1');
  
  if (memory1 && memory2) {
    console.log('Memory1:', memory1.content);
    console.log('Memory2:', memory2.content);
    
    // 使用反射访问私有方法进行测试
    const similarity = memoryManager.calculateSimilarity ? 
      memoryManager.calculateSimilarity(memory1, memory2) : 'Method not accessible';
    console.log('相似度分数:', similarity);
  } else {
    console.log('无法获取记忆:', { memory1: !!memory1, memory2: !!memory2 });
  }
  
  // 测试getRelatedMemories
  console.log('\n测试getRelatedMemories...');
  const relatedMemories = memoryManager.getRelatedMemories('base', {
    type: 'semantic',
    minScore: 0.1,
    limit: 10
  });
  console.log('相关记忆结果:', relatedMemories.length);
  relatedMemories.forEach((mem, idx) => {
    console.log(`${idx + 1}. ID: ${mem.id}, Content: ${mem.content.substring(0, 50)}...`);
  });
  
  // 测试findSimilarMemories
  console.log('\n测试findSimilarMemories...');
  const query = '人工智能技术';
  console.log('查询:', query);
  
  const similarMemories = memoryManager.findSimilarMemories(query, 0.1);
  console.log('相似记忆结果:', similarMemories.length);
  similarMemories.forEach((mem, idx) => {
    console.log(`${idx + 1}. ID: ${mem.id}, Content: ${mem.content.substring(0, 50)}...`);
  });
  
  // 手动测试文本相似度计算
  console.log('\n手动测试文本相似度...');
  const testContent1 = '人工智能是一个快速发展的技术领域，包括机器学习、深度学习等多个分支。';
  const testContent2 = '机器学习是人工智能的一个重要分支，通过算法让计算机从数据中学习。';
  
  // 模拟extractKeywords方法
  function extractKeywords(text) {
    // 处理中文和英文混合文本
    const processed = text
      .toLowerCase()
      // 保留中文字符、英文字母、数字和空格
      .replace(/[^\u4e00-\u9fa5a-zA-Z0-9\s]/g, ' ')
      // 在中文字符之间添加空格以便分词
      .replace(/[\u4e00-\u9fa5]/g, ' $& ')
      // 清理多余空格
      .replace(/\s+/g, ' ')
      .trim();
    
    return processed
      .split(/\s+/)
      .filter(word => word.length > 0 && word.trim() !== '') // 过滤空字符串
      .slice(0, 50); // 限制关键词数量
  }
  
  // 模拟computeTextSimilarity方法
  function computeTextSimilarity(query, content) {
    const qWords = extractKeywords(query);
    const cWords = extractKeywords(content);
    const setQ = new Set(qWords);
    const setC = new Set(cWords);
    const intersection = Array.from(setQ).filter(w => setC.has(w)).length;
    const union = new Set([...Array.from(setQ), ...Array.from(setC)]).size || 1;
    return intersection / union;
  }
  
  const textSim1 = computeTextSimilarity(query, testContent1);
  const textSim2 = computeTextSimilarity(query, testContent2);
  console.log(`查询 "${query}" 与内容1的相似度:`, textSim1);
  console.log(`查询 "${query}" 与内容2的相似度:`, textSim2);
  
  console.log('\n关键词提取测试:');
  console.log('查询关键词:', extractKeywords(query));
  console.log('内容1关键词:', extractKeywords(testContent1));
  console.log('内容2关键词:', extractKeywords(testContent2));
}

testSimilarityDetailed().catch(console.error);