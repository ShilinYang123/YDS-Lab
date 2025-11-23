# 智能会议室系统技术架构文档

## 1. 架构概述

本系统采用前后端分离架构，支持本地部署，集成AI智能体协作、实时通信、文档管理和决策追溯功能。

### 1.1 技术栈选择
- **后端**: Node.js + Express.js + TypeScript
- **数据库**: PostgreSQL (主数据库) + Redis (缓存)
- **实时通信**: Socket.io
- **身份认证**: JWT (RS256)
- **文件存储**: 本地文件系统
- **AI服务**: Ollama (LLM) + Shimmy (STT/TTS)

### 1.2 架构原则
- 高内聚、低耦合
- 微服务化设计
- 安全性优先
- 可扩展性设计
- 本地部署优化

## 2. 数据库设计

### 2.1 数据库架构
```sql
-- 用户表
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('CEO', 'MeetingSecretary', 'FinanceDirector', 'TechRepresentative', 'Observer')),
    display_name VARCHAR(100),
    avatar_url VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 会议室表
CREATE TABLE meeting_rooms (
    id SERIAL PRIMARY KEY,
    room_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(10) NOT NULL CHECK (type IN ('A', 'B', 'C')),
    status VARCHAR(20) DEFAULT 'active',
    creator_id INTEGER REFERENCES users(id),
    scheduled_start TIMESTAMP,
    scheduled_end TIMESTAMP,
    actual_start TIMESTAMP,
    actual_end TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 会议议程表
CREATE TABLE meeting_agendas (
    id SERIAL PRIMARY KEY,
    room_id INTEGER REFERENCES meeting_rooms(id),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    priority INTEGER DEFAULT 1,
    estimated_duration INTEGER, -- 分钟
    order_index INTEGER,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 消息表
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    message_id VARCHAR(50) UNIQUE NOT NULL,
    room_id INTEGER REFERENCES meeting_rooms(id),
    channel VARCHAR(20) NOT NULL CHECK (channel IN ('text', 'voice', 'docs', 'vote')),
    event_type VARCHAR(50) NOT NULL,
    sender_id INTEGER REFERENCES users(id),
    content TEXT,
    file_path VARCHAR(500),
    file_name VARCHAR(255),
    file_size BIGINT,
    file_hash VARCHAR(64),
    parent_id INTEGER REFERENCES messages(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 投票表
CREATE TABLE votes (
    id SERIAL PRIMARY KEY,
    vote_id VARCHAR(50) UNIQUE NOT NULL,
    room_id INTEGER REFERENCES meeting_rooms(id),
    proposal_title VARCHAR(200) NOT NULL,
    proposal_description TEXT,
    options JSONB NOT NULL,
    is_anonymous BOOLEAN DEFAULT false,
    quorum DECIMAL(3,2) DEFAULT 0.6,
    expires_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active',
    creator_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 投票记录表
CREATE TABLE vote_records (
    id SERIAL PRIMARY KEY,
    vote_id INTEGER REFERENCES votes(id),
    user_id INTEGER REFERENCES users(id),
    selected_option VARCHAR(100),
    weight INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vote_id, user_id)
);

-- 决策追溯表
CREATE TABLE decisions (
    id SERIAL PRIMARY KEY,
    decision_id VARCHAR(50) UNIQUE NOT NULL,
    room_id INTEGER REFERENCES meeting_rooms(id),
    topic VARCHAR(200) NOT NULL,
    options JSONB,
    final_decision VARCHAR(100),
    reasoning TEXT,
    discussion_process JSONB,
    vote_result JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 行动项表
CREATE TABLE action_items (
    id SERIAL PRIMARY KEY,
    action_id VARCHAR(50) UNIQUE NOT NULL,
    decision_id INTEGER REFERENCES decisions(id),
    room_id INTEGER REFERENCES meeting_rooms(id),
    task_description TEXT NOT NULL,
    assignee_id INTEGER REFERENCES users(id),
    deadline TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 审计日志表
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_path VARCHAR(500),
    result VARCHAR(20),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_messages_room_id ON messages(room_id);
CREATE INDEX idx_messages_channel ON messages(channel);
CREATE INDEX idx_messages_created_at ON messages(created_at);
CREATE INDEX idx_votes_room_id ON votes(room_id);
CREATE INDEX idx_vote_records_vote_id ON vote_records(vote_id);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
```

### 2.2 Redis缓存设计
```
# 会话缓存
session:{token} -> user_data (TTL: 24h)

# 房间状态缓存
room:{room_id}:status -> room_status (TTL: 1h)
room:{room_id}:participants -> participant_list (TTL: 5min)

# 消息缓存
room:{room_id}:messages:latest -> latest_messages (TTL: 30min)
room:{room_id}:messages:count -> message_count (TTL: 5min)

# 投票缓存
vote:{vote_id}:status -> vote_status (TTL: 5min)
vote:{vote_id}:results -> vote_results (TTL: 5min)

# 系统监控缓存
system:metrics:{metric_name} -> metric_value (TTL: 1min)
system:health -> health_status (TTL: 30s)
```

## 3. API设计

### 3.1 REST API端点
```
# 认证
POST /api/auth/login
POST /api/auth/logout
POST /api/auth/refresh

# 会议室管理
GET  /api/rooms
POST /api/rooms
GET  /api/rooms/:id
PUT  /api/rooms/:id
DELETE /api/rooms/:id

# 议程管理
GET  /api/rooms/:roomId/agendas
POST /api/rooms/:roomId/agendas
PUT  /api/rooms/:roomId/agendas/:id
DELETE /api/rooms/:roomId/agendas/:id

# 消息管理
GET  /api/rooms/:roomId/messages
POST /api/rooms/:roomId/messages
DELETE /api/rooms/:roomId/messages/:id

# 文档管理
POST /api/rooms/:roomId/documents
GET  /api/rooms/:roomId/documents
DELETE /api/rooms/:roomId/documents/:id

# 投票管理
POST /api/rooms/:roomId/votes
GET  /api/rooms/:roomId/votes
POST /api/votes/:voteId/cast
GET  /api/votes/:voteId/results

# 决策追溯
GET  /api/rooms/:roomId/decisions
GET  /api/decisions/:id

# 行动项
GET  /api/rooms/:roomId/action-items
PUT  /api/action-items/:id

# 系统监控
GET /api/system/health
GET /api/system/metrics
```

### 3.2 WebSocket事件
```javascript
// 客户端发送事件
'join_room'
'leave_room'
'send_message'
'typing_start'
'typing_stop'
'vote_cast'
'document_share'

// 服务端推送事件
'user_joined'
'user_left'
'message_received'
'user_typing'
'vote_updated'
'document_shared'
'room_status_changed'
'system_notice'
```

## 4. 安全设计

### 4.1 身份认证
- JWT令牌使用RS256算法签名
- 令牌有效期：访问令牌2小时，刷新令牌7天
- 支持令牌撤销和刷新机制

### 4.2 权限控制
- RBAC基于角色的访问控制
- ACL基于资源的细粒度权限控制
- 路径白名单/黑名单机制

### 4.3 数据加密
- 敏感数据使用AES-256加密
- 密码使用bcrypt哈希（salt rounds: 12）
- 传输层使用HTTPS

### 4.4 审计日志
- 所有关键操作记录审计日志
- 日志包含用户、时间、操作、资源、结果等信息
- 日志保留180天，按月归档

## 5. 性能优化

### 5.1 数据库优化
- 合理的索引设计
- 查询优化和分页处理
- 连接池配置

### 5.2 缓存策略
- Redis缓存热点数据
- 客户端缓存静态资源
- CDN加速（如需要）

### 5.3 前端优化
- 组件懒加载
- 虚拟滚动处理大量消息
- WebSocket连接池管理

## 6. 监控和运维

### 6.1 监控指标
- 系统指标：CPU、内存、磁盘、网络
- 应用指标：响应时间、错误率、并发数
- 业务指标：会议数量、消息量、投票参与率

### 6.2 告警机制
- 系统异常告警
- 性能阈值告警
- 业务指标异常告警

### 6.3 备份策略
- 数据库每日增量备份
- 每周全量备份
- 备份保留30天

## 7. 扩展性设计

### 7.1 水平扩展
- 无状态服务设计
- 负载均衡支持
- 数据库读写分离

### 7.2 微服务化
- 核心服务模块化
- 支持服务独立部署
- API版本管理

## 8. 部署架构

### 8.1 本地部署
```
┌─────────────────┐
│   Nginx/Apache  │
│   (反向代理)     │
└────────┬────────┘
         │
┌────────▼────────┐
│  Node.js应用    │
│  (Express.js)   │
└────────┬────────┘
         │
    ┌────┴────┐
    │        │
┌───▼───┐ ┌─▼───┐
│PostgreSQL│ │Redis│
└─────────┘ └───┘
```

### 8.2 服务配置
- Node.js：PM2进程管理
- PostgreSQL：主从复制（可选）
- Redis：主从配置（可选）
- Nginx：负载均衡和静态资源服务

## 9. 开发规范

### 9.1 代码规范
- TypeScript严格模式
- ESLint代码检查
- Prettier代码格式化
- 单元测试覆盖率≥80%

### 9.2 Git规范
- 分支管理：main/develop/feature分支模型
- 提交信息：遵循Conventional Commits规范
- Code Review：强制代码审查

### 9.3 文档规范
- API文档：OpenAPI/Swagger规范
- 代码注释：JSDoc标准
- 架构文档：保持更新

## 10. 风险评估和应对

### 10.1 技术风险
- **WebSocket连接管理**：使用成熟的Socket.io库
- **高并发处理**：合理的架构设计和性能测试
- **数据一致性**：事务处理和分布式锁

### 10.2 业务风险
- **权限控制复杂性**：细粒度的权限设计和测试
- **文档安全**：严格的路径控制和审计机制
- **AI服务稳定性**：本地服务的健康检查和降级策略

### 10.3 应对措施
- 完善的监控和告警系统
- 详细的错误处理和日志记录
- 定期的安全审计和性能测试
- 完善的备份和恢复机制