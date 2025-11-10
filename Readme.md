# YDS-Lab

## 项目简介

YDS-Lab 是一个综合性的AI工具和数据处理实验室项目，集成了多种工具和服务。

## 项目结构

```
YDS-Lab/
├── 01-struc/                # 结构文档和项目规范
├── 02-task/                 # 任务管理和开发文档
├── 03-dev/                  # 开发环境和工作区
├── 04-prod/                 # 生产部署和发布
├── Training/                # 培训材料和教程
├── config/                  # 配置文件
├── coverage/                # 代码覆盖率报告
├── docs/                    # 项目文档
├── tools/                   # 核心工具集
├── utils/                   # 实用工具脚本
├── ch.py                    # 结构检查工具
├── fi.py                    # 文件索引工具
├── st.py                    # 系统测试工具
├── up.py                    # 更新工具
└── requirements.txt         # Python依赖
```

## 主要功能

- **长记忆系统**: 集成Trae IDE长效记忆功能，支持知识图谱管理
- **AI工具集成**: 集成多种AI服务和工具（Ollama、Shimmy等）
- **MCP服务器**: 模型上下文协议服务器集成和管理
- **会议管理**: 智能会议室调度和会议记录管理
- **数据处理**: 批量处理各种格式的文件和数据
- **文档管理**: 自动化文档生成和管理
- **质量控制**: 代码质量检查、合规监控和性能分析
- **部署管理**: 自动化部署和发布流程

## 快速开始

### 环境要求
- Python 3.8+
- Node.js 16+
- Git
- PowerShell 5.1+

### 安装步骤

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd YDS-Lab
   ```

2. **安装Python依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **初始化环境**
   ```bash
   python tools/init_trae_environment.py
   ```

4. **运行系统测试**
   ```bash
   python st.py
   ```

5. **启动长记忆系统**
   ```bash
   cd 04-prod/001-memory-system
   npm start
   ```

## 技术栈

### 后端技术
- **Python 3.8+**: 主要开发语言
- **Node.js 16+**: 长记忆系统运行环境
- **PowerShell**: 自动化脚本和系统管理

### AI和数据处理
- **Ollama**: 本地大模型服务
- **Shimmy**: AI模型路由和代理
- **Pandas**: 数据处理和分析
- **NumPy**: 数值计算

### 开发工具
- **Git**: 版本控制
- **Pre-commit**: 代码质量检查
- **Coverage**: 代码覆盖率测试

### 部署和运维
- **Docker**: 容器化部署（可选）
- **NPM**: Node.js包管理
- **PM2**: 进程管理（生产环境）

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

- 为兼容多种本地模型后端并统一调用入口，项目引入“LLM 路由与后端选择”能力：
- 详细说明文档（正式）：`01-struc/docs/LLM路由与后端选择（Shimmy-Ollama）使用说明.md`
- 统一入口：`models/services/llm_router.py` → `route_chat(model, messages, ...)`
- 基准脚本：`tools/performance/performance_analyzer.py`（含健康预热、失败回退）
- 日志与偏好：`01-struc/0B-general-manager/logs/bench_local_llm.json`、`models/config/router_preference.json`

请先确保本地已启动 Shimmy 与 Ollama 服务，并根据说明文档完成配置与基准测试。
