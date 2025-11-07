YDS-Lab MCP Servers (迁移版)

说明：
- 本目录为 MCPCluster 的新位置，统一路径为 tools/mcp/servers。
- 已从 01-struc/MCPCluster 复制以下子模块：Excel、Figma、FileSystem、GitHub、Builder、Database。
- 集群配置文件：cluster_config.yaml（路径已更新为 tools/mcp/servers/*）。
- 若项目中仍有对 01-struc/MCPCluster 的引用，请尽快修复为新路径。兼容期已结束，禁止任何“旧路径回退”。

迁移策略（以当前 MCPCluster 版本为准）：
- 如遇到重复工具或冲突，统一使用本目录中的实现。
- 旧目录 01-struc/MCPCluster 仅保留历史记录说明，不再作为运行或读取来源。

使用建议：
- 新增或更新 MCP 服务，请在本目录下进行，并同步更新 cluster_config.yaml。
- 管理脚本（如 mcp_server_manager.py、mcp_health_checker.py）已指向此目录。

目录结构：
- Excel/
- Figma/
- FileSystem/
- GitHub/
- Builder/
- Database/
- cluster_config.yaml