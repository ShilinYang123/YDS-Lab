#!/usr/bin/env node

/**
 * 测试长效记忆系统记录助手操作的功能
 */

const { LongTermMemorySystem } = require('./memory-system/dist/src');

async function testMemoryRecording() {
  console.log('🧠 测试长效记忆系统记录功能...');
  
  const memorySystem = new LongTermMemorySystem({
    dataPath: './memory-system/data',
    logPath: './memory-system/logs'
  });

  try {
    await memorySystem.initialize();
    console.log('✓ 记忆系统初始化成功');

    // 记录助手的操作历史
    const operationMemory = {
      content: `助手操作记录 - ${new Date().toISOString()}:
1. 助手错误地重新下载了Shimmy，覆盖了用户原有的可用文件
2. 下载过程未完成，导致shimmy.exe文件被占用无法运行
3. 助手重新下载了完整的shimmy_new.exe文件
4. 成功替换了损坏的shimmy.exe文件
5. 验证Shimmy版本1.7.4正常工作
6. 反思了必须先调查现状、听取用户意见的重要性`,
      type: 'episodic',
      metadata: {
        source: 'assistant-operations',
        importance: 'high',
        tags: ['shimmy', 'repair', 'lesson-learned', 'system-investigation'],
        project: 'trae-ide-integration',
        timestamp: new Date().toISOString(),
        operation_type: 'system_repair',
        lessons: [
          '必须先调查现状再执行操作',
          '听取用户意见避免重复操作',
          '不要盲目覆盖现有文件'
        ]
      }
    };

    const memoryId = await memorySystem.storeMemory(operationMemory);
    console.log(`✓ 操作记忆已存储，ID: ${memoryId}`);

    // 检索刚存储的记忆
    const retrievedMemories = await memorySystem.retrieveMemories('助手操作 Shimmy 修复', {
      limit: 5,
      minConfidence: 0.1
    });

    console.log(`✓ 检索结果:`, retrievedMemories);
    if (retrievedMemories && retrievedMemories.memories && Array.isArray(retrievedMemories.memories)) {
      console.log(`✓ 检索到 ${retrievedMemories.memories.length} 条相关记忆:`);
      retrievedMemories.memories.forEach((memory, index) => {
        console.log(`  ${index + 1}. [置信度: ${retrievedMemories.confidence.toFixed(2)}] ${memory.content.substring(0, 100)}...`);
      });
    } else {
      console.log(`✓ 检索结果格式:`, typeof retrievedMemories);
    }

    // 获取系统统计 - 使用正确的方法名
    try {
      const stats = await memorySystem.getStatistics();
      console.log(`✓ 系统统计: 记忆数量 ${stats.memoryCount || 'N/A'}, 规则数量 ${stats.ruleCount || 'N/A'}`);
    } catch (error) {
      console.log(`⚠ 统计功能暂不可用: ${error.message}`);
    }

    await memorySystem.destroy();
    console.log('✓ 记忆系统已安全关闭');

  } catch (error) {
    console.error('❌ 测试失败:', error.message);
    if (memorySystem) {
      await memorySystem.destroy();
    }
    process.exit(1);
  }
}

if (require.main === module) {
  testMemoryRecording().catch(console.error);
}

module.exports = testMemoryRecording;