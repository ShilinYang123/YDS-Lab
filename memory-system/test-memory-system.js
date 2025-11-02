#!/usr/bin/env node

/**
 * YDS-Lab 长记忆系统功能测试脚本
 */

const { LongTermMemorySystem } = require('./dist/src');
const fs = require('fs-extra');
const path = require('path');

// 简单的颜色输出函数
const colors = {
  blue: (text) => `\x1b[34m${text}\x1b[0m`,
  green: (text) => `\x1b[32m${text}\x1b[0m`,
  yellow: (text) => `\x1b[33m${text}\x1b[0m`,
  red: (text) => `\x1b[31m${text}\x1b[0m`,
  gray: (text) => `\x1b[90m${text}\x1b[0m`
};

class MemorySystemTester {
  constructor() {
    this.memorySystem = null;
    this.testResults = [];
  }

  async runAllTests() {
    console.log(colors.blue('🧪 开始YDS-Lab长记忆系统功能测试...'));
    console.log('');

    try {
      await this.testSystemInitialization();
      await this.testMemoryStorage();
      await this.testMemoryRetrieval();
      await this.testSystemStatistics();
      await this.testConfigurationManagement();
      
      this.outputTestResults();
      
    } catch (error) {
      console.error(colors.red('❌ 测试过程中发生错误：'), error.message);
      process.exit(1);
    } finally {
      if (this.memorySystem) {
        await this.memorySystem.destroy();
      }
    }
  }

  async testSystemInitialization() {
    console.log(colors.blue('📋 测试1: 系统初始化'));
    
    try {
      this.memorySystem = new LongTermMemorySystem();
      await this.memorySystem.initialize();
      
      this.addTestResult('系统初始化', true, '系统成功初始化');
      console.log(colors.green('  ✓ 系统初始化成功'));
      
    } catch (error) {
      this.addTestResult('系统初始化', false, error.message);
      console.log(colors.red('  ✗ 系统初始化失败：' + error.message));
      throw error;
    }
  }

  async testMemoryStorage() {
    console.log(colors.blue('📋 测试2: 记忆存储功能'));
    
    try {
      const testMemory = {
        content: '这是一个测试记忆，用于验证YDS-Lab长记忆系统的存储功能',
        type: 'semantic', // 使用有效的记忆类型
        metadata: {
          source: 'test-script',
          importance: 'medium',
          tags: ['test', 'yds-lab', 'memory-system'],
          project: 'memory-system-test'
        }
      };

      const memoryId = await this.memorySystem.storeMemory(testMemory);
      
      if (memoryId) {
        this.addTestResult('记忆存储', true, `记忆ID: ${memoryId}`);
        console.log(colors.green(`  ✓ 记忆存储成功，ID: ${memoryId}`));
      } else {
        throw new Error('记忆存储返回空ID');
      }
      
    } catch (error) {
      this.addTestResult('记忆存储', false, error.message);
      console.log(colors.red('  ✗ 记忆存储失败：' + error.message));
    }
  }

  async testMemoryRetrieval() {
    console.log(colors.blue('📋 测试3: 记忆检索功能'));
    
    try {
      const query = {
        text: '测试记忆',
        type: 'semantic',
        limit: 10
      };
      
      const result = await this.memorySystem.retrieveMemories(query);
      
      if (result && result.memories && result.memories.length > 0) {
        this.addTestResult('记忆检索', true, `找到 ${result.memories.length} 条记忆`);
        console.log(colors.green(`  ✓ 记忆检索成功，找到 ${result.memories.length} 条记忆`));
        console.log(colors.gray(`    - 置信度: ${result.confidence}`));
        
        // 显示第一条记忆的详细信息
        if (result.memories[0]) {
          console.log(colors.gray(`    - 记忆内容: ${result.memories[0].content?.substring(0, 50)}...`));
          console.log(colors.gray(`    - 记忆类型: ${result.memories[0].type}`));
        }
      } else {
        this.addTestResult('记忆检索', false, '未找到任何记忆');
        console.log(colors.yellow('  ⚠️  记忆检索未找到结果'));
      }
      
    } catch (error) {
      this.addTestResult('记忆检索', false, error.message);
      console.log(colors.red('  ✗ 记忆检索失败：' + error.message));
    }
  }

  async testSystemStatistics() {
    console.log(colors.blue('📋 测试4: 系统统计功能'));
    
    try {
      const stats = this.memorySystem.getSystemStats();
      
      if (stats) {
        this.addTestResult('系统统计', true, '统计信息获取成功');
        console.log(colors.green('  ✓ 系统统计获取成功'));
        console.log(colors.gray(`    - 记忆数量: ${stats.memory?.total_memories || 0}`));
        console.log(colors.gray(`    - 规则数量: ${stats.rules?.total_rules || 0}`));
        console.log(colors.gray(`    - 知识节点: ${stats.knowledge?.total_nodes || 0}`));
      } else {
        throw new Error('统计信息为空');
      }
      
    } catch (error) {
      this.addTestResult('系统统计', false, error.message);
      console.log(colors.red('  ✗ 系统统计失败：' + error.message));
    }
  }

  async testConfigurationManagement() {
    console.log(colors.blue('📋 测试5: 配置管理功能'));
    
    try {
      const configManager = this.memorySystem.getConfigManager();
      
      if (configManager) {
        const config = configManager.getSystemConfig();
        
        if (config && config.database && config.cache && config.logging) {
          this.addTestResult('配置管理', true, '配置获取成功');
          console.log(colors.green('  ✓ 配置管理功能正常'));
          console.log(colors.gray(`    - 数据库类型: ${config.database.type}`));
          console.log(colors.gray(`    - 缓存启用: ${config.cache.enabled}`));
          console.log(colors.gray(`    - 日志级别: ${config.logging.level}`));
        } else {
          throw new Error('配置信息不完整');
        }
      } else {
        throw new Error('配置管理器未初始化');
      }
      
    } catch (error) {
      this.addTestResult('配置管理', false, error.message);
      console.log(colors.red('  ✗ 配置管理失败：' + error.message));
    }
  }

  addTestResult(testName, success, message) {
    this.testResults.push({
      test: testName,
      success: success,
      message: message,
      timestamp: new Date().toISOString()
    });
  }

  outputTestResults() {
    console.log('');
    console.log(colors.blue('📊 测试结果汇总'));
    console.log('='.repeat(50));
    
    const successCount = this.testResults.filter(r => r.success).length;
    const totalCount = this.testResults.length;
    
    this.testResults.forEach(result => {
      const status = result.success ? colors.green('✓ 通过') : colors.red('✗ 失败');
      console.log(`${status} ${result.test}: ${result.message}`);
    });
    
    console.log('='.repeat(50));
    console.log(`总计: ${totalCount} 项测试，${successCount} 项通过，${totalCount - successCount} 项失败`);
    
    if (successCount === totalCount) {
      console.log('');
      console.log(colors.green('🎉 所有测试通过！YDS-Lab长记忆系统部署成功！'));
      console.log('');
      console.log(colors.blue('📋 系统已就绪，可以开始使用：'));
      console.log(colors.gray('  1. 在其他项目中引用: require("../memory-system/dist/src")'));
      console.log(colors.gray('  2. 通过符号链接访问: require("../memory")'));
      console.log(colors.gray('  3. 查看使用文档: README.md'));
      console.log(colors.gray('  4. 配置个性化设置: memory-config.yaml'));
    } else {
      console.log('');
      console.log(colors.yellow('⚠️  部分测试失败，请检查系统配置'));
    }
  }
}

// 运行测试
if (require.main === module) {
  const tester = new MemorySystemTester();
  tester.runAllTests().catch(console.error);
}

module.exports = MemorySystemTester;