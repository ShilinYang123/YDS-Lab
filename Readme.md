# YDS-Lab

## 项目简介

YDS-Lab 是一个综合性的AI工具和数据处理实验室项目，集成了多种工具和服务。

## 项目结构

```
YDS-Lab/
├── Docs/                    # 项目文档
├── ai/                      # AI相关模块
├── tools/                   # 核心工具集
├── tools2/                  # 扩展工具集
├── projects/                # 项目文件
├── knowledge/               # 知识库
├── config/                  # 配置文件
└── archive/                 # 归档文件
```

## 主要功能

- **AI工具集成**: 集成多种AI服务和工具
- **数据处理**: 批量处理各种格式的文件
- **MCP服务器**: 模型上下文协议服务器集成
- **文档管理**: 自动化文档生成和管理
- **质量控制**: 代码质量检查和合规监控

## 快速开始

1. 克隆项目到本地
2. 安装依赖
3. 配置环境变量
4. 运行启动脚本

## 技术栈

- Python 3.x
- Node.js
- PowerShell
- Git
- 各种AI和数据处理库

## 贡献

欢迎提交Issue和Pull Request来改进项目。

## 许可证

许可证待定。

## 离线安装与二进制文件管理

为避免仓库被大体积安装包或归档文件污染，统一约定：

- 不将安装包、压缩包等二进制文件提交到仓库。
- 如需离线安装或本地保留，请统一放置在 downloads/ 目录（该目录已在 .gitignore 中忽略）。
- 提交前本项目的 pre-commit 钩子与 auto_push.py 会拦截 >10MB 且扩展名在 {exe, zip, 7z, tar, iso} 的文件，防止误提交。

示例：在 Windows 下获取 Git 安装包并保存在本地（不会被提交）

PowerShell：

1) 创建目录并下载
```
$dl = "downloads"
New-Item -ItemType Directory -Force -Path $dl | Out-Null
$uri = "https://github.com/git-for-windows/git/releases/latest/download/Git-64-bit.exe"
$dest = Join-Path $dl "Git-installer.exe"
Invoke-WebRequest -Uri $uri -OutFile $dest
```

2) 安装或保留离线安装包。该文件位于 downloads/，默认不会被 Git 跟踪。

如确需将二进制纳入版本管理，请按团队约定启用 Git LFS（需要协作者安装 LFS 并可能影响历史）。

---

## 本地 LLM 路由（Shimmy / Ollama）

为兼容多种本地模型后端并统一调用入口，项目引入“LLM 路由与后端选择”能力：
- 详细说明文档（正式）：`Struc/GeneralOffice/Docs/LLM路由与后端选择（Shimmy-Ollama）使用说明.md`
- 统一入口：`models/services/llm_router.py` → `route_chat(model, messages, ...)`
- 基准脚本：`tools/performance/performance_analyzer.py`（含健康预热、失败回退）
- 日志与偏好：`Struc/GeneralOffice/logs/bench_local_llm.json`、`models/config/router_preference.json`

请先确保本地已启动 Shimmy 与 Ollama 服务，并根据说明文档完成配置与基准测试。
