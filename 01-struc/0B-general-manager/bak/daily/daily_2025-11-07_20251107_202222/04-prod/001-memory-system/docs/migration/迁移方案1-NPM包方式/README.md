# 迁移方案1: NPM包方式 (推荐)

## 📦 概述

将JS003-Trae长记忆功能打包为NPM包，便于在其他项目中安装和使用。这是最推荐的迁移方式，具有版本管理、依赖管理和更新便利等优势。

## 🎯 适用场景

- 需要在多个项目中复用长记忆功能
- 希望通过NPM进行版本管理
- 团队协作开发，需要统一的包管理
- 需要发布到私有或公共NPM仓库

## 📋 迁移步骤

### 步骤1: 准备NPM包

1. **修改package.json**
```json
{
  "name": "@your-org/trae-long-term-memory",
  "version": "1.0.0",
  "description": "Trae长记忆功能系统 - 包含规则系统和知识图谱记忆",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "files": [
    "dist/**/*",
    "README.md",
    "LICENSE"
  ],
  "scripts": {
    "build": "tsc",
    "prepublishOnly": "npm run build"
  },
  "keywords": [
    "trae",
    "memory",
    "knowledge-graph",
    "rules-engine",
    "ai-assistant"
  ],
  "author": "Your Name",
  "license": "MIT",
  "repository": {
    "type": "git",
    "url": "https://github.com/your-org/trae-long-term-memory.git"
  }
}
```

2. **构建包**
```bash
npm run build
```

3. **发布到NPM**
```bash
# 登录NPM (如果还未登录)
npm login

# 发布包
npm publish
```

### 步骤2: 在目标项目中安装

```bash
# 安装NPM包
npm install @your-org/trae-long-term-memory

# 或使用yarn
yarn add @your-org/trae-long-term-memory
```

### 步骤3: 在目标项目中使用

1. **基本导入和使用**
```typescript
// 导入主要类
import { LongTermMemorySystem } from '@your-org/trae-long-term-memory';

// 创建实例
const memorySystem = new LongTermMemorySystem();

// 初始化
await memorySystem.initialize();

// 使用功能
const memoryId = await memorySystem.storeMemory({
  content: "用户偏好信息",
  type: "preference",
  tags: ["user", "preference"]
});
```

2. **按需导入**
```typescript
// 只导入需要的模块
import { 
  RuleManager, 
  KnowledgeGraphManager,
  MemoryRetrievalManager 
} from '@your-org/trae-long-term-memory';

const ruleManager = new RuleManager();
const knowledgeGraph = new KnowledgeGraphManager();
```

### 步骤4: 配置文件迁移

1. **复制配置文件**
```bash
# 创建配置目录
mkdir -p .trae/rules

# 复制规则配置
cp node_modules/@your-org/trae-long-term-memory/examples/personal-rules.yaml .trae/rules/
cp node_modules/@your-org/trae-long-term-memory/examples/project-rules.yaml .trae/rules/
```

2. **自定义配置**
```typescript
// 使用自定义配置路径
const memorySystem = new LongTermMemorySystem('./config/memory-config.json');
```

## 📁 包结构

```
@your-org/trae-long-term-memory/
├── dist/                          # 编译后的代码
│   ├── index.js                   # 主入口文件
│   ├── index.d.ts                 # TypeScript类型定义
│   ├── config/                    # 配置模块
│   ├── services/                  # 服务模块
│   └── utils/                     # 工具模块
├── examples/                      # 示例配置文件
│   ├── personal-rules.yaml        # 个人规则示例
│   ├── project-rules.yaml         # 项目规则示例
│   └── usage-examples.ts          # 使用示例
├── docs/                          # 文档
├── package.json                   # 包配置
├── README.md                      # 说明文档
└── LICENSE                        # 许可证
```

## 🔧 高级配置

### 环境变量配置

```bash
# .env文件
TRAE_MEMORY_CONFIG_PATH=./config/memory-config.json
TRAE_MEMORY_LOG_LEVEL=info
TRAE_MEMORY_PERFORMANCE_MONITORING=true
```

### TypeScript配置

```json
// tsconfig.json
{
  "compilerOptions": {
    "types": ["@your-org/trae-long-term-memory"]
  }
}
```

### Webpack配置 (如果需要)

```javascript
// webpack.config.js
module.exports = {
  resolve: {
    alias: {
      '@memory': '@your-org/trae-long-term-memory'
    }
  }
};
```

## 🚀 使用示例

### 完整集成示例

```typescript
// src/memory-integration.ts
import { 
  LongTermMemorySystem,
  type Memory,
  type RetrievalQuery 
} from '@your-org/trae-long-term-memory';

export class ProjectMemoryService {
  private memorySystem: LongTermMemorySystem;

  constructor() {
    this.memorySystem = new LongTermMemorySystem();
  }

  async initialize() {
    await this.memorySystem.initialize();
    console.log('记忆系统已初始化');
  }

  async storeUserPreference(preference: string, tags: string[]) {
    return await this.memorySystem.storeMemory({
      content: preference,
      type: 'preference',
      tags,
      metadata: { source: 'user_input' }
    });
  }

  async getRelevantMemories(query: string, limit = 5) {
    const retrievalQuery: RetrievalQuery = {
      query,
      limit,
      threshold: 0.7,
      includeMetadata: true
    };

    return await this.memorySystem.retrieveMemories(retrievalQuery);
  }

  async getEnhancedContext(task: string) {
    return await this.memorySystem.getEnhancementContext({
      query: task,
      includeRules: true,
      includeMemories: true,
      maxMemories: 10
    });
  }
}

// 使用示例
async function main() {
  const memoryService = new ProjectMemoryService();
  await memoryService.initialize();

  // 存储用户偏好
  await memoryService.storeUserPreference(
    "用户喜欢使用React进行前端开发",
    ["react", "frontend", "preference"]
  );

  // 检索相关记忆
  const memories = await memoryService.getRelevantMemories("前端开发");
  console.log('相关记忆:', memories);

  // 获取增强上下文
  const context = await memoryService.getEnhancedContext("创建React组件");
  console.log('增强上下文:', context);
}
```

### React项目集成示例

```typescript
// src/hooks/useMemorySystem.ts
import { useEffect, useState } from 'react';
import { LongTermMemorySystem } from '@your-org/trae-long-term-memory';

export function useMemorySystem() {
  const [memorySystem, setMemorySystem] = useState<LongTermMemorySystem | null>(null);
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    const initMemorySystem = async () => {
      const system = new LongTermMemorySystem();
      await system.initialize();
      setMemorySystem(system);
      setIsInitialized(true);
    };

    initMemorySystem();
  }, []);

  return { memorySystem, isInitialized };
}

// 组件中使用
function MyComponent() {
  const { memorySystem, isInitialized } = useMemorySystem();

  const handleStoreMemory = async (content: string) => {
    if (memorySystem) {
      await memorySystem.storeMemory({
        content,
        type: 'user_action',
        tags: ['ui', 'interaction']
      });
    }
  };

  if (!isInitialized) {
    return <div>正在初始化记忆系统...</div>;
  }

  return (
    <div>
      {/* 你的组件内容 */}
    </div>
  );
}
```

## 📊 版本管理

### 语义化版本控制

- **主版本号**: 不兼容的API修改
- **次版本号**: 向下兼容的功能性新增
- **修订号**: 向下兼容的问题修正

### 更新策略

```bash
# 检查更新
npm outdated @your-org/trae-long-term-memory

# 更新到最新版本
npm update @your-org/trae-long-term-memory

# 更新到指定版本
npm install @your-org/trae-long-term-memory@^2.0.0
```

## 🔍 故障排除

### 常见问题

1. **安装失败**
   - 检查NPM仓库访问权限
   - 确认网络连接正常
   - 尝试清除NPM缓存: `npm cache clean --force`

2. **类型定义问题**
   - 确认TypeScript版本兼容性
   - 检查tsconfig.json配置
   - 重新安装类型定义: `npm install --save-dev @types/node`

3. **运行时错误**
   - 检查配置文件路径
   - 确认所有依赖已安装
   - 查看详细错误日志

## ✅ 优势

- **版本管理**: 通过NPM进行版本控制
- **依赖管理**: 自动处理依赖关系
- **更新便利**: 一键更新到最新版本
- **团队协作**: 统一的包管理和版本
- **文档完整**: 包含完整的API文档和示例
- **类型安全**: 完整的TypeScript类型定义

## 📝 注意事项

1. **私有包**: 如果是私有项目，考虑使用私有NPM仓库
2. **版本兼容**: 注意不同版本间的API变更
3. **配置迁移**: 升级时注意配置文件的兼容性
4. **性能考虑**: 大型项目中注意包大小和加载性能

---

**推荐指数**: ⭐⭐⭐⭐⭐ (强烈推荐)
**适用场景**: 所有类型的项目，特别是需要版本管理的项目
**维护成本**: 低
**学习成本**: 低