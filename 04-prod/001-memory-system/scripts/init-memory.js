#!/usr/bin/env node

/**
 * YDS-Lab 长记忆系统初始化脚本
 * 
 * 用于初始化长记忆系统的基础数据结构和配置
 */

const fs = require('fs-extra');
const path = require('path');

// 简单的颜色输出函数，替代chalk
const colors = {
  blue: (text) => `\x1b[34m${text}\x1b[0m`,
  green: (text) => `\x1b[32m${text}\x1b[0m`,
  yellow: (text) => `\x1b[33m${text}\x1b[0m`,
  red: (text) => `\x1b[31m${text}\x1b[0m`,
  gray: (text) => `\x1b[90m${text}\x1b[0m`
};

const chalk = colors;

class MemorySystemInitializer {
  constructor() {
    this.baseDir = process.cwd();
    this.dataDir = path.join(this.baseDir, 'data');
    this.logsDir = path.join(this.baseDir, 'logs');
    // 统一备份目录到顶层，可通过环境变量 YDS_BACKUPS_ROOT 覆盖
    const topBackups = process.env.YDS_BACKUPS_ROOT || 'S\\\\YDS-Lab\\\\backups';
    this.backupsDir = topBackups;
  }

  async initialize() {
    console.log(chalk.blue('🚀 初始化YDS-Lab长记忆系统...'));
    
    try {
      // 创建必要的目录结构
      await this.createDirectories();
      
      // 初始化数据文件
      await this.initializeDataFiles();
      
      // 验证配置文件
      await this.validateConfiguration();
      
      // 创建示例数据
      await this.createExampleData();
      
      console.log(chalk.green('✅ YDS-Lab长记忆系统初始化完成！'));
      console.log(chalk.yellow('💡 提示：请运行 npm run build 编译TypeScript代码'));
      
    } catch (error) {
      console.error(chalk.red('❌ 初始化失败：'), error.message);
      process.exit(1);
    }
  }

  async createDirectories() {
    console.log(chalk.blue('📁 创建目录结构...'));
    
    const directories = [
      path.join(this.dataDir, 'memories'),
      path.join(this.dataDir, 'knowledge-graph'),
      path.join(this.dataDir, 'cache'),
      path.join(this.logsDir, 'performance'),
      this.backupsDir
    ];

    for (const dir of directories) {
      await fs.ensureDir(dir);
      console.log(chalk.gray(`  ✓ ${dir}`));
    }
  }

  async initializeDataFiles() {
    console.log(chalk.blue('📄 初始化数据文件...'));
    
    // 创建空的记忆索引文件
    const memoryIndexPath = path.join(this.dataDir, 'memories', 'index.json');
    if (!await fs.pathExists(memoryIndexPath)) {
      await fs.writeJson(memoryIndexPath, {
        version: '1.0.0',
        created_at: new Date().toISOString(),
        memories: [],
        total_count: 0
      }, { spaces: 2 });
      console.log(chalk.gray('  ✓ 记忆索引文件'));
    }

    // 创建知识图谱初始文件
    const knowledgeGraphPath = path.join(this.dataDir, 'knowledge-graph', 'graph.json');
    if (!await fs.pathExists(knowledgeGraphPath)) {
      await fs.writeJson(knowledgeGraphPath, {
        version: '1.0.0',
        created_at: new Date().toISOString(),
        nodes: [],
        edges: [],
        metadata: {
          node_count: 0,
          edge_count: 0
        }
      }, { spaces: 2 });
      console.log(chalk.gray('  ✓ 知识图谱文件'));
    }

    // 创建性能监控日志文件
    const performanceLogPath = path.join(this.logsDir, 'performance', 'metrics.json');
    if (!await fs.pathExists(performanceLogPath)) {
      await fs.writeJson(performanceLogPath, {
        version: '1.0.0',
        started_at: new Date().toISOString(),
        metrics: []
      }, { spaces: 2 });
      console.log(chalk.gray('  ✓ 性能监控文件'));
    }
  }

  async validateConfiguration() {
    console.log(chalk.blue('🔍 验证配置文件...'));
    
    const configPath = path.join(this.baseDir, 'memory-config.yaml');
    if (!await fs.pathExists(configPath)) {
      throw new Error('配置文件 memory-config.yaml 不存在');
    }
    
    console.log(chalk.gray('  ✓ 配置文件存在'));
  }

  async createExampleData() {
    console.log(chalk.blue('📝 创建示例数据...'));
    
    // 创建示例记忆
    const exampleMemory = {
      id: 'example_memory_001',
      type: 'system_initialization',
      content: 'YDS-Lab长记忆系统初始化完成',
      metadata: {
        source: 'init-script',
        importance: 'high',
        tags: ['system', 'initialization', 'yds-lab']
      },
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    const exampleMemoryPath = path.join(this.dataDir, 'memories', 'example_memory_001.json');
    await fs.writeJson(exampleMemoryPath, exampleMemory, { spaces: 2 });
    console.log(chalk.gray('  ✓ 示例记忆数据'));

    // 更新记忆索引
    const memoryIndexPath = path.join(this.dataDir, 'memories', 'index.json');
    const memoryIndex = await fs.readJson(memoryIndexPath);
    memoryIndex.memories.push({
      id: exampleMemory.id,
      type: exampleMemory.type,
      created_at: exampleMemory.created_at,
      file_path: 'example_memory_001.json'
    });
    memoryIndex.total_count = 1;
    memoryIndex.updated_at = new Date().toISOString();
    await fs.writeJson(memoryIndexPath, memoryIndex, { spaces: 2 });
  }
}

// 运行初始化
if (require.main === module) {
  const initializer = new MemorySystemInitializer();
  initializer.initialize().catch(console.error);
}

module.exports = MemorySystemInitializer;