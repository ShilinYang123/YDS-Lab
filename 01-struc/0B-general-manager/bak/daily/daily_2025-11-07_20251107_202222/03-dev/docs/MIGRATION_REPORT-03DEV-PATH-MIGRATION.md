# 03-dev 路径优先级迁移报告（阶段性）

概述：
- 本次迁移将代码与工具的“项目目录”优先级从 projects 切换为 03-dev，并保留对旧路径（projects）的兼容回退。
- 同步完成关键项目目录与文档复制，确保前后端服务正常运行。

已完成的变更与操作：

1. 目录备份
   - 已创建完整备份：`S:/YDS-Lab/backups/legacy/projects_pre_merge_03dev-<timestamp>`（示例：20251106-072428）。
   - 备份工具：PowerShell + robocopy（退出码 1，属于成功/警告范围）。

2. 项目目录同步到 03-dev
   - 已同步：
     - `projects/001-dewatermark-ai` → `03-dev/001-dewatermark-ai`
     - `projects/JS001-meetingroom` → `03-dev/JS001-meetingroom`
     - `projects/templates` → `03-dev/templates`

3. 代码路径更新（优先 03-dev，兼容 projects 回退）
   - tools/check/env_ready.py：
     - required_dirs 从 `projects` 调整为 `03-dev`。
     - check_directory_structure 增加兼容回退逻辑（缺失 03-dev 时，若存在 projects 则不判定失败并提示）。
     - check_write_permissions 优先检查 `03-dev`，兼容检查 `projects`。
   - tools/start.py：
     - 启动检查的必需目录从 `projects` 调整为 `03-dev`。
     - `03-dev` 缺失时回退到 `projects` 并打印警告。
   - tools/agents/run_collab.py：
     - 会议元信息中的“项目目录”优先输出 `03-dev/<project_id>`，存在时回退到 `projects/<project_id>`。
   - tools/project/create_project.py：
     - 项目创建目标目录优先 `03-dev`，列出项目时兼容展示 `projects`。
   - tools/sub/utils/create_project.py：
     - 子工具项目创建路径从 `projects` 切换为优先 `03-dev`，并在日志中标注根目录选择。
   - tools/backup/daily_snapshot.py：
     - 默认 include_patterns 增加 `03-dev/**/*`。
     - 加载已有配置时自动补充 `03-dev/**/*` 与 `projects/**/*`，避免旧配置遗漏新路径。
 - 03-dev/JS001-meetingroom/servers/meetingroom_server.py：
     - 前端 UI 与项目目录显示逻辑已优先适配 `03-dev`（不再指向 tools/servers），并保留对 `projects` 的回退说明（仅文档层面）。

6. 配置路径统一（LongMemory 与通用配置）
   - 标准配置路径：`config/yds_ai_config.yaml`、`config/document_governance_config.json`、`config/voice_service_config.json`。
- 代码层面已移除旧路径 `tools/servers/yds_ai_config.yaml` 的兼容回退读取，统一仅使用 `config/yds_ai_config.yaml`。
   - 已更新下列文档的旧路径引用：
     - `04-prod/001-memory-system/docs/快速部署指南.md`
     - `04-prod/001-memory-system/docs/JS003-Trae长记忆功能使用说明书.md`
     - `04-prod/001-memory-system/docs/reports/项目总结报告.md`

7. 目录清理
   - 已将 `tools/servers` 目录下遗留的配置与报告归档至：`backups/legacy/tools-servers-config-20251106_201920/`。
   - 归档文件：`document_governance_config.json`、`voice_service_config.json`、`system_analysis_report.md`。
- 当前 `tools/servers/` 目录为空，不再作为运行依赖；严禁从该目录读取配置或启动服务。

4. 文档迁移到 03-dev/docs
   - 已复制：
     - `projects/README.md` → `03-dev/docs/`
     - `projects/DELIVERY_SUMMARY.md` → `03-dev/docs/`

5. 前端服务验证
   - 已启动会议室服务：`http://127.0.0.1:8020/`，前端 UI 指向 `03-dev/JS001-meetingroom/ui` 成功。
   - 已打开本地预览验证，无报错；建议继续观察终端日志，确保无新错误。

后续建议与清理计划：
- 保留回退策略：所有新增逻辑均保留 `projects` 作为兼容路径，避免迁移期间服务中断。
- 渐进式清理：
  1) 在连续 7 天内无对 `projects` 的新增写入后，计划归档 `projects` 到 `backups/legacy` 并标记只读。
  2) 对文档内容中关于 `projects/` 的文字描述进行批量修订为“优先 03-dev，兼容 projects”。
  3) 在 CI/备份工具中，确认 `03-dev/**/*` 已包含并优先，`projects/**/*` 作为次要项。
- 监控与校验：
  - 使用 `tools/check/env_ready.py` 与 `tools/start.py` 的检查输出，确认 `03-dev` 可写、目录结构完整。
  - 结合 `tools/backup/daily_snapshot.py` 每日快照，确保变更后的目录均被纳入备份。

风险与回滚方案：
- 若出现路径解析错误或服务访问异常，立即切换至 `projects` 目录（已保留回退），并在修复后重新切回 `03-dev`。
- 保留备份目录，确保可以在 10 分钟内通过 robocopy 完成紧急回滚。

状态：
- 本报告反映的迁移为“阶段性完成”，尚有少量代码/文档中的文字性引用需要逐步修订，不影响功能运行。

更新时间：2025-11-06（阶段性补充）
 
新增：端口策略与运行状态（2025-11-06）
- 策略：采用策略 A（双端口）。
- 稳定服务端口：8020（生产/演示）。
- 验证服务端口：8023（专用于变更验证）。
- 已停止端口：8021（避免环境混淆）。
- 运行状态：两端口均可正常加载 `03-dev/JS001-meetingroom/ui/index.html`，`@vite/client` 资源 404 为预期（非 Vite 开发模式）。