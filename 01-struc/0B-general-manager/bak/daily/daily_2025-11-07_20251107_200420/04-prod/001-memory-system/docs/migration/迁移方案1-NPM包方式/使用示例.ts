/**
 * JS003-Trae长记忆功能 NPM包使用示例
 * 
 * 本文件展示了如何在项目中使用 @your-org/trae-long-term-memory NPM包
 */

import { 
  LongTermMemorySystem,
  RuleManager,
  KnowledgeGraphManager,
  MemoryRetrievalManager,
  type Memory,
  type RetrievalQuery,
  type Entity,
  type Relationship
} from '@your-org/trae-long-term-memory';

// ==================== 基础使用示例 ====================

/**
 * 基础使用示例 - 完整的系统初始化和使用
 */
async function basicUsageExample() {
  console.log('=== 基础使用示例 ===');
  
  // 1. 创建系统实例
  const memorySystem = new LongTermMemorySystem();
  
  // 2. 初始化系统
  await memorySystem.initialize();
  console.log('✅ 记忆系统初始化完成');
  
  // 3. 存储记忆
  const memoryId = await memorySystem.storeMemory({
    content: "用户偏好使用React进行前端开发，特别喜欢函数式组件和Hooks",
    type: "preference",
    tags: ["react", "frontend", "hooks", "functional-components"],
    metadata: {
      importance: "high",
      source: "user_interview",
      context: "project_setup"
    }
  });
  console.log('✅ 记忆已存储，ID:', memoryId);
  
  // 4. 检索记忆
  const memories = await memorySystem.retrieveMemories({
    query: "前端开发框架偏好",
    limit: 5,
    threshold: 0.7,
    tags: ["frontend"],
    includeMetadata: true
  });
  console.log('✅ 检索到记忆:', memories.length, '条');
  
  // 5. 更新记忆
  await memorySystem.updateMemory(memoryId, {
    content: "用户偏好使用React 18进行前端开发，特别喜欢函数式组件、Hooks和Suspense",
    tags: ["react", "frontend", "hooks", "functional-components", "suspense", "react18"]
  });
  console.log('✅ 记忆已更新');
}

// ==================== 模块化使用示例 ====================

/**
 * 模块化使用示例 - 单独使用各个管理器
 */
async function modularUsageExample() {
  console.log('\n=== 模块化使用示例 ===');
  
  // 1. 规则管理器使用
  const ruleManager = new RuleManager();
  await ruleManager.initialize();
  
  const rules = await ruleManager.loadRules();
  console.log('✅ 规则加载完成，个人规则数:', rules.personal?.length || 0);
  
  // 2. 知识图谱管理器使用
  const knowledgeGraph = new KnowledgeGraphManager();
  await knowledgeGraph.initialize();
  
  // 添加实体
  const reactEntityId = await knowledgeGraph.addEntity({
    name: "React",
    type: "Technology",
    properties: {
      version: "18.2.0",
      category: "Frontend Framework",
      maintainer: "Meta"
    }
  });
  
  const userEntityId = await knowledgeGraph.addEntity({
    name: "Developer_001",
    type: "Person",
    properties: {
      role: "Frontend Developer",
      experience: "5 years"
    }
  });
  
  // 添加关系
  await knowledgeGraph.addRelationship({
    fromId: userEntityId,
    toId: reactEntityId,
    type: "uses",
    properties: {
      proficiency: "expert",
      since: "2019"
    }
  });
  
  console.log('✅ 知识图谱实体和关系已创建');
  
  // 3. 记忆检索管理器使用
  const memoryRetrieval = new MemoryRetrievalManager();
  await memoryRetrieval.initialize();
  
  const similarity = await memoryRetrieval.calculateSimilarity(
    "React开发经验",
    "前端框架使用经验"
  );
  console.log('✅ 文本相似度:', similarity);
}

// ==================== React项目集成示例 ====================

/**
 * React项目集成示例
 */

// React Hook示例
import { useEffect, useState, useCallback } from 'react';

export function useMemorySystem() {
  const [memorySystem, setMemorySystem] = useState<LongTermMemorySystem | null>(null);
  const [isInitialized, setIsInitialized] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const initMemorySystem = async () => {
      try {
        const system = new LongTermMemorySystem();
        await system.initialize();
        setMemorySystem(system);
        setIsInitialized(true);
      } catch (err) {
        setError(err instanceof Error ? err.message : '初始化失败');
      }
    };

    initMemorySystem();
  }, []);

  const storeMemory = useCallback(async (memory: Omit<Memory, 'id' | 'createdAt' | 'updatedAt'>) => {
    if (!memorySystem) throw new Error('记忆系统未初始化');
    return await memorySystem.storeMemory(memory);
  }, [memorySystem]);

  const retrieveMemories = useCallback(async (query: RetrievalQuery) => {
    if (!memorySystem) throw new Error('记忆系统未初始化');
    return await memorySystem.retrieveMemories(query);
  }, [memorySystem]);

  return {
    memorySystem,
    isInitialized,
    error,
    storeMemory,
    retrieveMemories
  };
}

// React组件示例
interface MemoryComponentProps {
  userId: string;
}

export function MemoryComponent({ userId }: MemoryComponentProps) {
  const { memorySystem, isInitialized, error, storeMemory, retrieveMemories } = useMemorySystem();
  const [memories, setMemories] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const handleStoreUserAction = async (action: string) => {
    try {
      setLoading(true);
      await storeMemory({
        content: `用户 ${userId} 执行了操作: ${action}`,
        type: 'user_action',
        tags: ['user', 'action', userId],
        metadata: {
          userId,
          timestamp: new Date().toISOString(),
          source: 'ui_interaction'
        }
      });
      
      // 刷新记忆列表
      await loadUserMemories();
    } catch (err) {
      console.error('存储记忆失败:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadUserMemories = async () => {
    try {
      const results = await retrieveMemories({
        query: `用户 ${userId} 的操作记录`,
        tags: [userId],
        limit: 10,
        threshold: 0.6
      });
      setMemories(results);
    } catch (err) {
      console.error('加载记忆失败:', err);
    }
  };

  useEffect(() => {
    if (isInitialized) {
      loadUserMemories();
    }
  }, [isInitialized, userId]);

  if (error) {
    return <div className="error">记忆系统错误: {error}</div>;
  }

  if (!isInitialized) {
    return <div className="loading">正在初始化记忆系统...</div>;
  }

  return (
    <div className="memory-component">
      <h3>用户记忆管理</h3>
      
      <div className="actions">
        <button 
          onClick={() => handleStoreUserAction('查看项目列表')}
          disabled={loading}
        >
          记录: 查看项目列表
        </button>
        <button 
          onClick={() => handleStoreUserAction('创建新项目')}
          disabled={loading}
        >
          记录: 创建新项目
        </button>
      </div>

      <div className="memories">
        <h4>历史记忆 ({memories.length})</h4>
        {memories.map((memory, index) => (
          <div key={index} className="memory-item">
            <p>{memory.content}</p>
            <small>
              相似度: {memory.similarity?.toFixed(2)} | 
              标签: {memory.tags?.join(', ')} |
              时间: {new Date(memory.createdAt).toLocaleString()}
            </small>
          </div>
        ))}
      </div>
    </div>
  );
}

// ==================== Node.js服务端集成示例 ====================

/**
 * Node.js Express服务端集成示例
 */
import express from 'express';

class MemoryService {
  private memorySystem: LongTermMemorySystem;
  private initialized = false;

  constructor() {
    this.memorySystem = new LongTermMemorySystem();
  }

  async initialize() {
    if (!this.initialized) {
      await this.memorySystem.initialize();
      this.initialized = true;
      console.log('✅ 记忆服务初始化完成');
    }
  }

  async storeUserPreference(userId: string, preference: string, category: string) {
    await this.ensureInitialized();
    
    return await this.memorySystem.storeMemory({
      content: preference,
      type: 'preference',
      tags: ['user', 'preference', userId, category],
      metadata: {
        userId,
        category,
        source: 'api',
        timestamp: new Date().toISOString()
      }
    });
  }

  async getUserContext(userId: string, query: string) {
    await this.ensureInitialized();
    
    const memories = await this.memorySystem.retrieveMemories({
      query,
      tags: [userId],
      limit: 10,
      threshold: 0.7,
      includeMetadata: true
    });

    const context = await this.memorySystem.getEnhancementContext({
      query,
      includeRules: true,
      includeMemories: true,
      maxMemories: 5
    });

    return {
      memories,
      context,
      userProfile: {
        userId,
        memoryCount: memories.length,
        lastActivity: new Date().toISOString()
      }
    };
  }

  private async ensureInitialized() {
    if (!this.initialized) {
      await this.initialize();
    }
  }
}

// Express路由示例
export function createMemoryRoutes() {
  const router = express.Router();
  const memoryService = new MemoryService();

  // 初始化服务
  router.use(async (req, res, next) => {
    await memoryService.initialize();
    next();
  });

  // 存储用户偏好
  router.post('/users/:userId/preferences', async (req, res) => {
    try {
      const { userId } = req.params;
      const { preference, category } = req.body;
      
      const memoryId = await memoryService.storeUserPreference(userId, preference, category);
      
      res.json({
        success: true,
        memoryId,
        message: '用户偏好已存储'
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        error: error instanceof Error ? error.message : '存储失败'
      });
    }
  });

  // 获取用户上下文
  router.get('/users/:userId/context', async (req, res) => {
    try {
      const { userId } = req.params;
      const { query = '用户偏好和历史' } = req.query;
      
      const context = await memoryService.getUserContext(userId, query as string);
      
      res.json({
        success: true,
        data: context
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        error: error instanceof Error ? error.message : '获取上下文失败'
      });
    }
  });

  return router;
}

// ==================== 高级使用示例 ====================

/**
 * 高级使用示例 - 自定义配置和扩展
 */
async function advancedUsageExample() {
  console.log('\n=== 高级使用示例 ===');
  
  // 1. 自定义配置
  const customConfig = {
    rules: {
      personalRulesPath: './config/my-personal-rules.yaml',
      projectRulesPath: './config/my-project-rules.yaml'
    },
    knowledgeGraph: {
      maxEntities: 10000,
      maxRelationships: 50000
    },
    memory: {
      maxMemories: 5000,
      defaultThreshold: 0.8
    },
    performance: {
      enableMonitoring: true,
      logLevel: 'info'
    }
  };

  const memorySystem = new LongTermMemorySystem('./config/custom-config.json');
  await memorySystem.initialize();

  // 2. 批量操作
  const batchMemories = [
    {
      content: "用户喜欢使用TypeScript",
      type: "preference" as const,
      tags: ["typescript", "language"]
    },
    {
      content: "项目使用微服务架构",
      type: "architecture" as const,
      tags: ["microservices", "architecture"]
    },
    {
      content: "团队采用敏捷开发方法",
      type: "methodology" as const,
      tags: ["agile", "methodology"]
    }
  ];

  const memoryIds = await Promise.all(
    batchMemories.map(memory => memorySystem.storeMemory(memory))
  );
  console.log('✅ 批量存储完成，记忆IDs:', memoryIds);

  // 3. 复杂查询
  const complexQuery = {
    query: "开发相关的偏好和架构决策",
    tags: ["typescript", "architecture"],
    limit: 10,
    threshold: 0.6,
    includeMetadata: true,
    sortBy: "relevance" as const,
    filters: {
      type: ["preference", "architecture"],
      dateRange: {
        start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), // 30天前
        end: new Date()
      }
    }
  };

  const complexResults = await memorySystem.retrieveMemories(complexQuery);
  console.log('✅ 复杂查询结果:', complexResults.length, '条');

  // 4. 性能监控
  const performanceMonitor = memorySystem.getPerformanceMonitor();
  const stats = performanceMonitor.getStats();
  console.log('✅ 性能统计:', {
    totalOperations: stats.totalOperations,
    averageResponseTime: stats.averageResponseTime,
    memoryUsage: stats.memoryUsage
  });
}

// ==================== 主函数 ====================

async function main() {
  try {
    await basicUsageExample();
    await modularUsageExample();
    await advancedUsageExample();
    
    console.log('\n🎉 所有示例执行完成！');
  } catch (error) {
    console.error('❌ 示例执行失败:', error);
  }
}

// 如果直接运行此文件，则执行示例
if (require.main === module) {
  main();
}

// 导出示例函数供其他模块使用
export {
  basicUsageExample,
  modularUsageExample,
  advancedUsageExample,
  useMemorySystem,
  MemoryComponent,
  MemoryService,
  createMemoryRoutes
};