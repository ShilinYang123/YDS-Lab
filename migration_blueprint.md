# YDS-Lab 仓库规范化迁移蓝图（2025-11-06）

本蓝图用于一次性执行“盘点 → 备份 → 迁移/清理 → 验证”的规范化重构，避免逐目录逐文件确认的低效流程。

## 目标分层
- 01-struc：组织治理与制度配置
- 02-task：任务与工作流
- 03-dev：开发环境（源码/UI/服务/测试）
- 04-prod：生产环境（服务/发布/报告）
- config：统一配置入口
- tools：通用工具与兼容包装器（保留 start/finish/update_structure/check_structure 等）
- backups：备份与归档（支持回滚）
- tmp：临时文件（迁移后尽量清空）

## 执行策略
1. 所有迁移均“先备份（zip）”再移动，最后删除旧路径，确保可回滚。
2. 对代码引用统一批量替换为新路径，并做冒烟验证（首页 + API + WebSocket + /health）。
3. 对重复与过时目录合并或清理，减少工具目录里的业务代码。

## 显式迁移清单（第一批）

已完成：
- tools/servers/ui → 03-dev/JS001-meetingroom/ui（保留备份：backups/legacy/servers-ui-YYYYMMDD_HHMMSS.zip）

待执行（本次批处理）：
1) Meetingroom 服务与依赖模块归位（开发环境）
   - tools/servers/meetingroom_server.py → 03-dev/JS001-meetingroom/servers/meetingroom_server.py
   - tools/servers/agent_roles.py → 03-dev/JS001-meetingroom/servers/agent_roles.py
   - tools/servers/meeting_levels.py → 03-dev/JS001-meetingroom/servers/meeting_levels.py
   - tools/servers/mcp_message_model.py → 03-dev/JS001-meetingroom/servers/mcp_message_model.py
   - tools/servers/intelligent_agenda.py → 03-dev/JS001-meetingroom/servers/intelligent_agenda.py
   - tools/servers/rbac_system.py → 03-dev/JS001-meetingroom/servers/rbac_system.py
   - tools/servers/voice_service.py → 03-dev/JS001-meetingroom/servers/voice_service.py
   - tools/servers/test_yds_ai_system.py → 03-dev/JS001-meetingroom/servers/test_yds_ai_system.py（后续可再归档到 tests/）
   - 处理：tools/servers/external_models.json 备份后删除（meetingroom_server 已改为读取 01-struc/0B-general-manager/config/external_models.json）

2) 启动脚本与文档引用
   - tools/scripts/start_meetingroom_server.ps1 中的旧路径（tools/servers/meetingroom_server.py）替换为 03-dev/JS001-meetingroom/servers/meetingroom_server.py
   - meetingroom_server.py 顶部“启动示例”改为：python 03-dev/JS001-meetingroom/servers/meetingroom_server.py --host 127.0.0.1 --port 8020

3) UI 重复目录合并
   - 03-dev/002-meetingroom/ui 与 03-dev/JS001-meetingroom/ui 比对差异后，合并到 JS001 统一；完成后 002-meetingroom/ui 备份并清理。

## 第二批（准备项）
- tools/mcp/* → 03-dev/mcp（开发工具与集成测试）（需要逐模块评估依赖链）
- tools/production/start.py → 04-prod/scripts/start.py
- tools/scripts/start_production.bat → 04-prod/scripts/start_production.bat
- tmp/memory_tests → 03-dev/001-memory-system/tests（迁移后清空 tmp）
- root 重复配置（rbac_config.json、voice_service_config.json、document_governance_config.json）统一到 config/ 并在代码中指定路径（需回归测试）

## 验证项
- http://127.0.0.1:8020/ 首页加载
- /api/search-rooms、/api/book-room、/api/my-bookings、/api/room-status 响应正常
- /health 返回 ok 且 ui: true
- WebSocket mcp_event/mcp_message 能建立握手并广播日志

## 风险与回滚
- 每一步都有 zip 备份；若出现不可预期错误，可将备份 zip 解压回原位回滚。
- meetingroom_server 改路径后，启动脚本和文档需要同步更新，否则会启动失败或找不到 UI。

—— 本蓝图由 Trae 助手生成并执行，所有操作均记录到 backups/legacy 下，确保可审计和可回滚。

## 2025-11-07 追加：日志路径统一 & tools 目录治理完成
- 全局批量替换旧日志路径 `01-struc/Log` → `01-struc/0B-general-manager/logs`（含 config、main.py、voice_service 等配置与注释）。
- 保留 backups/legacy 与 bak 目录下的历史 README 旧路径引用，确保归档可回溯。
- tools/production/start.py 核心实现迁移至 04-prod/scripts/start.py，原目录删除；tools/project/create_project.py 迁移至 03-dev/scripts/create_project.py，原目录删除。
- tools/scripts/start_production.bat 未直接调用旧路径，无需改动，保持兼容；后续可统一由 04-prod\scripts\start.py 接管。
- 至此，活跃代码与配置中已无旧日志路径残留；tools 目录瘦身完成，进入后续业务模块归位阶段。