/**
 * 服务模块入口文件
 * 
 * @description 导出项目核心服务功能，包括规则服务、知识图谱服务和智能体服务
 * @author 高级软件专家
 */

// 规则系统服务
export {
  RuleEngine,
  RuleProcessor,
  RuleManager
} from './rule-system';

// 知识图谱记忆服务
export {
  KnowledgeGraph,
  MemoryManager,
  KnowledgeGraphManager
} from './knowledge-graph';

// 智能体增强服务
// export * from './agent-enhancement'; // 暂时注释掉，该模块不存在

// 记忆检索服务
export {
  MemoryRetriever,
  AgentEnhancer,
  MemoryRetrievalManager
} from './memory-retrieval';

export type {
  RetrievalStrategy,
  LearningPattern
} from './memory-retrieval';

// 导出所有类型定义
export type {
  // 规则系统类型
  Rule,
  RuleCondition,
  RuleAction,
  RuleCategory,
  // RuleContext, // 已在rule-system/engine.ts中定义
  
  // 知识图谱类型
  KnowledgeNode,
  KnowledgeEdge,
  Memory,
  MemoryType,
  MemoryContext,
  
  // 基础类型
  BaseEntity,
  Agent,
  AgentType,
  AgentStatus,
  PerformanceMetrics,
  SystemConfiguration,
  ApiResponse,
  ApiError,
  SystemEvent
} from '../types/base';