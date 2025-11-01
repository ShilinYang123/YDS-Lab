# 组织架构目录

本目录包含 YDS-Lab 的完整组织架构和智能体系统。

## 目录结构

### 🤖 Agents - 智能体定义
包含各部门和角色的智能体配置：
- `dev-team/` - 开发团队智能体（架构师、开发者、测试员等）
- `finance_director/` - 财务总监智能体
- `ceo/` - 总经理（CEO）智能体
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

---

## 附录：模型路由与后端选择策略（Shimmy / Ollama）

为满足本地 LLM 的统一调用与自动选择需求，项目引入“模型路由与后端选择”能力：

- 详细说明文档（正式）：`Struc/GeneralOffice/Docs/LLM路由与后端选择（Shimmy-Ollama）使用说明.md`
- 基准测试输出：`Struc/GeneralOffice/logs/bench_local_llm.json`
- 路由偏好：`models/config/router_preference.json`（若未创建，请参考说明文档草案）
- 外部服务地址：`models/config/external_models.json`（Shimmy / Ollama 主机地址）
- 统一调用入口：`models/services/llm_router.py` → `route_chat(model, messages, ...)`
- 基准测试脚本：`tools/performance/performance_analyzer.py`（含健康预热与端点回退）

快速开始（示例）：
- 确认本地已启动：Shimmy（如 11435/11436），Ollama（11434）。
- 运行基准脚本并生成日志：
  ```powershell
  python tools\performance\performance_analyzer.py `
    --shimmy-url http://127.0.0.1:11436 `
    --shimmy-model qwen2-0_5b-instruct-q4_0 `
    --ollama-url http://127.0.0.1:11434 `
    --ollama-model qwen2:0.5b `
    --prompt "请用两句中文写一首秋天的短诗。" `
    --out "S:\\YDS-Lab\\Struc\\GeneralOffice\\logs\\bench_local_llm.json" `
    --write-preference
  ```
- 在应用中统一调用：
  ```python
  from models.services.llm_router import route_chat
  messages = [
      {"role": "system", "content": "你是一个有帮助的助手"},
      {"role": "user", "content": "请用一句话介绍自己"}
  ]
  print(route_chat("tinyllama:latest", messages))
  ```

如需同名模型对比与自动偏好更新，请确保两后端均加载相同模型名（例如 `qwen2:0.5b`）。