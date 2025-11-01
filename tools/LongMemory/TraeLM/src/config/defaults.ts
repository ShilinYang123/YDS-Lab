/**
 * 默认配置设置
 * 定义系统的默认配置参数
 */

import {
  SystemConfiguration,
  LogLevel,
  AgentConfiguration,
  AgentType,
  MemoryType,
  RuleCategory
} from '../types/base';

export const DEFAULT_SYSTEM_CONFIG: SystemConfiguration = {
  database: {
    type: 'memory',
    maxConnections: 10,
    timeout: 5000
  },
  cache: {
    enabled: true,
    maxSize: 1000,
    ttl: 3600000, // 1 hour
    strategy: 'lru'
  },
  logging: {
    level: LogLevel.INFO,
    format: 'json',
    destination: 'both',
    maxFileSize: 10485760, // 10MB
    maxFiles: 5
  },
  security: {
    encryption: {
      enabled: true,
      algorithm: 'aes-256-gcm',
      keySize: 256
    },
    authentication: {
      required: false,
      tokenExpiry: 86400000 // 24 hours
    }
  },
  performance: {
    maxConcurrentOperations: 100,
    batchSize: 50,
    cacheEnabled: true,
    compressionEnabled: true,
    historySize: 1000,
    enableCPUMonitoring: true,
    enableMemoryMonitoring: true,
    enableNetworkMonitoring: true,
    monitoringInterval: 5000,
    alertThresholds: {
      responseTime: 5000,
      cpuUsage: 80,
      memoryUsage: 85
    }
  }
};

export const DEFAULT_AGENT_CONFIGS: Record<AgentType, AgentConfiguration> = {
  [AgentType.RULE_PROCESSOR]: {
    maxMemorySize: 100,
    processingTimeout: 5000,
    retryAttempts: 3,
    logLevel: LogLevel.INFO,
    customSettings: {
      batchSize: 10,
      priorityThreshold: 5
    }
  },
  [AgentType.MEMORY_MANAGER]: {
    maxMemorySize: 1000,
    processingTimeout: 10000,
    retryAttempts: 2,
    logLevel: LogLevel.INFO,
    customSettings: {
      compressionEnabled: true,
      autoCleanup: true,
      cleanupInterval: 3600000 // 1 hour
    }
  },
  [AgentType.KNOWLEDGE_CURATOR]: {
    maxMemorySize: 500,
    processingTimeout: 15000,
    retryAttempts: 3,
    logLevel: LogLevel.INFO,
    customSettings: {
      maxNodeConnections: 50,
      relationshipWeightThreshold: 0.1
    }
  },
  [AgentType.TASK_EXECUTOR]: {
    maxMemorySize: 200,
    processingTimeout: 30000,
    retryAttempts: 5,
    logLevel: LogLevel.INFO,
    customSettings: {
      maxConcurrentTasks: 5,
      taskTimeout: 60000
    }
  },
  [AgentType.PERFORMANCE_MONITOR]: {
    maxMemorySize: 50,
    processingTimeout: 2000,
    retryAttempts: 1,
    logLevel: LogLevel.WARN,
    customSettings: {
      monitoringInterval: 30000, // 30 seconds
      alertThresholds: {
        memoryUsage: 80,
        errorRate: 5,
        responseTime: 1000
      }
    }
  }
};

export const DEFAULT_MEMORY_SETTINGS = {
  [MemoryType.SHORT_TERM]: {
    maxSize: 100,
    ttl: 3600000, // 1 hour
    importance: 1
  },
  [MemoryType.LONG_TERM]: {
    maxSize: 10000,
    ttl: 0, // permanent
    importance: 5
  },
  [MemoryType.WORKING]: {
    maxSize: 50,
    ttl: 1800000, // 30 minutes
    importance: 3
  },
  [MemoryType.EPISODIC]: {
    maxSize: 1000,
    ttl: 86400000, // 24 hours
    importance: 4
  },
  [MemoryType.SEMANTIC]: {
    maxSize: 5000,
    ttl: 0, // permanent
    importance: 5
  },
  [MemoryType.PROCEDURAL]: {
    maxSize: 500,
    ttl: 0, // permanent
    importance: 4
  }
};

export const DEFAULT_RULE_PRIORITIES: Record<RuleCategory, number> = {
  [RuleCategory.SECURITY]: 10,
  [RuleCategory.QUALITY]: 8,
  [RuleCategory.TECHNICAL]: 6,
  [RuleCategory.PROJECT]: 4,
  [RuleCategory.PERSONAL]: 2
};

export const DEFAULT_PERFORMANCE_THRESHOLDS = {
  memoryUsage: {
    warning: 70,
    critical: 90
  },
  responseTime: {
    warning: 1000,
    critical: 5000
  },
  errorRate: {
    warning: 1,
    critical: 5
  },
  throughput: {
    minimum: 10,
    target: 100
  }
};

export const DEFAULT_KNOWLEDGE_GRAPH_SETTINGS = {
  maxNodes: 10000,
  maxEdges: 50000,
  defaultRelationshipWeight: 1.0,
  minRelationshipWeight: 0.1,
  maxRelationshipWeight: 10.0,
  nodeTypes: {
    concept: { color: '#4CAF50', size: 10 },
    entity: { color: '#2196F3', size: 8 },
    event: { color: '#FF9800', size: 6 },
    person: { color: '#9C27B0', size: 12 },
    project: { color: '#F44336', size: 15 },
    task: { color: '#607D8B', size: 8 },
    rule: { color: '#795548', size: 10 },
    memory: { color: '#E91E63', size: 6 }
  }
};

export const DEFAULT_FILE_PATHS = {
  rulesDirectory: '.trae/rules',
  memoryDirectory: '.trae/memory',
  knowledgeGraphFile: '.trae/knowledge-graph.json',
  configFile: '.trae/config.json',
  logsDirectory: '.trae/logs',
  backupDirectory: '.trae/backups'
};

export const DEFAULT_API_SETTINGS = {
  timeout: 30000,
  retryAttempts: 3,
  retryDelay: 1000,
  maxRequestSize: 10485760, // 10MB
  rateLimiting: {
    enabled: true,
    maxRequests: 100,
    windowMs: 60000 // 1 minute
  }
};

export const DEFAULT_VALIDATION_RULES = {
  memory: {
    minContentLength: 1,
    maxContentLength: 10000,
    maxTags: 10,
    importanceRange: [1, 10]
  },
  rule: {
    minNameLength: 3,
    maxNameLength: 100,
    maxConditions: 20,
    maxActions: 10,
    priorityRange: [1, 10]
  },
  knowledgeNode: {
    minLabelLength: 1,
    maxLabelLength: 200,
    maxProperties: 50
  }
};