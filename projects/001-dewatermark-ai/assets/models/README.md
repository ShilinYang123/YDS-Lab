# 模型资源目录（assets/models）

此目录用于统一存放 001-dewatermark-ai 项目所需的各类模型资源。

## 目录规范
- 所有模型统一归档至 `assets/models/`。
- 典型结构示例：
  - `assets/models/lama/`：LAMA 相关模型与配置
  - `assets/models/shimmy/`：Shimmy 相关模型与脚本

## 路径迁移说明
- 原 `projects/001-dewatermark-ai/models/` 已迁移到本目录。
- 请将代码中的旧路径更新为新的标准路径，例如：
  - 旧：`projects/001-dewatermark-ai/models/shimmy/...`
  - 新：`projects/001-dewatermark-ai/assets/models/shimmy/...`

## 加载建议
- 前端或 Tauri 后端加载模型时，使用相对路径 `assets/models/...` 或通过 Tauri 的资源解析方式来确保跨平台路径一致性。