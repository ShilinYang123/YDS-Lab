# YDS-Lab 标准目录结构（顶层设计）

> **文档版本**: V2.0  
> **更新时间**: 2025年10月22日  
> **项目根目录**: `S:\YDS-Lab`  
> **架构类型**: AI原生分布式协作架构

## 🏗️ 架构概述

YDS-Lab采用AI原生的分布式协作架构设计，通过CrewAI多智能体系统集成6个核心AI Agent，结合标准化的目录结构和自动化工具链，实现"一个人+一群AI"的低门槛创业模式。

## 📁 标准目录结构
```
YDS-Lab/
├── 📁 Struc/                   # 🏢 公司组织架构
│   ├── 📁 Agents/              # 🤖 AI智能体定义和配置
│   │   ├── ceo/                # 总经理Agent - 目标拆解与任务分发
│   │   │   ├── __init__.py
│   │   │   ├── define.py       # Agent定义与配置
│   │   │   ├── prompt.py       # 提示词模板
│   │   │   └── tools.py        # 专用工具集
│   │   ├── dev_team/           # 开发团队Agent群组
│   │   │   ├── __init__.py
│   │   │   ├── dev_architect/  # 开发架构师Agent
│   │   │   ├── dev_coder/      # 开发工程师Agent
│   │   │   └── dev_tester/     # 测试工程师Agent
│   │   ├── finance_director/   # 财务总监Agent - 成本核算与预算管理
│   │   │   ├── __init__.py
│   │   │   ├── define.py
│   │   │   ├── prompt.py
│   │   │   └── tools.py
│   │   ├── marketing_director/ # 市场总监Agent - 用户画像与需求分析
│   │   │   ├── __init__.py
│   │   │   ├── define.py
│   │   │   ├── prompt.py
│   │   │   └── tools.py
│   │   ├── planning_director/  # 企划总监Agent - 市场分析与可行性研究
│   │   │   ├── __init__.py
│   │   │   ├── define.py
│   │   │   ├── prompt.py
│   │   │   └── tools.py
│   │   └── resource_admin/     # 资源行政Agent - 合同初审与法务支持
│   │       ├── __init__.py
│   │       ├── define.py
│   │       ├── prompt.py
│   │       └── tools.py
│   │
│   ├── 📁 DevTeam/             # 开发团队工作区
│   ├── 📁 FinanceDept/         # 财务部门工作区
│   ├── 📁 GeneralOffice/       # 总经办工作区
│   │   ├── 📁 Docs/            # 🏢 公司各种文件
│   │   │   ├── 📁 YDS-AI-战略规划/        # 公司战略方向
│   │   │   ├── 📁 YDS-AI-组织与流程/      # 组织架构与流程
│   │   │   ├── 📁 YDS-AI-技术文档/        # 技术规范文档
│   │   │   ├── 📁 YDS-AI-合规与法务/      # 法务合规文档
│   │   │   ├── 📁 YDS-AI-对外文档/        # 对外展示文档
│   │   │   ├── 📁 YDS-AI-会议记录/        # 会议纪要记录
│   │   │   └── 📁 模板库/                 # 标准模板库
│   │   ├── 📁 logs/            # 🏷️ 各部门工作记录
│   │   ├── 📁 config/          # 🔧 公司开办运营环境配置
│   │   ├── 📁 meetings/        # 📅 各种工作会议
│   │   └── 📁 bak/             # 🗄️ 档案室
│   ├── 📁 MarketingDept/       # 市场部门工作区
│   ├── 📁 PlanningDept/        # 企划部门工作区
│   └── 📁 ResourceAdminDept/   # 资源管理部门工作区
│       ├── 📁 downloads/       # 下载资源管理
│       └── 📁 config/          # 部门配置文件
│
├── 📁 projects/                # 🚀 项目容器
│   ├── 📁 001-dewatermark-ai/      # 视频去水印项目
│   │   ├── 📁 docs/            # 项目文档
│   │   ├── 📁 src/             # 前端源码（Tauri Web）
│   │   ├── 📁 src-tauri/       # 后端源码（Rust）
│   │   ├── 📁 servers/         # 多设备部署配置
│   │   │   ├── guiyang-server/ # 贵阳台式机配置
│   │   │   └── local-pc/       # 本地PC配置
│   │   ├── 📁 assets/          # 项目资源与测试素材
│   │   ├── 📁 output/          # 输出结果
│   │   ├── 📁 debug/           # 调试信息
│   │   ├── 📁 backups/         # 项目备份
│   │   ├── package.json        # 前端依赖配置
│   │   └── README.md           # 项目说明
│   └── 📁 templates/           # 项目模板库
│       └── tauri-python-ai/    # 标准AI项目模板
│
├── 📁 tools/                   # 🔧 工具集合
│   ├── 📁 -sub/                # 专业工具模块集合
│   │   ├── 📁 api/             # API相关工具
│   │   ├── 📁 backup/          # 备份工具
│   │   ├── 📁 check/           # 检查验证工具
│   │   ├── 📁 config/          # 配置管理工具
│   │   ├── 📁 data/            # 数据处理工具
│   │   ├── 📁 database/        # 数据库工具
│   │   ├── 📁 deployment/      # 部署工具
│   │   ├── 📁 docs/            # 文档生成工具
│   │   ├── 📁 documentation/   # 文档管理工具
│   │   ├── 📁 git/             # Git工具
│   │   ├── 📁 git_tools/       # Git扩展工具
│   │   ├── 📁 integration/     # 集成工具
│   │   ├── 📁 log_management/  # 日志管理工具
│   │   ├── 📁 monitoring/      # 监控工具
│   │   ├── 📁 performance/     # 性能工具
│   │   ├── 📁 project/         # 项目管理工具
│   │   ├── 📁 quality/         # 质量保证工具
│   │   ├── 📁 security/        # 安全工具
│   │   ├── 📁 testing/         # 测试工具
│   │   ├── 📁 utils/           # 通用工具
│   │   └── 📁 version/         # 版本管理工具
│   ├── 📁 backup/              # 备份相关工具
│   ├── 📁 config/              # 配置工具
│   ├── 📁 mcp/                 # MCP协议工具
│   ├── 📁 project/             # 项目创建工具
│   ├── 📁 git/                 # Git管理工具
│   ├── 📁 docs/                # 文档工具
│   └── 📄 *.py                 # 核心脚本文件
│
├── 📁 models/                  # 🤖 AI模型配置
│   ├── 📁 config/              # 模型配置文件
│   └── 📁 services/            # 模型服务
├── 📁 config/                  # 🔧 全局配置管理
├── 📁 utils/                   # 🛠️ 通用工具库
├── 📄 main.py                  # 🚀 主程序入口
├── 📄 requirements.txt         # 📦 Python依赖包
├── 📄 .gitignore              # 🚫 Git忽略规则
├── 📄 Readme.md               # 📖 项目说明
└── 📄 DIRECTORY_MAINTENANCE_GUIDE.md  # 📋 目录维护指南
```

## 🔧 核心模块说明

### 📚 Struc/ - 公司组织架构
YDS AI公司的组织架构模拟，包含：

#### 🤖 Agents/ - AI智能体定义和配置
模拟各部门负责人和专业角色的AI智能体：
- **ceo/**: 总经理（CEO）智能体 - 目标拆解与任务分发、进度监控与风险预警、决策协调与结果整合
- **dev_team/**: 开发团队智能体群组
  - **dev_architect/**: 开发架构师智能体 - 系统架构设计与技术选型
  - **dev_coder/**: 开发工程师智能体 - 代码编写与功能实现
  - **dev_tester/**: 测试工程师智能体 - 质量保证与测试自动化
- **finance_director/**: 财务总监智能体 - 成本核算与预算管理、收支记录与财务分析、投资回报评估
- **marketing_director/**: 市场总监智能体 - 用户画像与需求分析、内容创作与社媒运营、客户跟进与销售支持
- **planning_director/**: 企划总监智能体 - 市场分析与可行性研究、商业计划生成、竞品分析与策略建议
- **resource_admin/**: 资源行政智能体 - 合同初审与法务支持、会议安排与资源协调、项目管理与进度跟踪

#### 🏢 部门工作区
- **GeneralOffice/**: 总经办工作区，包含公司级文档和统一日志管理
- **DevTeam/**: 开发团队工作区
- **FinanceDept/**: 财务部门工作区  
- **MarketingDept/**: 市场部门工作区
- **PlanningDept/**: 企划部门工作区
- **ResourceAdminDept/**: 资源行政部门工作区

### 🚀 projects/ - 项目容器
所有创业项目的统一管理目录：
- **001-dewatermark-ai/**: 视频去水印AI工具项目
- **templates/**: 项目模板库，提供标准化的项目结构

### ⚙️ tools/ - 自动化工具集
全局运维和开发工具：
- **check/**: 环境检查与健康监控
- **config/**: 配置管理工具
- **docs/**: 文档生成与处理工具
- **git/**: 版本控制自动化
- **mcp/**: MCP服务器集成工具
- **project/**: 项目创建与管理工具

### 🤖 models/ - AI模型配置
AI服务的配置与管理：
- **config/**: API密钥和模型配置
- **services/**: LLM路由和服务接口

### 🛠️ utils/ - 通用工具库
跨项目的通用功能模块：
- **logger.py**: 统一日志记录
- **tts.py**: 文本转语音功能

## 🚀 AI协作意义

### 1. 标准化协作
- 统一的目录结构便于AI Agent理解项目组织
- 标准化的文件命名和分类规则
- 清晰的职责边界和工作流程

### 2. 知识管理
- 集中化的文档管理（Struc/GeneralOffice/Docs/）
- 结构化的日志存储（Struc/GeneralOffice/logs/）
- 版本化的配置管理（tools/structure_config.yaml）

### 3. 自动化运维
- 统一的工具集管理（tools/）
- 自动化的备份与恢复机制
- 智能化的环境检查与维护

### 4. 项目管理
- 标准化的项目模板（projects/templates/）
- 统一的项目生命周期管理
- 跨项目的资源共享与复用

## 📋 使用指南

### 新项目创建
```bash
python tools/project/create_project.py --name [项目名] --template tauri-python-ai
```

### 环境检查
```bash
python tools/check/env_ready.py
```

### 目录结构更新
```bash
python tools/update_structure.py
```

### Git环境配置
```bash
python tools/setup_git_environment.py
```

---

## 📊 项目统计信息

### 目录结构统计
- **总项目数**: 3,704 项
- **目录数量**: 658 个
- **文件数量**: 3,046 个
- **扫描深度**: 完整递归扫描
- **结构合规率**: 100%

### 核心模块分布
- **AI智能体**: 6 个专业角色
- **部门工作区**: 5 个业务部门
- **工具模块**: 16 个专业工具类别
- **项目容器**: 动态扩展支持
- **模型库**: 统一模型管理

*统计数据来源: 《动态目录结构清单》.md*  
*数据更新时间: 2025年10月22日*

---

*本文档与项目架构设计和动态目录结构清单保持同步更新*  
*最后更新: 2025年10月22日*