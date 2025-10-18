S:\YDS-Lab/

新增模块：yds-lab 顶层设计（占位已创建）

```
 yds-lab/
 ├── agents/               # 所有AI智能体代码 
 │   ├── ceo/ 
 │   │   ├── __init__.py 
 │   │   ├── prompt.py 
 │   │   └── tools.py 
 │   ├── planning/ 
 │   │   ├── __init__.py 
 │   │   ├── market_research.py 
 │   │   └── swot_analysis.py 
 │   ├── finance/ 
 │   │   ├── __init__.py 
 │   │   ├── budget_calculator.py 
 │   │   └── report_generator.py 
 │   └── marketing/ 
 │       ├── __init__.py 
 │       ├── content_writer.py 
 │       └── social_media_scheduler.py 
 ├── projects/             # 各个创业项目 
 │   └── dewatermark-ai/   # 视频去水印项目 
 │       ├── main.py 
 │       ├── ui/           # Tauri 前端代码 
 │       │   └── .gitkeep
 │       └── models/       # ONNX 模型存放目录 
 │           └── .gitkeep
 ├── meetings/             # 会议录音与纪要 
 │   └── .gitkeep
 ├── knowledge/            # 知识库 
 │   ├── company_rules.md 
 │   └── past_projects/ 
 │       └── .gitkeep
 ├── utils/                # 工具函数 
 │   ├── tts.py            # 语音合成模块 
 │   └── logger.py         # 日志记录模块 
 ├── config/               # 配置中心 
 │   └── api_keys.json     # 存放GPT/Claude/Qwen等API密钥 
 ├── main.py               # 主程序入口：启动每日晨会 
 └── requirements.txt      # 依赖包 
```

说明：上述目录与文件均为占位内容，后续可按模块需求逐步完善；api_keys.json 为占位文件，请勿提交任何真实密钥。
│
├── 📁 Docs/                    # 🏢 公司级战略与管理文档
│   ├── 📁 YDS-AI-战略规划/
│   │   ├── YDS AI公司建设与项目实施完整方案（V1.0）.md
│   │   ├── 技术路线图-2025-2027.md
│   │   └── 产品矩阵规划.md
│   ├── 📁 YDS-AI-组织与流程/
│   │   ├── 团队角色与职责.md
│   │   └── 项目立项流程.md
│   ├── 📁 YDS-AI-合规与法务/
│   │   └── 开源许可证汇总.md
│   ├── 📁 YDS-AI-对外文档/
│   │   └── 投资人简报-2025Q3.md
│   ├── 📁 YDS-AI-会议记录/
│   │   └── 2025-10-12-战略对齐会议.md
│   └── 📁 模板库/
│       └── 项目任务书模板.md
│
├── 📁 meta/                    # 🏷️ 实验室元信息（AI 的“记忆中枢”）
│   ├── README.md               # 实验室简介
│   ├── ROADMAP.md              # 短期技术路线（同步自 Docs）
│   ├── RULES.md                # 协作规范
│   ├── TODO.md                 # 全局待办
│   └── logs/
│       └── session_20251012.md # AI 对话摘要
│
├── 📁 projects/                # 🚀 所有项目根目录
│   ├── 📁 decontam/            # 项目1：视频去水印工具
│   │   ├── docs/               # 项目文档
│   │   ├── src/                # 前端（Tauri Web）
│   │   ├── src-tauri/          # 后端（Rust）
│   │   ├── scripts/            # Python 脚本
│   │   ├── models/             # AI 模型（软链接）
│   │   ├── assets/             # 测试素材
│   │   ├── output/             # 输出结果
│   │   ├── debug/              # 调试记录
│   │   ├── backups/            # 项目备份
│   │   ├── tools/              # 工具（软链接到全局 tools/）
│   │   └── servers/            # 多设备配置
│   │
│   ├── 📁 subgen/              # 项目2：智能字幕生成（未来）
│   │   └── ...
│   │
│   └── 📁 templates/           # 项目模板库
│       └── tauri-python-ai/    # 标准模板
│
├── 📁 ai/                      # 🤖 AI 协作中心
│   ├── prompts/                # 提示词库
│   │   ├── code.md             # “写一个FFmpeg脚本”
│   │   ├── doc.md              # “生成任务书”
│   │   └── refactor.md         # “重构目录”
│   ├── outputs/                # AI 输出缓存
│   ├── memory/                 # 上下文快照
│   └── rules/                  # AI 行为约束
│       └── style-guide.md      # 输出格式规范
│
├── 📁 env/                     # 🖥️ 开发环境配置
│   ├── local-pc/               # 华硕笔记本
│   │   ├── paths.json          # 路径映射
│   │   ├── tools_installed.txt # 工具清单
│   │   └── performance.log     # 性能记录
│   ├── guiyang-server/         # 贵阳台式机
│   │   ├── ip.txt
│   │   └── ssh_config.json
│   └── shared/                 # 共享工具
│       └── check_env.py
│
├── 📁 tools/                   # ⚙️ 全局运维工具
│   ├── 📁 backup/              # 备份脚本
│   │   ├── full_backup.py      # 全量备份
│   │   ├── incremental_backup.py # 增量备份
│   │   └── restore.py
│   ├── 📁 check/               # 环境检测
│   │   ├── check_env.py        # 主入口
│   │   └── health_report.md
│   ├── 📁 git/                 # GitHub 自动化
│   │   ├── auto_push.py        # 自动推送
│   │   └── sync_all.py
│   ├── 📁 mcp/                 # MCP Server
│   │   ├── server.py           # AI IDE 集成
│   │   └── config.json
│   └── 📁 utils/               # 实用工具
│       ├── create_project.py   # 创建项目
│       └── clean_temp.py
│
├── 📁 bak/                     # 💾 全局备份存储
│   ├── daily/                  # 每日增量
│   ├── weekly/                 # 每周全量
│   └── projects/               # 项目备份区
│
├── 📁 logs/                    # 📜 全局运维日志
│   ├── backup.log              # 备份日志
│   ├── git_push.log            # 推送日志
│   ├── mcp_server.log          # MCP 日志
│   ├── health_check.log        # 健康检查
│   └── security/
│       └── access.log          # 安全审计
│
├── 📁 knowledge/               # 🧠 知识库
│   ├── papers/                 # 论文摘要
│   ├── tutorials/              # 教程笔记
│   └── case-studies/           # 竞品分析
│
├── 📁 archive/                 # 🗄️ 项目归档
│   ├── decontam-v0.1-old/
│   └── experiments/
│       └── logo-detect-only/
│
├── 📄 .gitignore               # 忽略大文件
├── 📄 CODEOWNERS
└── 📄 CONTRIBUTING.md


✅ 核心模块说明
模块	用途	AI 协作意义
Docs/	公司战略、流程、对外文档	AI 可读取战略方向，确保建议不跑偏
meta/	实验室元信息	AI 的“短期记忆”和行为规范
projects/	所有项目容器	AI 可按标准结构创建/修改项目
ai/	AI 协作专属空间	存放提示词、输出、规则
tools/	全局运维工具	AI 可调用脚本执行任务
bak/	备份中心	保障数据安全
logs/	操作留痕	所有行为可追溯
env/	多设备配置	支持本地+贵阳服务器协作
knowledge/	学习材料	构建 AI 的“训练集”
archive/	项目归档	保持主目录整洁