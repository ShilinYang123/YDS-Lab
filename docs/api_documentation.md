# API 文档

## 概述

YDS-Lab API 提供了一套完整的接口用于管理多智能体系统。

## 认证

所有API请求都需要包含认证信息。

## 端点

### 智能体管理

- `GET /api/agents` - 获取智能体列表
- `POST /api/agents` - 创建新智能体
- `GET /api/agents/{id}` - 获取智能体详情
- `PUT /api/agents/{id}` - 更新智能体
- `DELETE /api/agents/{id}` - 删除智能体

### 任务管理

- `GET /api/tasks` - 获取任务列表
- `POST /api/tasks` - 创建新任务
- `GET /api/tasks/{id}` - 获取任务详情
- `PUT /api/tasks/{id}` - 更新任务状态

## 错误处理

API使用标准的HTTP状态码表示请求结果。

---
*本文档由自动化工具生成*
