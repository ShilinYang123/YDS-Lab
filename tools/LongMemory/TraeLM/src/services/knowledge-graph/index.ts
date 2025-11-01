/**
 * 知识图谱模块入口
 * 导出知识图谱和记忆管理的核心组件
 */

export { KnowledgeGraph } from './graph';
export { MemoryManager } from './memory';
export { KnowledgeGraphManager } from './manager';

// 导出类型定义
export type {
  KnowledgeGraphOptions,
  NodeSearchQuery,
  KnowledgeGraphStats,
  GraphExportData
} from './graph';

export type {
  MemoryManagerOptions,
  MemorySearchQuery,
  MemoryStats
} from './memory';

export type {
  KnowledgeGraphManagerOptions,
  GraphAnalysisResult,
  MemoryConsolidationResult,
  KnowledgeExtractionResult
} from './manager';