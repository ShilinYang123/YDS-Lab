# 工具脚本目录

本目录包含 YDS-Lab 系统的核心维护和管理工具。

## 🔧 核心工具

### 系统管理
- `start.py` - 系统启动脚本
- `fi.py` - 完成/收尾（新入口，替代旧 `tools/finish.py`）
- `refresh_env.bat` - 环境刷新批处理

### 结构管理
- `check_structure.py` - 目录结构检查
- `update_structure.py` - 目录结构更新
- `setup_git_path.py` - Git路径配置

### 功能模块
- `check/env_ready.py` - 环境就绪检查
- `docs/generate_meeting_log.py` - 会议日志生成
- `agents/run_collab.py` - 多Agent协作编排器（每日/紧急会议纪要自动生成与归档）
- `git/auto_push.py` - 自动Git推送
- `project/create_project.py` - 项目创建工具

## 📁 -sub 目录

`-sub/` 目录包含从老项目继承的工具集，作为功能库暂存：
- 🚫 **不会备份到Git** (已在.gitignore中排除)
- 📦 **按需提取** 需要时从中提取有用的工具
- 🔄 **逐步整合** 将有价值的工具整合到主工具集

## 📋 配置文件

配置文件已统一到 `/config/` 目录管理：
- `structure_config.yaml` → `/config/structure_config.yaml`
- `finish_config.yaml` → `/config/finish_config.yaml`
- `yds_ai_config.yaml` → `/config/yds_ai_config.yaml`
- 其他配置（如 `production.yaml`、`trae_config.yaml`、`rbac_config*.json`、`security/*`、`voice_service_config.json` 等）均统一位于 `/config/`

> 强制要求：更新或新增脚本必须从 `/config/` 读取配置；禁止旧路径回退。发现旧路径引用应立即整改为直达 `/config/`。

## 📊 报告输出位置

所有运行与验证报告统一输出到 `/04-prod/reports/`：
- `system_test_report.json`（系统测试报告）
- `mcp_validation_report.json`（MCP 集成验证报告）
- `migration_report.json`（智能体迁移报告）
- `migration_status.json`（迁移状态跟踪）
- `servers_test_report.json`（服务器测试报告，原 `tools/servers/test_report.json`）

> 路径变更说明：历史脚本中若仍引用 `tools/*.json`，请更新为 `/04-prod/reports/*.json`。

## 🧩 MCP 依赖安装（统一入口）

MCP 依赖安装脚本统一入口：

```bash
python tools/mcp/install_mcp_dependencies.py
```

根目录版本（`tools/install_mcp_dependencies.py`）已归档至 `backups/legacy/tools-YYYYMMDD/`，请使用 `tools/mcp/` 版本作为唯一入口。

## 🚀 使用方法

### 基本操作
```bash
# 启动系统
python tools/start.py

# 检查结构
python tools/check_structure.py

# 更新结构
python tools/update_structure.py

# 完成操作（新入口）
python fi.py
```

### 环境管理
```bash
# 刷新环境
tools/refresh_env.bat

# 检查环境就绪
python tools/check/env_ready.py
```

### 多Agent 协作（每日/紧急会议）

快速生成并归档会议纪要到 `01-struc/0B-general-manager/meetings`：

```powershell
# 每日晨会（默认项目 DeWatermark AI）
python tools/agents/run_collab.py --meeting daily --project "DeWatermark AI"

# 紧急会议（需提供原因）
python tools/agents/run_collab.py --meeting emergency --reason "开发进度延迟2天" --project "DeWatermark AI"

# 指定默认模型（与 models/services/llm_router.py 配置一致）
python tools/agents/run_collab.py --meeting daily --model "qwen2:7b-instruct"

# 为“行动项与决策”指定独立模型
python tools/agents/run_collab.py --meeting daily --actions-model "qwen2:7b-instruct"

# 自定义参会角色与议程（逗号分隔）
python tools/agents/run_collab.py --meeting daily \
  --participants "总经理(CEO),企划总监,财务总监,开发总监,市场总监,资源与行政" \
  --agenda "开场说明,部门汇报,行动项与决策"

# 绑定项目目录（用于会议信息展示）
python tools/agents/run_collab.py --meeting daily --project "DeWatermark AI" --project-id "001-dewatermark-ai"

# 计划任务脚本（输出日志到 01-struc/0B-general-manager/logs）
powershell -ExecutionPolicy Bypass -File scripts/schedule_daily_meeting.ps1
```

完整说明见：
- `01-struc/docs/YDS-AI-组织与流程/多Agent协作指南.md`

## 📝 开发规范

1. **新工具添加**: 按功能分类到对应子目录
2. **配置管理**: 统一使用 `/config/` 目录的配置文件
3. **文档更新**: 新增工具需更新本README
4. **测试验证**: 确保工具在不同环境下正常运行

## ⚠️ 注意事项

- `-sub/` 目录内容不会同步到Git仓库
- 修改核心工具前请先备份
- 配置文件路径已更改，注意更新引用

### 兼容入口清理说明（2025-11-06）
- 旧兼容入口 `tools/finish.py` 已移除；请统一使用根目录 `fi.py`
- 若发现文档或脚本仍引用 `tools/finish.py`，请按上述使用方法更新为 `python fi.py`