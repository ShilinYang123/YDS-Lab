# Chrome DevTools MCP Server 使用指南（Trae 集成版）

本目录用于在 Trae 的 MCP 工具集中集成并使用「Chrome DevTools MCP Server」。该方式由 Trae 负责服务的生命周期与通信，无需安装社区桥接器、无需手动加载解压扩展，也不需要本地 HTTP 端点。

## 关键点
- 使用方式：通过 Trae 的 MCP 工具面板启用并使用 chrome-devtools 工具集（如 list_pages、navigate_page、evaluate_script、take_screenshot 等）。
- 连接与管理：由 Trae 统一管理，无需 `mcp-chrome-bridge`、无需 Native Messaging Host 注册，也无需 `http://127.0.0.1:12306/mcp`。
- 无需额外资产：不需要 `chrome-mcp-extension.pem`；仅当自行构建浏览器扩展并进行签名/发布时才需要该文件。
- 日志与报告：建议将功能性健康检查报告输出到：`S:\YDS-Lab\Struc\GeneralOffice\logs\tools\mcp\chrome-mcp\`。

## 使用步骤（Trae 集成）
1) 在 Trae 的 MCP 工具列表中启用「chrome-devtools」工具。
2) 直接调用工具：
   - 列出页面：`list_pages`
   - 选择页面：`select_page`
   - 导航页面：`navigate_page`
   - 评估脚本：`evaluate_script`（例如返回 `document.title`）
   - 截图与快照：`take_screenshot` / `take_snapshot`
3) 根据业务需要编排自动化流程，例如打开 1688 网站并进行搜索/筛选。

## 功能性健康检查（推荐）
- 目的：验证 MCP 服务可工作（能获取页面列表、执行脚本、列出网络请求）。
- 示例流程：
  1. 调用 `list_pages`，确认返回页面列表（例如包含 1688 页面）。
  2. `select_page` 选择目标页面。
  3. `evaluate_script` 执行 `() => document.title`，返回页面标题。
  4. `list_network_requests` 列出最近网络请求，确认页面加载正常。
- 报告建议：将上述结果序列化为 JSON，保存到 `S:\YDS-Lab\Struc\GeneralOffice\logs\tools\mcp\chrome-mcp\devtools_mcp_health.json`。

## 旧版/独立方式（不再推荐）
- 旧文档中提到的以下做法已不再适用：
  - 加载本地解压扩展并点击「连接」。
  - 安装并注册 `mcp-chrome-bridge` 作为 Native Messaging Host。
  - 通过 `http://127.0.0.1:12306/mcp` 的 HTTP 端点进行健康检查。
- 说明：在 Trae 集成方案下，服务由 Trae 直接托管与调用，以上步骤均不需要。

## 故障排查
- 工具未显示或调用失败：
  - 在 Trae MCP 工具列表确认「chrome-devtools」已启用；必要时重启 Trae。
- 页面操作异常：
  - 重新选择页面或创建新页面（`new_page`），并重试操作；
  - 使用 `take_snapshot` 确认页面结构已获取；
  - 检查网络连通性与站点可访问性。

## 目录与路径
- 代码与脚本：`S:\YDS-Lab\tools\mcp\chrome-mcp\`
- 建议的健康检查报告目录：`S:\YDS-Lab\Struc\GeneralOffice\logs\tools\mcp\chrome-mcp\`
- 注意：路径统一使用小写 `mcp`（已与全局文档一致）。