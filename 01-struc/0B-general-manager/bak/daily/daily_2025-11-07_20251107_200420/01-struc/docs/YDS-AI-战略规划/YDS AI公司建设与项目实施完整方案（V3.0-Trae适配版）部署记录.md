YDS AI公司建设与项目实施完整方案（V3.0-Trae适配版）部署记录

日期：2025-11-04
版本：v3.0 适配部署记录（Meetingroom 子系统与 MCP 消息通道增强）
负责人：项目技术负责人（Trae集成）

一、目标与范围
- 对会议系统（meetingroom_server）进行低风险、向后兼容的增强：
  - 强化 WebSocket 握手安全（可开关的 JWT 校验）。
  - 统一 MCP 严格版消息事件通道（mcp_message），并在关键端点广播。
  - 完善投票流程（新增官方 finalize 端点）。
  - 建立语音会话与分片主链路（保留旧演示端点）。
  - 统一消息模型字段（MCPMessageBuilder：message_id → id）。

二、主要变更项（已实施）
1) 消息模型字段一致性
- 文件：03-dev/JS001-meetingroom/servers/mcp_message_model.py
- 变更：MCPMessageBuilder 的以下工厂方法，在构造 MCPMessage 时统一使用 `id` 字段，替代历史遗留 `message_id`：
  - create_docs_share
  - create_vote
  - create_system_notice
- 影响范围：保证严格版消息 `MCPMessage.to_dict()` 输出字段与文档一致（id、room_id、channel、event_type、topic、sender、timestamp、payload 等）。

2) WebSocket 事件与握手安全
- 文件：03-dev/JS001-meetingroom/servers/meetingroom_server.py
- 新增事件通道：`emit_mcp_message(message)` → 广播严格版 MCP 消息事件 `mcp_message`。
- 保留兼容事件：`emit_mcp_event(event, data)` → 兼容聚合事件 `mcp_event`。
- 握手JWT强制（可开关）：
  - 环境变量：`WS_JWT_REQUIRED`（默认关闭）。
  - 开启后：握手阶段必须携带有效JWT，否则拒绝连接。
  - JWT提取来源：请求头 `Authorization: Bearer <token>`，或 query/body 的 `token`。
  - JWT验证：`rbac_system.verify_jwt_token()`（payload包含 user_id、username、roles、exp、iat）。
- 保留默认Socket.IO路径：`/socket.io`（不新增 `/ws`），降低前端兼容风险。

3) REST端点增强（广播严格版 MCP 消息）
- 文档共享：`/mcp/docs/share`（广播 mcp_message，优先从JWT解析角色与room_id）。
- 投票：
  - `/mcp/votes/create`（兼容+严格版并行广播）。
  - `/mcp/votes/cast`（兼容+严格版并行广播）。
  - `/mcp/votes/finalize`（新增官方端点，兼容+严格版并行广播）。
- 语音链路：
  - 新主链路：`/mcp/voice/session/start`、`/mcp/voice/chunk`（严格版消息 VOICE_STREAM）。
  - 兼容演示端点：`/mcp/voice/stream`（保留）。

三、配置项说明（生产建议）
- WS_JWT_REQUIRED（WebSocket握手JWT强制开关）：
  - 建议：开发环境关闭以兼容旧客户端；生产环境开启提升安全性。
  - 开启值：`true/1/yes/on`；关闭值：`false/0/no/off`。
- RBAC JWT Payload：`{ user_id, username, roles[], exp, iat }`（由 rbac_system 生成与校验）。

四、客户端接入与示例
1) Socket.IO 握手时传JWT（两种方式）
- 通过 query 参数：
```
const socket = io("http://127.0.0.1:8021", { query: { token: jwt } });
```
  注意：query 的 token 为纯JWT字符串，不带 `Bearer ` 前缀。
- 通过请求头：
```
const socket = io("http://127.0.0.1:8021", {
  extraHeaders: { Authorization: `Bearer ${jwt}` }
});
```

2) REST 快速验证示例（PowerShell / curl）
- 投票 finalize：
```
curl -X POST http://127.0.0.1:8021/mcp/votes/finalize -H "Content-Type: application/json" \
  -d "{\"proposal_id\":\"P-001\",\"room_id\":\"ROOM-01\",\"role\":\"meeting_admin\"}"
```
- 语音会话：
```
curl -X POST http://127.0.0.1:8021/mcp/voice/session/start -H "Content-Type: application/json" \
  -d "{\"room_id\":\"ROOM-01\",\"role\":\"assistant\"}"
```
- 语音分片：
```
curl -X POST http://127.0.0.1:8021/mcp/voice/chunk -H "Content-Type: application/json" \
  -d "{\"session_id\":\"S-001\",\"chunk_seq\":1,\"audio_base64\":\"...\"}"
```

五、部署与运行记录
- 代码变更：
  - mcp_message_model.py：统一消息构造 `id` 字段（替换历史 `message_id`）。
  - meetingroom_server.py：新增 `emit_mcp_message`、`_get_jwt_payload_from_request`、`_resolve_effective_role`。
  - meetingroom_server.py：增强 `/mcp/docs/share`、`/mcp/votes/*`、语音相关端点的严格版消息广播。
- 编译检查：通过（py_compile 无语法错误）。
- 服务重启：已重启，运行于 `http://127.0.0.1:8021`。
- 路由快照（节选）：
```
/mcp/voice/session/start
/mcp/voice/chunk
/mcp/votes/finalize
/mcp/votes/create
/mcp/votes/cast
/mcp/docs/share
/yds/auth/login
/yds/voice/stt
/yds/voice/tts
```

六、风险控制与回退策略
- 保留兼容事件通道 `mcp_event` 与演示端点 `/mcp/voice/stream`，确保前端在过渡期不受影响。
- 握手JWT强制为“可开关”，默认关闭，出现兼容问题时可通过 `WS_JWT_REQUIRED=false` 回退。
- 所有新增功能为增量，不改变历史端点语义与返回结构。

七、后续工作计划（待落实）
- 文档完善（待办）：
  - 补充 WebSocket 握手JWT使用说明与配置建议。
  - 更新规范端点清单（含 `/mcp/votes/finalize`）。
  - 语音新旧链路说明与最佳实践。
- 测试与验收（待办）：
  - 新增 WS 握手（有/无JWT）连接测试用例。
  - 投票 finalize 端到端（创建-投票-最终化-广播）用例。
  - 语音 session/chunk 流程用例（分片顺序与会话闭合）。

八、附录：环境与配置示例
- Windows PowerShell 开启握手JWT校验：
```
$env:WS_JWT_REQUIRED = "true"
python 03-dev/JS001-meetingroom/servers/meetingroom_server.py --host 127.0.0.1 --port 8021
```
- 关闭校验：
```
$env:WS_JWT_REQUIRED = "false"
python 03-dev/JS001-meetingroom/servers/meetingroom_server.py --host 127.0.0.1 --port 8021
```

九、变更影响评估（结论）
- 安全性：可在生产开启握手JWT校验，提升实时通道安全。
- 兼容性：保持默认路径与兼容事件，风险低。
- 可维护性：统一消息字段与严格版事件通道，前端实现更清晰。
- 可扩展性：语音主链路（session/chunk）利于后续集成 STT 与流控制。

—— 完 ——