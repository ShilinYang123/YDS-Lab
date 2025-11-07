# 03-dev

职责：开发与测试区域，用于源码改造、配置、测试与临时构建产物（不入库）。

建议约定：
- 在 03-dev/build 放置临时构建产物，并通过 .gitignore 忽略。
- 优先使用 `03-dev/<project>` 作为开发路径，逐步替换旧的 `projects/` 引用。

路径治理与兼容说明：
1. 会议室服务（JS001）已迁移到 `03-dev/JS001-meetingroom/servers` 与 `03-dev/JS001-meetingroom/ui`，旧的 `tools/servers/*` 已废弃并清理为归档。
2. 通用配置文件统一至 `config/` 目录（如 `config/yds_ai_config.yaml`、`config/rbac_config.json`），代码层面保留对旧路径的回退读取。
3. 新增模块建议直接放在 03-dev 下（apps/components），并在迁移报告中记录变更以便回滚。