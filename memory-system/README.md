# YDS-Lab 长记忆系统

## 概述

YDS-Lab长记忆系统是基于Trae长记忆功能的统一记忆管理解决方案，为YDS-Lab环境中的各个项目提供智能记忆存储、检索和管理功能。

## 部署信息

- **部署时间**: 2025/11/2 00:35:37
- **部署目录**: S:\YDS-Lab\memory-system
- **YDS-Lab根目录**: S:\YDS-Lab
- **Node.js版本**: v22.20.0

## 快速开始

### 1. 基本使用

```javascript
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
```

### 2. 配置管理

编辑 `memory-config.yaml` 文件来自定义系统配置：

```yaml
system:
  name: "YDS-Lab长记忆系统"
  environment: "production"

storage:
  memory_path: "./data/memories"
  knowledge_graph_path: "./data/knowledge-graph"
```

### 3. 集成到项目

在其他YDS-Lab项目中使用：

```javascript
// 通过符号链接访问
const memorySystem = require('../memory');

// 或者通过npm包方式
const memorySystem = require('@yds-lab/memory-system');
```

## 目录结构

```
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
```

## 维护命令

- `npm run build` - 编译TypeScript代码
- `npm run dev` - 开发模式运行
- `npm test` - 运行测试
- `npm run lint` - 代码检查
- `node scripts/validate-config.js` - 验证配置
- `node scripts/init-memory.js` - 重新初始化系统

## 故障排除

### 常见问题

1. **TypeScript编译错误**
   ```bash
   npm run clean
   npm run build
   ```

2. **配置文件错误**
   ```bash
   node scripts/validate-config.js
   ```

3. **权限错误**
   - 确保对数据目录有读写权限
   - Windows环境下可能需要管理员权限创建符号链接

### 获取帮助

- 查看日志文件: `logs/`
- 运行诊断脚本: `node scripts/validate-config.js`
- 查看Trae配置: `.trae/`

## 更新日志

### v1.0.0 (2025-11-01)
- 初始部署到YDS-Lab环境
- 集成Trae长记忆功能
- 支持多项目统一记忆管理
- 提供完整的配置和部署脚本

---

**注意**: 这是自动生成的部署文档，部署时间: 2025/11/2 00:35:37
