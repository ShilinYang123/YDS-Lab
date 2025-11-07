# Trae IDE 长效记忆系统集成指南

## 概述

本指南详细介绍如何在 Trae IDE 中集成和使用 YDS-Lab 长效记忆系统的自动记录功能。该功能能够自动捕获、处理和存储用户在 IDE 中的交互行为，为 AI 助手提供持续的学习和改进能力。

## 功能特性

### 🎯 核心功能
- **自动交互捕获**: 实时捕获用户输入、AI响应、代码执行等事件
- **智能内容筛选**: 基于重要性、相似度等多维度筛选有价值的记忆
- **上下文感知处理**: 自动提取文件、项目、Git等上下文信息
- **批量处理优化**: 高效的批处理机制，减少系统开销
- **实时监控统计**: 提供详细的性能监控和统计信息

### 🔧 技术特性
- **模块化设计**: 松耦合的组件架构，易于扩展和维护
- **配置驱动**: 灵活的配置系统，支持运行时动态调整
- **错误恢复**: 完善的错误处理和自动恢复机制
- **性能优化**: 内存缓存、异步处理等性能优化策略

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Trae IDE 集成层                          │
├─────────────────────────────────────────────────────────────┤
│  InteractionHook  │  ContextExtractor  │  TraeIDEIntegration │
├─────────────────────────────────────────────────────────────┤
│                   AutoRecordMiddleware                       │
├─────────────────────────────────────────────────────────────┤
│ IntelligentFilter │  ContentProcessor  │   MemoryService    │
├─────────────────────────────────────────────────────────────┤
│                 LongTermMemorySystem                        │
└─────────────────────────────────────────────────────────────┘
```

### 组件说明

1. **InteractionHook**: 事件捕获钩子，监听 IDE 中的各种交互事件
2. **ContextExtractor**: 上下文提取器，获取当前工作环境的上下文信息
3. **IntelligentFilter**: 智能筛选器，过滤和评估记忆的重要性
4. **ContentProcessor**: 内容处理器，分析和增强记忆内容
5. **MemoryService**: 记忆服务，负责记忆的存储和管理
6. **AutoRecordMiddleware**: 自动记录中间件，协调各组件工作
7. **TraeIDEIntegration**: 主集成组件，提供统一的管理接口

## 快速开始

### 1. 安装依赖

```bash
cd memory-system
npm install
```

### 2. 基础配置

创建配置文件 `trae-ide-config.yaml`:

```yaml
# Trae IDE 集成配置
traeIDEIntegration:
  enabled: true
  
  # 自动记录配置
  autoRecord:
    enabled: true
    batchSize: 10
    flushInterval: 5000
    maxRetries: 3
  
  # 智能筛选配置
  intelligentFilter:
    enabled: true
    minImportance: 0.3
    maxSimilarity: 0.8
    
  # 内容处理配置
  contentProcessor:
    enabled: true
    extractKeywords: true
    generateSummary: true
    analyzeCode: true
    
  # 上下文提取配置
  contextExtractor:
    enabled: true
    extractFileContext: true
    extractProjectContext: true
    extractGitContext: true
```

### 3. 初始化系统

```javascript
const { LongTermMemorySystem } = require('./src/index');

// 创建系统实例
const memorySystem = new LongTermMemorySystem();

// 初始化配置
const config = {
  dataPath: './data/memories',
  logLevel: 'info',
  traeIDEIntegration: {
    enabled: true,
    config: {
      // 从配置文件加载或直接配置
      autoRecord: { enabled: true },
      intelligentFilter: { enabled: true },
      contentProcessor: { enabled: true },
      contextExtractor: { enabled: true }
    }
  }
};

// 初始化系统
await memorySystem.initialize(config);

// 启用自动记录
await memorySystem.enableAutoRecord();

console.log('✅ Trae IDE 集成已启用');
```

## 详细配置

### 自动记录配置

```yaml
autoRecord:
  enabled: true                 # 是否启用自动记录
  batchSize: 10                # 批处理大小
  flushInterval: 5000          # 刷新间隔(毫秒)
  maxRetries: 3                # 最大重试次数
  queueSize: 1000              # 队列大小
  processingTimeout: 30000     # 处理超时(毫秒)
```

### 智能筛选配置

```yaml
intelligentFilter:
  enabled: true                # 是否启用智能筛选
  minImportance: 0.3          # 最小重要性阈值
  maxSimilarity: 0.8          # 最大相似度阈值
  
  # 内容过滤规则
  contentFilters:
    minLength: 10              # 最小内容长度
    maxLength: 10000           # 最大内容长度
    excludePatterns:           # 排除模式
      - "^console\\.log"
      - "^//"
      - "^\\s*$"
  
  # 元数据过滤规则
  metadataFilters:
    requiredFields: []         # 必需字段
    excludeTypes: []           # 排除类型
  
  # 频率控制
  frequencyControl:
    enabled: true
    maxSameContent: 3          # 相同内容最大数量
    timeWindow: 3600000        # 时间窗口(毫秒)
```

### 内容处理配置

```yaml
contentProcessor:
  enabled: true                # 是否启用内容处理
  extractKeywords: true        # 提取关键词
  generateSummary: true        # 生成摘要
  analyzeCode: true           # 分析代码
  compressContent: true       # 压缩内容
  
  # 关键词提取配置
  keywordExtraction:
    maxKeywords: 10           # 最大关键词数
    minKeywordLength: 3       # 最小关键词长度
    
  # 摘要生成配置
  summaryGeneration:
    maxLength: 200            # 最大摘要长度
    preserveCode: true        # 保留代码片段
    
  # 代码分析配置
  codeAnalysis:
    detectLanguage: true      # 检测编程语言
    extractFunctions: true    # 提取函数
    analyzeComplexity: true   # 分析复杂度
```

### 上下文提取配置

```yaml
contextExtractor:
  enabled: true               # 是否启用上下文提取
  extractFileContext: true    # 提取文件上下文
  extractProjectContext: true # 提取项目上下文
  extractGitContext: true     # 提取Git上下文
  
  # 缓存配置
  cache:
    enabled: true
    timeout: 300000          # 缓存超时(毫秒)
    maxSize: 1000           # 最大缓存条目数
  
  # 文件上下文配置
  fileContext:
    includeContent: true     # 包含文件内容
    maxContentLength: 5000   # 最大内容长度
    
  # 项目上下文配置
  projectContext:
    includeStructure: true   # 包含项目结构
    maxDepth: 3             # 最大目录深度
    
  # Git上下文配置
  gitContext:
    includeBranch: true     # 包含分支信息
    includeCommits: true    # 包含提交信息
    maxCommits: 10          # 最大提交数
```

## API 使用指南

### 基础操作

```javascript
// 获取集成状态
const integration = memorySystem.getTraeIDEIntegration();
const status = await integration.getStatus();
console.log('集成状态:', status);

// 获取自动记录状态
const autoRecordStatus = await memorySystem.getAutoRecordStatus();
console.log('自动记录状态:', autoRecordStatus);

// 暂停自动记录
await memorySystem.disableAutoRecord();

// 恢复自动记录
await memorySystem.enableAutoRecord();

// 手动触发记忆处理
await memorySystem.processMemoriesNow();
```

### 记忆操作

```javascript
// 存储记忆
const memory = {
  content: '用户执行了代码部署操作',
  type: 'episodic',
  metadata: {
    action: 'deployment',
    target: 'production',
    timestamp: new Date().toISOString()
  },
  context: {
    project: 'my-project',
    file: 'deploy.js'
  },
  importance: 0.8,
  tags: ['deployment', 'production']
};

const memoryId = await memorySystem.storeMemory(memory);

// 检索记忆
const results = await memorySystem.retrieveMemories('部署操作', {
  limit: 10,
  minConfidence: 0.5
});

console.log('检索结果:', results);
```

### 统计信息

```javascript
// 获取系统统计
const stats = await memorySystem.getSystemStats();
console.log('系统统计:', stats);

// 获取性能指标
const performance = memorySystem.getPerformanceMonitor();
const metrics = performance.getMetrics();
console.log('性能指标:', metrics);
```

## 事件类型

系统支持以下事件类型的自动捕获：

### 用户交互事件
- `USER_INPUT`: 用户输入内容
- `USER_SELECTION`: 用户选择操作
- `USER_NAVIGATION`: 用户导航行为

### AI 响应事件
- `AGENT_RESPONSE`: AI助手响应
- `AGENT_ACTION`: AI助手执行的操作
- `AGENT_SUGGESTION`: AI助手的建议

### 代码执行事件
- `CODE_EXECUTION`: 代码执行
- `COMMAND_RUN`: 命令执行
- `SCRIPT_EXECUTION`: 脚本执行

### 文件操作事件
- `FILE_CHANGE`: 文件变更
- `FILE_CREATE`: 文件创建
- `FILE_DELETE`: 文件删除

### 系统事件
- `ERROR_LOG`: 错误日志
- `SESSION_END`: 会话结束
- `SYSTEM_EVENT`: 系统事件

## 性能优化

### 批处理优化
- 使用批处理机制减少I/O操作
- 可配置的批处理大小和刷新间隔
- 智能队列管理

### 内存管理
- LRU缓存机制
- 定期内存清理
- 可配置的缓存大小

### 异步处理
- 非阻塞的事件处理
- 异步记忆存储
- 并发处理优化

## 监控和诊断

### 日志配置

```yaml
logging:
  level: info                 # 日志级别
  file: ./logs/trae-ide.log  # 日志文件
  maxSize: 10MB              # 最大文件大小
  maxFiles: 5                # 最大文件数
```

### 性能监控

```javascript
// 启用性能监控
const monitor = memorySystem.getPerformanceMonitor();

// 获取实时指标
const metrics = monitor.getMetrics();
console.log('CPU使用率:', metrics.cpu);
console.log('内存使用率:', metrics.memory);
console.log('响应时间:', metrics.responseTime);

// 设置告警阈值
monitor.setAlertThresholds({
  cpuUsage: 80,
  memoryUsage: 85,
  responseTime: 5000
});
```

### 健康检查

```javascript
// 执行健康检查
const integration = memorySystem.getTraeIDEIntegration();
const healthStatus = await integration.healthCheck();

console.log('健康状态:', healthStatus);
// 输出示例:
// {
//   status: 'healthy',
//   components: {
//     memoryService: 'healthy',
//     intelligentFilter: 'healthy',
//     contentProcessor: 'healthy',
//     contextExtractor: 'healthy'
//   },
//   uptime: 3600000,
//   lastCheck: '2024-01-01T12:00:00.000Z'
// }
```

## 故障排除

### 常见问题

#### 1. 自动记录未启动
**症状**: 事件未被捕获和记录
**解决方案**:
```javascript
// 检查配置
const status = await memorySystem.getAutoRecordStatus();
if (!status.enabled) {
  await memorySystem.enableAutoRecord();
}

// 检查组件状态
const integration = memorySystem.getTraeIDEIntegration();
const health = await integration.healthCheck();
console.log('组件健康状态:', health);
```

#### 2. 内存使用过高
**症状**: 系统内存占用持续增长
**解决方案**:
```javascript
// 调整批处理配置
const config = {
  autoRecord: {
    batchSize: 5,        // 减小批处理大小
    flushInterval: 3000  // 减少刷新间隔
  }
};

// 清理缓存
const integration = memorySystem.getTraeIDEIntegration();
await integration.clearCache();
```

#### 3. 处理延迟过高
**症状**: 事件处理响应时间过长
**解决方案**:
```javascript
// 优化筛选配置
const config = {
  intelligentFilter: {
    minImportance: 0.5,  // 提高重要性阈值
    maxSimilarity: 0.9   // 提高相似度阈值
  }
};

// 禁用部分处理功能
const config = {
  contentProcessor: {
    generateSummary: false,  // 禁用摘要生成
    analyzeCode: false       // 禁用代码分析
  }
};
```

### 调试模式

```javascript
// 启用调试模式
const config = {
  logLevel: 'debug',
  traeIDEIntegration: {
    config: {
      debug: true,
      verbose: true
    }
  }
};

await memorySystem.initialize(config);
```

## 最佳实践

### 1. 配置优化
- 根据项目规模调整批处理大小
- 合理设置重要性和相似度阈值
- 定期清理过期记忆

### 2. 性能监控
- 定期检查系统性能指标
- 设置合理的告警阈值
- 监控内存和CPU使用情况

### 3. 数据管理
- 定期备份记忆数据
- 实施数据保留策略
- 监控存储空间使用

### 4. 安全考虑
- 避免记录敏感信息
- 实施访问控制
- 定期安全审计

## 扩展开发

### 自定义事件处理器

```javascript
class CustomEventHandler {
  async handleEvent(event) {
    // 自定义事件处理逻辑
    if (event.type === 'CUSTOM_EVENT') {
      return {
        shouldRecord: true,
        importance: 0.8,
        tags: ['custom']
      };
    }
    return null;
  }
}

// 注册自定义处理器
const integration = memorySystem.getTraeIDEIntegration();
integration.registerEventHandler(new CustomEventHandler());
```

### 自定义筛选规则

```javascript
class CustomFilter {
  async shouldKeep(memory) {
    // 自定义筛选逻辑
    if (memory.metadata.project === 'important-project') {
      return true;
    }
    return memory.importance > 0.5;
  }
}

// 注册自定义筛选器
const filter = memorySystem.getIntelligentFilter();
filter.registerCustomFilter(new CustomFilter());
```

## 版本更新

### 升级指南
1. 备份现有数据
2. 更新代码库
3. 检查配置兼容性
4. 运行迁移脚本
5. 验证功能正常

### 兼容性说明
- 向后兼容现有配置
- 数据格式自动迁移
- API接口保持稳定

## 支持和反馈

如有问题或建议，请通过以下方式联系：

- 项目仓库: [YDS-Lab Memory System](https://github.com/yds-lab/memory-system)
- 问题反馈: 创建 GitHub Issue
- 文档更新: 提交 Pull Request

---

*本文档持续更新中，最新版本请查看项目仓库。*