# 后端API项目结构文档

## 概述
后端API服务基于 Node.js + TypeScript + Express 构建，采用分层架构设计，提供RESTful API接口，支持数字员工系统的核心业务逻辑。

## 目录结构

```
api/
├── controllers/          # 控制器层
│   ├── auth.controller.ts      # 认证控制器
│   ├── user.controller.ts      # 用户控制器
│   ├── digitalEmployee.controller.ts  # 数字员工控制器
│   ├── task.controller.ts      # 任务控制器
│   ├── analytics.controller.ts # 分析控制器
│   ├── voice.controller.ts     # 语音控制器
│   └── file.controller.ts      # 文件控制器
├── models/               # 数据模型层
│   ├── User.ts           # 用户模型
│   ├── DigitalEmployee.ts # 数字员工模型
│   ├── Task.ts           # 任务模型
│   ├── Conversation.ts   # 对话模型
│   ├── Analytics.ts      # 分析数据模型
│   └── File.ts           # 文件模型
├── routes/               # 路由层
│   ├── index.ts          # 路由入口
│   ├── auth.routes.ts    # 认证路由
│   ├── user.routes.ts    # 用户路由
│   ├── digitalEmployee.routes.ts # 数字员工路由
│   ├── task.routes.ts    # 任务路由
│   ├── analytics.routes.ts # 分析路由
│   ├── voice.routes.ts   # 语音路由
│   └── file.routes.ts    # 文件路由
├── middleware/           # 中间件层
│   ├── auth.middleware.ts     # 认证中间件
│   ├── validation.middleware.ts # 验证中间件
│   ├── error.middleware.ts     # 错误处理中间件
│   ├── logger.middleware.ts    # 日志中间件
│   ├── rateLimit.middleware.ts # 限流中间件
│   └── cors.middleware.ts      # CORS中间件
├── services/            # 业务逻辑层
│   ├── auth.service.ts       # 认证服务
│   ├── user.service.ts       # 用户服务
│   ├── digitalEmployee.service.ts # 数字员工服务
│   ├── task.service.ts       # 任务服务
│   ├── analytics.service.ts  # 分析服务
│   ├── voice.service.ts      # 语音服务
│   ├── file.service.ts       # 文件服务
│   ├── ai.service.ts         # AI服务
│   └── notification.service.ts # 通知服务
├── config/              # 配置文件
│   ├── database.ts      # 数据库配置
│   ├── redis.ts         # Redis配置
│   ├── minio.ts         # MinIO配置
│   ├── jwt.ts           # JWT配置
│   ├── cors.ts          # CORS配置
│   ├── logger.ts        # 日志配置
│   └── swagger.ts       # Swagger配置
├── utils/               # 工具函数
│   ├── response.ts      # 响应工具
│   ├── validator.ts     # 验证工具
│   ├── encrypt.ts       # 加密工具
│   ├── date.ts          # 日期工具
│   ├── file.ts          # 文件工具
│   └── constants.ts     # 常量定义
├── types/               # TypeScript类型定义
│   ├── api.ts           # API相关类型
│   ├── models.ts        # 模型类型
│   ├── requests.ts      # 请求类型
│   └── responses.ts     # 响应类型
├── tests/               # 测试文件
│   ├── unit/            # 单元测试
│   ├── integration/     # 集成测试
│   └── e2e/             # 端到端测试
├── docs/                # API文档
│   ├── swagger.yaml     # Swagger文档
│   └── api.md           # API说明文档
├── logs/                # 日志文件
├── uploads/             # 上传文件临时存储
├── scripts/             # 脚本文件
│   ├── seed.ts          # 数据种子
│   └── migrate.ts       # 数据迁移
├── app.ts               # Express应用配置
├── server.ts            # 服务器入口
└── package.json         # 项目依赖配置
```

## 技术栈

### 核心依赖
- **Node.js**: JavaScript运行时
- **TypeScript**: 类型安全
- **Express**: Web框架
- **Supabase**: 数据库服务
- **Redis**: 缓存服务
- **MinIO**: 对象存储

### 中间件和工具
- **JWT**: 身份认证
- **Bcrypt**: 密码加密
- **Winston**: 日志管理
- **Joi**: 数据验证
- **Cors**: 跨域处理
- **Helmet**: 安全头
- **Compression**: 压缩中间件

### 开发工具
- **Nodemon**: 开发热重载
- **Jest**: 测试框架
- **Supertest**: API测试
- **ESLint**: 代码检查
- **Prettier**: 代码格式化

## 架构设计

### 分层架构
1. **路由层 (Routes)**: 定义API端点和请求路由
2. **控制器层 (Controllers)**: 处理HTTP请求和响应
3. **服务层 (Services)**: 实现业务逻辑
4. **模型层 (Models)**: 定义数据结构和数据库操作
5. **中间件层 (Middleware)**: 处理横切关注点

### 数据流
```
HTTP Request → Router → Middleware → Controller → Service → Model → Database
                    ↓
HTTP Response ← Controller ← Service ← Model ← Database
```

## API设计规范

### RESTful原则
- 使用HTTP动词 (GET, POST, PUT, DELETE)
- 资源导向的URL设计
- 状态码语义化
- 统一的响应格式

### 响应格式
```json
{
  "success": true,
  "data": {},
  "message": "操作成功",
  "code": 200
}
```

### 错误处理
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "参数验证失败",
    "details": {}
  }
}
```

## 环境配置

### 环境变量
```env
# 基础配置
NODE_ENV=development
PORT=3001
API_PREFIX=/api/v1

# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/digital_employee
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# Redis配置
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=

# MinIO配置
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_BUCKET=digital-employee

# JWT配置
JWT_SECRET=your-jwt-secret
JWT_EXPIRES_IN=7d

# AI服务配置
OPENAI_API_KEY=your-openai-key
AZURE_SPEECH_KEY=your-azure-speech-key
AZURE_SPEECH_REGION=your-region

# 文件上传配置
MAX_FILE_SIZE=10485760
UPLOAD_PATH=./uploads

# 日志配置
LOG_LEVEL=info
LOG_FILE=./logs/app.log
```

### 开发环境
```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 运行测试
npm run test

# 构建项目
npm run build
```

## 数据库设计

### 核心表结构
- **users**: 用户表
- **digital_employees**: 数字员工表
- **tasks**: 任务表
- **conversations**: 对话记录表
- **analytics**: 分析数据表
- **files**: 文件表

### 关系设计
- 用户与数字员工：一对多
- 数字员工与任务：一对多
- 数字员工与对话：一对多
- 任务与分析：一对一

## 安全措施

### 身份认证
- JWT Token认证
- Refresh Token机制
- 密码加密存储

### 访问控制
- 基于角色的权限控制(RBAC)
- API接口权限验证
- 资源访问权限控制

### 数据安全
- 敏感数据加密
- SQL注入防护
- XSS攻击防护
- CSRF防护

## 性能优化

### 缓存策略
- Redis缓存热点数据
- 数据库查询优化
- 接口响应缓存

### 并发处理
- 异步任务处理
- 消息队列机制
- 连接池管理

### 监控指标
- API响应时间
- 数据库查询性能
- 内存使用情况
- 错误率统计