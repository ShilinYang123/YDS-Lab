# 数字员工系统（基于 LatentSync）

## 项目简介

数字员工系统是一个基于 LatentSync 技术的智能数字人平台，旨在为企业和个人提供高度拟真的虚拟员工服务。通过先进的AI技术，实现自然语言交互、任务执行、数据分析和智能决策等功能。

### 核心目标
- 构建高度拟真的数字员工形象
- 实现自然流畅的语音交互
- 提供智能化的任务处理能力
- 支持多场景业务应用

## 技术栈

### 前端技术
- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **样式**: Tailwind CSS + Ant Design
- **状态管理**: Zustand
- **路由**: React Router v6
- **HTTP客户端**: Axios

### 后端技术
- **运行时**: Node.js + TypeScript
- **框架**: Express.js
- **数据库**: PostgreSQL (通过 Supabase)
- **缓存**: Redis
- **文件存储**: MinIO
- **AI服务**: OpenAI API / 其他LLM服务

### 基础设施
- **容器化**: Docker + Docker Compose
- **API网关**: Nginx
- **监控**: 日志收集与性能监控
- **部署**: 支持本地开发和云端部署

## 项目结构

```
digital-employee/
├── src/                    # 前端React应用
│   ├── components/          # 可复用组件
│   ├── pages/              # 页面组件
│   ├── hooks/              # 自定义Hooks
│   ├── services/           # API服务
│   ├── utils/              # 工具函数
│   ├── styles/             # 样式文件
│   └── assets/             # 静态资源
├── api/                    # 后端API服务
│   ├── controllers/        # 控制器
│   ├── models/            # 数据模型
│   ├── routes/            # 路由定义
│   ├── middleware/        # 中间件
│   ├── services/          # 业务逻辑
│   └── config/            # 配置文件
├── docker/                # Docker配置
├── docs/                  # 项目文档
├── scripts/               # 脚本文件
└── docker-compose.yml     # 服务编排
```

## 快速开始

### 环境要求
- Node.js >= 18.0.0
- Docker 和 Docker Compose
- Git

### 1. 克隆项目
```bash
git clone <repository-url>
cd digital-employee
```

### 2. 环境配置
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
vim .env
```

### 3. 启动基础设施服务
```bash
# 启动 PostgreSQL、Redis、MinIO
docker-compose up -d postgres redis minio
```

### 4. 安装依赖
```bash
# 安装前端依赖
cd src && npm install

# 安装后端依赖
cd ../api && npm install
```

### 5. 启动开发服务器
```bash
# 启动前端开发服务器（在src目录下）
npm run dev

# 启动后端API服务器（在api目录下）
npm run dev
```

### 6. 访问应用
- 前端应用: http://localhost:3000
- 后端API: http://localhost:3001
- API文档: http://localhost:3001/docs
- MinIO控制台: http://localhost:9001

## 开发指南

### 前端开发
1. **组件开发**: 遵循React组件化开发规范
2. **状态管理**: 使用Zustand进行全局状态管理
3. **API调用**: 通过services层统一处理API请求
4. **样式规范**: 使用Tailwind CSS + CSS Modules

### 后端开发
1. **API设计**: 遵循RESTful API设计原则
2. **数据库**: 使用Supabase进行数据操作
3. **错误处理**: 统一的错误处理中间件
4. **日志记录**: 使用Winston进行日志管理

### 代码规范
- 使用ESLint进行代码检查
- 使用Prettier进行代码格式化
- 提交前进行代码审查

## 部署指南

### 开发环境
```bash
# 使用docker-compose一键启动所有服务
docker-compose up -d
```

### 生产环境
```bash
# 构建生产镜像
docker-compose -f docker-compose.prod.yml up -d
```

## 功能模块

### 核心功能
- [ ] 数字员工创建与管理
- [ ] 语音交互系统
- [ ] 任务调度与执行
- [ ] 数据分析与报告
- [ ] 多模态交互支持

### 管理功能
- [ ] 用户权限管理
- [ ] 系统配置管理
- [ ] 日志审计功能
- [ ] 性能监控面板

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系方式

- 项目维护者: 雨俊
- 邮箱: yujun@example.com
- 项目主页: https://github.com/your-org/digital-employee

## 更新日志

### v1.0.0 (2025-01-15)
- ✨ 初始版本发布
- 🎉 基础架构搭建完成
- 🔧 前后端分离架构实现
- 📦 Docker容器化部署支持