# 001-dewatermark-ai 项目

本项目为基于 Tauri 的跨平台桌面应用，包含前端 UI（Vite + React/TypeScript）与后端（Rust/Tauri，必要时结合 Python 服务）。

## 目录结构（核心）
- ui/：前端源码（Vite + React/TS）
- src-tauri/：Tauri 后端（Rust）
- assets/models/：模型文件标准归档目录（原 models/ 已迁移至此）
- docs/：项目文档
- servers/：本地或服务端辅助脚本与配置
- output/、backups/、debug/：运行输出、备份及调试相关目录

## 模型目录规范
- 统一使用 `assets/models/` 存放各类模型资源，例如：
  - `assets/models/lama/`
  - `assets/models/shimmy/`
- 若代码中仍有 `projects/001-dewatermark-ai/models/...` 的旧引用，请更新为 `projects/001-dewatermark-ai/assets/models/...`。
- 推荐在加载模型时，使用相对路径 `assets/models/...`（相对于项目根目录）或结合 Tauri 的资源路径解析。

## 开发与运行（概要）

### 1. 安装依赖
- **Node.js LTS**：用于前端开发
- **Rust**：用于 Tauri 后端开发
  - 如需安装 Rust，可使用 `downloads/rustup-init.exe`（已下载）
  - 或访问 https://rustup.rs/ 获取最新版本
  - 安装后重启终端以使 `cargo` 命令生效

### 2. 前端开发
- 进入 `ui/` 目录：`npm install` 后 `npm run dev`

### 3. Tauri 开发
- 在项目根或 `src-tauri/` 目录执行：`cargo tauri dev`
- 或按 `src-tauri/tauri.conf.json` 配置进行构建/运行

### 注意事项
- `downloads/` 目录存放安装程序等大文件，已被 `.gitignore` 排除
- 模型文件等大文件请放在 `assets/models/` 目录，并确保在 `.gitignore` 中排除

具体实现细节与需求请参考 `docs/` 下的文档（例如 `SPEC.md`、实施计划等）。