const { 
  LongTermMemorySystem, 
  longTermMemorySystem, 
  VERSION, 
  PROJECT_NAME 
} = require('../dist/src/index');

/**
 * TraeLM 长期记忆系统使用示例
 */
async function main() {
  console.log(`🚀 启动 ${PROJECT_NAME} v${VERSION}`);
  console.log('=' .repeat(50));
  
  try {
    // 初始化长期记忆系统
    console.log('📋 正在初始化长期记忆系统...');
    await longTermMemorySystem.initialize();
    console.log('✅ 长期记忆系统初始化成功！');
    
    // 存储一些示例记忆
    console.log('\n💾 存储示例记忆...');
    
    const memory1 = {
      type: 'knowledge',
      title: 'AI基础知识',
      content: '人工智能是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统',
      tags: ['AI', '基础知识', '机器学习'],
      metadata: { source: '学术论文', relevance: 0.9 },
      priority: 'high'
    };
    
    const memory2 = {
      type: 'experience',
      title: '项目开发经验',
      content: '在开发TraeLM系统时，我们采用了模块化架构和TypeScript来提高代码质量和可维护性',
      tags: ['项目', '开发', 'TraeLM'],
      metadata: { project: 'TraeLM', phase: 'development' },
      priority: 'medium'
    };
    
    const memory3 = {
      type: 'concept',
      title: '知识图谱概念',
      content: '知识图谱是一种结构化的知识表示方法，通过节点和边来表示实体及其关系',
      tags: ['知识图谱', '数据结构', 'AI'],
      metadata: { field: '知识工程', complexity: 'medium' },
      priority: 'high'
    };
    
    // 存储记忆
    const id1 = await longTermMemorySystem.storeMemory(memory1);
    const id2 = await longTermMemorySystem.storeMemory(memory2);
    const id3 = await longTermMemorySystem.storeMemory(memory3);
    
    console.log(`✅ 已存储记忆 - ID: ${id1}, ${id2}, ${id3}`);
    
    // 检索记忆
    console.log('\n🔍 检索相关记忆...');
    
    const retrievalResult = await longTermMemorySystem.retrieveMemories({
      text: 'AI人工智能',
      tags: ['AI'],
      limit: 10,
      sortBy: 'relevance',
      includeContent: true
    });
    
    console.log(`✅ 找到 ${retrievalResult.memories.length} 条相关记忆:`);
    retrievalResult.memories.forEach((memory, index) => {
      console.log(`  ${index + 1}. [${memory.title}] (相似度: ${memory.relevanceScore.toFixed(3)})`);
      console.log(`     ${memory.content.substring(0, 100)}...`);
      console.log(`     标签: ${memory.tags.join(', ')}`);
      console.log('');
    });
    
    // 获取系统统计信息
    console.log('\n📊 系统统计信息:');
    const stats = longTermMemorySystem.getSystemStats();
    console.log(`规则系统: ${JSON.stringify(stats.rules, null, 2)}`);
    console.log(`知识图谱: ${JSON.stringify(stats.knowledge, null, 2)}`);
    console.log(`记忆系统: ${JSON.stringify(stats.memory, null, 2)}`);
    console.log(`性能报告: ${JSON.stringify(stats.performance, null, 2)}`);
    
    console.log('\n🎉 TraeLM长期记忆系统运行成功！');
    console.log('ℹ️  这是一个库模块，通常作为其他应用的一部分集成使用');
    console.log('ℹ️  按 Ctrl+C 退出程序');
    
    // 保持程序运行以便用户测试
    process.on('SIGINT', async () => {
      console.log('\n\n🛑 正在关闭系统...');
      await longTermMemorySystem.destroy();
      console.log('✅ 系统已安全关闭');
      process.exit(0);
    });
    
    // 等待用户中断
    console.log('⏳ 程序正在运行，按 Ctrl+C 停止...');
    setInterval(() => {}, 1000);
    
  } catch (error) {
    console.error('❌ 启动失败:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

// 运行示例
if (require.main === module) {
  main().catch(console.error);
}

module.exports = { main };