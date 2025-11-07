# Production 目录迁移说明

本目录历史用于部署与产出管理。根据 2025-11 的目录治理方案：

- 长记忆系统已迁移至 `03-proc/memory-system/`。
- 发行物统一存放至 `03-proc/releases/`。
- 日志统一收敛至仓库根目录 `logs/`。

建议逐步将本目录下的以下子模块并入规范目录：

- `Config/` → 已迁移至 `config/production.yaml`。
- `Logs/` → 如有内容请合并至根 `logs/`。
- `MCPCluster/`、`TraeAgents/`、`SharedWorkspace/`、`tools/` → 结合实际用途，建议并入 `Struc/` 下对应目录。

后续迁移完成后，可删除本目录以减少路径混乱。