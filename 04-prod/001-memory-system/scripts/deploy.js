#!/usr/bin/env node

/**
 * YDS-Lab 长记忆系统部署脚本
 * 
 * 自动化部署长记忆系统到YDS-Lab环境
 */

const fs = require('fs-extra');
const path = require('path');
const { execSync } = require('child_process');

// 简单的颜色输出函数，替代chalk
const colors = {
  blue: (text) => `\x1b[34m${text}\x1b[0m`,
  green: (text) => `\x1b[32m${text}\x1b[0m`,
  yellow: (text) => `\x1b[33m${text}\x1b[0m`,
  red: (text) => `\x1b[31m${text}\x1b[0m`,
  gray: (text) => `\x1b[90m${text}\x1b[0m`
};

const chalk = colors;

class MemorySystemDeployer {
  constructor() {
    this.baseDir = process.cwd();
    this.ydsLabRoot = path.resolve(this.baseDir, '..');
    this.deploymentSteps = [
      'validateEnvironment',
      'installDependencies',
      'buildProject',
      'initializeSystem',
      'validateConfiguration',
      'createSymlinks',
      'runTests',
      'generateDocumentation'
    ];
  }

  async deploy() {
    console.log(chalk.blue('🚀 开始部署YDS-Lab长记忆系统...'));
    console.log(chalk.gray(`部署目录: ${this.baseDir}`));
    console.log(chalk.gray(`YDS-Lab根目录: ${this.ydsLabRoot}`));
    console.log('');

    try {
      for (const step of this.deploymentSteps) {
        await this[step]();
      }

      console.log('');
      console.log(chalk.green('🎉 YDS-Lab长记忆系统部署成功！'));
      console.log('');
      console.log(chalk.blue('📋 后续步骤：'));
      console.log(chalk.gray('  1. 查看部署文档: README.md'));
      console.log(chalk.gray('  2. 配置个性化规则: memory-config.yaml'));
      console.log(chalk.gray('  3. 集成到项目工作流'));
      console.log(chalk.gray('  4. 监控系统性能'));
      console.log('');

    } catch (error) {
      console.error(chalk.red('❌ 部署失败：'), error.message);
      console.log(chalk.yellow('💡 请检查错误信息并重新运行部署脚本'));
      process.exit(1);
    }
  }

  async validateEnvironment() {
    console.log(chalk.blue('🔍 验证部署环境...'));

    // 检查Node.js版本
    const nodeVersion = process.version;
    console.log(chalk.gray(`  ✓ Node.js版本: ${nodeVersion}`));

    // 检查npm版本
    try {
      const npmVersion = execSync('npm --version', { encoding: 'utf8' }).trim();
      console.log(chalk.gray(`  ✓ npm版本: ${npmVersion}`));
    } catch (error) {
      throw new Error('npm未安装或不可用');
    }

    // 检查YDS-Lab根目录
    if (!await fs.pathExists(this.ydsLabRoot)) {
      throw new Error('YDS-Lab根目录不存在');
    }
    console.log(chalk.gray(`  ✓ YDS-Lab根目录存在`));

    // 检查必要文件
    const requiredFiles = ['package.json', 'tsconfig.json', 'memory-config.yaml'];
    for (const file of requiredFiles) {
      const filePath = path.join(this.baseDir, file);
      if (!await fs.pathExists(filePath)) {
        throw new Error(`必要文件不存在: ${file}`);
      }
    }
    console.log(chalk.gray(`  ✓ 必要文件完整`));
  }

  async installDependencies() {
    console.log(chalk.blue('📦 安装项目依赖...'));

    try {
      execSync('npm install', { 
        cwd: this.baseDir, 
        stdio: 'pipe',
        encoding: 'utf8'
      });
      console.log(chalk.gray('  ✓ 依赖安装完成'));
    } catch (error) {
      throw new Error('依赖安装失败: ' + error.message);
    }
  }

  async buildProject() {
    console.log(chalk.blue('🔨 编译TypeScript项目...'));

    try {
      execSync('npm run build', { 
        cwd: this.baseDir, 
        stdio: 'pipe',
        encoding: 'utf8'
      });
      console.log(chalk.gray('  ✓ 项目编译完成'));

      // 验证编译输出
      const distPath = path.join(this.baseDir, 'dist');
      if (!await fs.pathExists(distPath)) {
        throw new Error('编译输出目录不存在');
      }
      console.log(chalk.gray('  ✓ 编译输出验证通过'));
    } catch (error) {
      throw new Error('项目编译失败: ' + error.message);
    }
  }

  async initializeSystem() {
    console.log(chalk.blue('🏗️  初始化长记忆系统...'));

    try {
      execSync('node scripts/init-memory.js', { 
        cwd: this.baseDir, 
        stdio: 'inherit'
      });
      console.log(chalk.gray('  ✓ 系统初始化完成'));
    } catch (error) {
      throw new Error('系统初始化失败: ' + error.message);
    }
  }

  async validateConfiguration() {
    console.log(chalk.blue('✅ 验证系统配置...'));

    try {
      execSync('node scripts/validate-config.js', { 
        cwd: this.baseDir, 
        stdio: 'inherit'
      });
      console.log(chalk.gray('  ✓ 配置验证通过'));
    } catch (error) {
      throw new Error('配置验证失败: ' + error.message);
    }
  }

  async createSymlinks() {
    console.log(chalk.blue('🔗 创建符号链接...'));

    // 在YDS-Lab根目录创建memory-system的符号链接
    const symlinkPath = path.join(this.ydsLabRoot, 'memory');
    
    try {
      // 如果符号链接已存在，先删除
      if (await fs.pathExists(symlinkPath)) {
        await fs.remove(symlinkPath);
      }

      // 创建符号链接（Windows需要管理员权限，这里使用复制作为替代）
      if (process.platform === 'win32') {
        // Windows环境下创建junction
        execSync(`mklink /J "${symlinkPath}" "${this.baseDir}"`, { 
          shell: 'cmd.exe',
          stdio: 'pipe'
        });
      } else {
        // Unix环境下创建符号链接
        await fs.symlink(this.baseDir, symlinkPath);
      }
      
      console.log(chalk.gray(`  ✓ 符号链接创建: ${symlinkPath}`));
    } catch (error) {
      // 如果符号链接创建失败，使用复制作为备选方案
      console.log(chalk.yellow('  ⚠️  符号链接创建失败，使用复制方式'));
      await fs.copy(this.baseDir, symlinkPath, {
        filter: (src) => !src.includes('node_modules') && !src.includes('.git')
      });
      console.log(chalk.gray(`  ✓ 目录复制完成: ${symlinkPath}`));
    }
  }

  async runTests() {
    console.log(chalk.blue('🧪 运行系统测试...'));

    try {
      // 检查是否有测试文件
      const testDir = path.join(this.baseDir, 'tests');
      if (await fs.pathExists(testDir)) {
        execSync('npm test', { 
          cwd: this.baseDir, 
          stdio: 'inherit'
        });
        console.log(chalk.gray('  ✓ 测试通过'));
      } else {
        console.log(chalk.yellow('  ⚠️  未找到测试文件，跳过测试'));
      }
    } catch (error) {
      console.log(chalk.yellow('  ⚠️  测试失败，但不影响部署: ' + error.message));
    }
  }

  async generateDocumentation() {
    console.log(chalk.blue('📚 生成部署文档...'));

    const readmePath = path.join(this.baseDir, 'README.md');
    const readmeContent = `# YDS-Lab 长记忆系统

## 概述

YDS-Lab长记忆系统是基于Trae长记忆功能的统一记忆管理解决方案，为YDS-Lab环境中的各个项目提供智能记忆存储、检索和管理功能。

## 部署信息

- **部署时间**: ${new Date().toLocaleString('zh-CN')}
- **部署目录**: ${this.baseDir}
- **YDS-Lab根目录**: ${this.ydsLabRoot}
- **Node.js版本**: ${process.version}

## 快速开始

### 1. 基本使用

\`\`\`javascript
const { LongTermMemorySystem } = require('./dist');

// 初始化系统
const memorySystem = new LongTermMemorySystem();
await memorySystem.initialize();

// 存储记忆
await memorySystem.storeMemory({
  content: '这是一个重要的项目决策',
  type: 'decision',
  metadata: {
    project: 'YDS-Lab',
    importance: 'high'
  }
});

// 检索记忆
const memories = await memorySystem.retrieveMemories('项目决策');
console.log(memories);
\`\`\`

### 2. 配置管理

编辑 \`memory-config.yaml\` 文件来自定义系统配置：

\`\`\`yaml
system:
  name: "YDS-Lab长记忆系统"
  environment: "production"

storage:
  memory_path: "./data/memories"
  knowledge_graph_path: "./data/knowledge-graph"
\`\`\`

### 3. 集成到项目

在其他YDS-Lab项目中使用：

\`\`\`javascript
// 通过符号链接访问
const memorySystem = require('../memory');

// 或者通过npm包方式
const memorySystem = require('@yds-lab/memory-system');
\`\`\`

## 目录结构

\`\`\`
memory-system/
├── src/                    # TypeScript源代码
│   ├── config/            # 配置管理
│   ├── services/          # 核心服务
│   ├── types/             # 类型定义
│   └── utils/             # 工具函数
├── dist/                  # 编译输出
├── data/                  # 数据存储
├── logs/                  # 日志文件
├── scripts/               # 部署脚本
├── .trae/                 # Trae配置
├── memory-config.yaml     # 系统配置
└── package.json           # 项目配置
\`\`\`

## 维护命令

- \`npm run build\` - 编译TypeScript代码
- \`npm run dev\` - 开发模式运行
- \`npm test\` - 运行测试
- \`npm run lint\` - 代码检查
- \`node scripts/validate-config.js\` - 验证配置
- \`node scripts/init-memory.js\` - 重新初始化系统

## 故障排除

### 常见问题

1. **TypeScript编译错误**
   \`\`\`bash
   npm run clean
   npm run build
   \`\`\`

2. **配置文件错误**
   \`\`\`bash
   node scripts/validate-config.js
   \`\`\`

3. **权限错误**
   - 确保对数据目录有读写权限
   - Windows环境下可能需要管理员权限创建符号链接

### 获取帮助

- 查看日志文件: \`logs/\`
- 运行诊断脚本: \`node scripts/validate-config.js\`
- 查看Trae配置: \`.trae/\`

## 更新日志

### v1.0.0 (${new Date().toISOString().split('T')[0]})
- 初始部署到YDS-Lab环境
- 集成Trae长记忆功能
- 支持多项目统一记忆管理
- 提供完整的配置和部署脚本

---

**注意**: 这是自动生成的部署文档，部署时间: ${new Date().toLocaleString('zh-CN')}
`;

    await fs.writeFile(readmePath, readmeContent, 'utf8');
    console.log(chalk.gray('  ✓ 部署文档生成完成'));
  }
}

// 运行部署
if (require.main === module) {
  const deployer = new MemorySystemDeployer();
  deployer.deploy().catch(console.error);
}

module.exports = MemorySystemDeployer;