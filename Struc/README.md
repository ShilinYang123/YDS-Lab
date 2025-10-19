# 组织架构目录

本目录包含 YDS-Lab 的完整组织架构和智能体系统。

## 目录结构

### 🤖 Agents - 智能体定义
包含各部门和角色的智能体配置：
- `dev-team/` - 开发团队智能体（架构师、开发者、测试员等）
- `finance_director/` - 财务总监智能体
- `general_manager/` - 总经理智能体
- `marketing_director/` - 市场总监智能体
- `planning_director/` - 规划总监智能体
- `resource_admin/` - 资源管理员智能体

每个智能体包含：
- `define.py` - 智能体定义和配置
- `prompt.py` - 提示词模板
- `tools.py` - 专用工具集

### 🏢 部门目录
各部门的工作目录（随业务发展逐步填充）：
- `DevTeam/` - 开发团队工作区
- `FinanceDept/` - 财务部门工作区
- `MarketingDept/` - 市场部门工作区
- `PlanningDept/` - 规划部门工作区
- `ResourceAdminDept/` - 资源管理部门工作区

### 📋 GeneralOffice - 综合办公室
- `Docs/` - 组织文档和流程
- `config/` - 办公配置
- `meetings/` - 会议记录
- `logs/` - 统一日志管理

## 使用说明

1. **智能体系统**: 通过 Agents 目录中的配置启动对应角色的AI助手
2. **部门协作**: 各部门目录用于存放部门特定的工作文件和资源
3. **文档管理**: 重要文档和流程规范统一存放在 GeneralOffice/Docs
4. **日志追踪**: 所有系统和工作日志集中在 GeneralOffice/logs

## 扩展指南

- 新增部门：在对应部门目录下创建工作结构
- 新增智能体：参考现有智能体结构创建新的角色定义
- 文档更新：遵循既定的文档分类和命名规范