/**
 * 基础类型定义
 * 定义项目中使用的核心数据结构和接口
 */

// 基础实体类型
export interface BaseEntity {
  id: string;
  name: string;
  type: string;
  createdAt: Date;
  updatedAt: Date;
  metadata?: Record<string, any>;
}

// 规则相关类型
export interface Rule {
  id: string;
  name: string;
  description: string;
  category: RuleCategory;
  priority: number;
  conditions: RuleCondition[];
  actions: RuleAction[];
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
  metadata?: Record<string, any>;
}

export enum RuleCategory {
  PERSONAL = 'personal',
  PROJECT = 'project',
  TECHNICAL = 'technical',
  QUALITY = 'quality',
  SECURITY = 'security'
}

export interface RuleCondition {
  field: string;
  operator: ConditionOperator;
  value: any;
  logicalOperator?: LogicalOperator;
}

export enum ConditionOperator {
  EQUALS = 'equals',
  NOT_EQUALS = 'not_equals',
  CONTAINS = 'contains',
  NOT_CONTAINS = 'not_contains',
  GREATER_THAN = 'greater_than',
  LESS_THAN = 'less_than',
  GREATER_EQUAL = 'greater_equal',
  LESS_EQUAL = 'less_equal',
  STARTS_WITH = 'starts_with',
  ENDS_WITH = 'ends_with',
  IN = 'in',
  NOT_IN = 'not_in',
  REGEX_MATCH = 'regex_match',
  REGEX = 'regex',
  EXISTS = 'exists',
  NOT_EXISTS = 'not_exists'
}

export enum LogicalOperator {
  AND = 'and',
  OR = 'or',
  NOT = 'not'
}

export interface RuleAction {
  type: ActionType;
  parameters: Record<string, any>;
  priority: number;
}

export enum ActionType {
  LOG = 'log',
  NOTIFY = 'notify',
  MODIFY = 'modify',
  BLOCK = 'block',
  ENHANCE = 'enhance',
  STORE_MEMORY = 'store_memory'
}

// 规则上下文类型（与规则引擎中的 RuleContext 保持结构一致，便于在类型层复用）
export interface RuleContext {
  [key: string]: any;
}

// 知识图谱相关类型
export interface KnowledgeNode {
  id: string;
  label: string;
  // 允许任意字符串类型以兼容测试中使用的 'topic' 等自定义类型，同时保留 NodeType 枚举供推荐使用
  type: string;
  description?: string;
  // 兼容测试使用的 content 字段
  content?: string;
  // 放宽类型为 any，避免 TS4111（索引签名属性需使用 ['key'] 访问）对测试的影响
  properties: any;
  tags?: string[];
  // 兼容测试中使用的字段
  metadata?: any;
  createdAt: Date;
  updatedAt?: Date;
}

export interface KnowledgeEdge {
  id: string;
  sourceId: string;
  targetId: string;
  // 兼容测试：使用 type 作为关系类型的主要字段
  type: string;
  // 旧版字段保留为可选，避免破坏已有逻辑
  relationship?: string;
  weight: number;
  properties: any;
  // 兼容测试中使用的字段
  label?: string;
  metadata?: any;
  createdAt: Date;
  updatedAt: Date;
}

export enum NodeType {
  CONCEPT = 'concept',
  ENTITY = 'entity',
  EVENT = 'event',
  PERSON = 'person',
  PROJECT = 'project',
  TASK = 'task',
  RULE = 'rule',
  MEMORY = 'memory',
  USER = 'user',
  DOMAIN = 'domain',
  SESSION = 'session'
}

export interface AnalysisResult {
  insights: string[];
  patterns: string[];
  recommendations: string[];
  confidence: number;
  metadata?: Record<string, any>;
}

export enum EdgeType {
  RELATES_TO = 'relates_to',
  BELONGS_TO = 'belongs_to',
  PART_OF = 'part_of',
  CATEGORIZED_AS = 'categorized_as',
  SIMILAR_TO = 'similar_to',
  DERIVED_FROM = 'derived_from'
}

// 记忆相关类型
export interface Memory {
  id: string;
  content: string;
  summary?: string;
  type: MemoryType;
  importance: number;
  // 放宽为可选以兼容单元测试中未提供 tags/context 的场景
  tags?: string[];
  context?: MemoryContext;
  embeddings?: number[];
  knowledgeLinks?: string[];
  metadata?: Record<string, any>;
  createdAt: Date;
  updatedAt?: Date;
  lastAccessedAt?: Date;
  accessCount?: number;
  expiresAt?: Date;
  // 记忆整合相关属性
  consolidated?: boolean;
  consolidatedInto?: string;
  consolidatedFrom?: string[];
}

export enum MemoryType {
  SHORT_TERM = 'short_term',
  LONG_TERM = 'long_term',
  WORKING = 'working',
  EPISODIC = 'episodic',
  SEMANTIC = 'semantic',
  PROCEDURAL = 'procedural',
  CONSOLIDATED = 'consolidated'
}

export interface MemoryContext {
  sessionId?: string;
  userId?: string;
  projectId?: string;
  taskId?: string;
  domain?: string;
  task?: string;
  environment?: Record<string, any>;
  [key: string]: any; // 允许动态属性访问
}

// 智能体相关类型
export interface Agent {
  id: string;
  name: string;
  type: AgentType;
  capabilities: string[];
  configuration: AgentConfiguration;
  status: AgentStatus;
  createdAt: Date;
  lastActiveAt: Date;
  lastUpdated?: Date;
  memory?: {
    episodic: Memory[];
    semantic: Memory[];
    procedural: Memory[];
    working: Memory[];
  };
}

export enum AgentType {
  RULE_PROCESSOR = 'rule_processor',
  MEMORY_MANAGER = 'memory_manager',
  KNOWLEDGE_CURATOR = 'knowledge_curator',
  TASK_EXECUTOR = 'task_executor',
  PERFORMANCE_MONITOR = 'performance_monitor'
}

export interface AgentConfiguration {
  maxMemorySize: number;
  processingTimeout: number;
  retryAttempts: number;
  logLevel: LogLevel;
  customSettings: Record<string, any>;
  learnedPatterns?: string[];
  currentContext?: Record<string, any>;
  workflows?: string[];
  knowledgeBase?: string[];
  strategies?: string[];
}

export enum AgentStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  PROCESSING = 'processing',
  ERROR = 'error',
  MAINTENANCE = 'maintenance',
  ENHANCED = 'enhanced'
}

export enum LogLevel {
  DEBUG = 'debug',
  INFO = 'info',
  WARN = 'warn',
  ERROR = 'error',
  FATAL = 'fatal'
}

// 性能监控类型
export interface PerformanceMetrics {
  timestamp: Date;
  memoryUsage: MemoryUsage;
  processingTime: number;
  throughput: number;
  errorRate: number;
  activeConnections: number;
}

export interface MemoryUsage {
  used: number;
  total: number;
  percentage: number;
}

// 配置相关类型
export interface SystemConfiguration {
  database: DatabaseConfig;
  cache: CacheConfig;
  logging: LoggingConfig;
  security: SecurityConfig;
  performance: PerformanceConfig;
}

export interface DatabaseConfig {
  type: 'memory' | 'file' | 'sqlite' | 'postgresql';
  connectionString?: string;
  maxConnections: number;
  timeout: number;
}

export interface CacheConfig {
  enabled: boolean;
  maxSize: number;
  ttl: number;
  strategy: 'lru' | 'fifo' | 'lfu';
  maxMemory?: number;
  defaultTTL?: number;
  cleanupInterval?: number;
  enablePersistence?: boolean;
  persistenceFile?: string;
  compressionEnabled?: boolean;
}

export interface LoggingConfig {
  level: LogLevel;
  format: 'json' | 'text';
  destination: 'console' | 'file' | 'both';
  maxFileSize: number;
  maxFiles: number;
}

export interface SecurityConfig {
  encryption: {
    enabled: boolean;
    algorithm: string;
    keySize: number;
  };
  authentication: {
    required: boolean;
    tokenExpiry: number;
  };
}

export interface PerformanceConfig {
  maxConcurrentOperations?: number;
  batchSize?: number;
  cacheEnabled?: boolean;
  compressionEnabled?: boolean;
  historySize: number;
  enableCPUMonitoring: boolean;
  enableMemoryMonitoring: boolean;
  enableNetworkMonitoring: boolean;
  monitoringInterval: number;
  alertThresholds: {
    responseTime: number;
    cpuUsage: number;
    memoryUsage: number;
  };
}

// API 相关类型
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: ApiError;
  timestamp: Date;
  requestId: string;
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, any>;
}

// 记忆检索相关类型
export interface RetrievalQuery {
  text?: string;
  type?: MemoryType;
  context?: Partial<MemoryContext>;
  tags?: string[];
  timeRange?: {
    start?: Date;
    end?: Date;
  };
  importance?: {
    min?: number;
    max?: number;
  };
  limit?: number;
  includeRelated?: boolean;
  semanticSearch?: boolean;
  sortBy?: 'relevance' | 'importance' | 'recency';
  filters?: Record<string, any>;
}

export interface RetrievalResult {
  memories: Memory[];
  relatedNodes: KnowledgeNode[];
  confidence: number;
  searchTime: number;
  totalResults: number;
}

// 智能体增强相关类型
export interface EnhancementContext {
  currentTask?: string;
  userInput?: string;
  sessionId?: string;
  domain?: string;
  priority?: number;
}

export interface EnhancementResult {
  enhancedAgent: Agent;
  appliedMemories: Memory[];
  relatedKnowledge: KnowledgeNode[];
  performanceImprovement: number;
  enhancementTime: number;
}

// 事件相关类型
export interface SystemEvent {
  id: string;
  type: EventType;
  source: string;
  data: Record<string, any>;
  timestamp: Date;
  severity: EventSeverity;
}

export enum EventType {
  RULE_TRIGGERED = 'rule_triggered',
  MEMORY_CREATED = 'memory_created',
  MEMORY_ACCESSED = 'memory_accessed',
  KNOWLEDGE_UPDATED = 'knowledge_updated',
  AGENT_STATUS_CHANGED = 'agent_status_changed',
  PERFORMANCE_ALERT = 'performance_alert',
  ERROR_OCCURRED = 'error_occurred'
}

export enum EventSeverity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

// 查询选项类型
export interface QueryOptions {
  filters?: Record<string, any>;
  limit?: number;
  offset?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  includeProperties?: boolean;
  includeRelations?: boolean;
}


