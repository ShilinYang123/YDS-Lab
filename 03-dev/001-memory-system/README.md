# 001-memory-system（开发版）

本目录是 Memory System 的开发环境（编号 001），与生产环境 `04-prod/001-memory-system` 保持统一编号与功能对应。

开发版主要包含：
- tests/：用于本地开发联调的 Python 测试脚本（智能监控、主动提醒、长记忆并发写入等）
- TraeLM/：长记忆相关的前端/服务端 Node 集成示例与测试（可选）

## 快速开始（一键运行/联调）

1) 直接运行所有开发测试（PowerShell）：

```
powershell -ExecutionPolicy Bypass -File 03-dev/001-memory-system/run_tests.ps1
```

2) 如需同时运行 TraeLM 的 Node 测试（需要安装 Node.js ≥ 18 与 npm）：

```
powershell -ExecutionPolicy Bypass -File 03-dev/001-memory-system/run_tests.ps1 -IncludeNode
```

脚本会顺序执行：
- Python 测试：`tests/test_intelligent_monitor.py`、`tests/test_longmemory_integration.py`
- （可选）Node 测试：进入 `TraeLM/` 执行 `npm install && npm test`

## 运行要求
- Python ≥ 3.10
- Windows PowerShell（已在脚本中处理路径，支持从仓库任意位置运行）
- 可选：Node.js ≥ 18 与 npm（仅在启用 `-IncludeNode` 时需要）

## 与生产目录的联动说明
- 测试脚本会自动将生产脚本目录加入 `sys.path`：
  - `04-prod/001-memory-system/scripts`
  - `04-prod/001-memory-system/scripts/monitoring`
- 主动提醒模块在生产中命名为 `start_proactive_reminder.py`，测试已适配从该模块导入 `ProactiveReminder`。
- 监控模块位于 `scripts/monitoring/` 下：`intelligent_monitor.py`、`smart_error_detector.py`。

## 常见问题
- 如遇到模块导入失败，请确认生产目录存在上述脚本文件；若移动或重命名，请同步更新测试脚本的导入路径。
- 如需在 CI 或其他环境运行，可将 `run_tests.ps1` 的逻辑拆分为独立命令。