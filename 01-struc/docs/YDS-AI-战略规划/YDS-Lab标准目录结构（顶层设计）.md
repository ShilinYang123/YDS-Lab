# YDS-Lab 标准目录结构（顶层设计）

> **文档版本**: V4.0  
> **更新时间**: 2025年1月15日  
> **项目根目录**: `S:\YDS-Lab`  
> **架构类型**: AI原生分布式协作架构

## 🏗️ 架构概述

YDS-Lab采用AI原生的分布式协作架构设计，通过Trae IDE集成多智能体系统，结合标准化的目录结构和自动化工具链，实现"一个人+一群AI"的高效协作模式。

核心特色是**项目生命周期管理体系**：从项目开发（projects/）→客户交付（output/），实现全流程管控。同时通过Struc/组织架构模拟真实公司运作，提供完整的AI协作环境。

## 🏢 公司简介

- 公司理念与治理哲学：参见《01-YDS-Lab AI公司简介》
  - [打开简介（Markdown）](./01-YDS-Lab AI公司简介.md)
- 治理原则图示（阴阳五行协同图）：参见《02-治理原则图示（阴阳五行协同图）》
  - [查看图示（Markdown）](./02-治理原则图示（阴阳五行协同图）.md)

## 📁 标准目录结构
```
YDS-Lab/
├── 📁 Struc/                   # 🏢 公司组织架构与AI协作环境
│   ├── 📁 Agents/              # 🤖 AI智能体定义和配置
│   ├── 📁 DevTeam/             # 开发团队工作区
│   ├── 📁 FinanceDept/         # 财务部门工作区
│   ├── 📁 GeneralOffice/       # 总经办工作区
│   ├── 📁 Log/                 # 🏷️ 系统日志与工作记录
│   ├── 📁 MCPCluster/          # MCP服务器集群配置
│   ├── 📁 MarketingDept/       # 市场部门工作区
│   ├── 📁 PlanningDept/        # 企划部门工作区
│   ├── 📁 ResourceAdminDept/   # 资源管理部门工作区
│   ├── 📁 Security/            # 安全配置与权限管理
│   ├── 📁 SharedWorkspace/     # 共享工作空间
│   ├── 📁 TraeAgents/          # Trae IDE专用AI智能体
│   └── 📁 Workflow/            # 工作流程定义
├── 📁 output/                  # 📦 客户项目交付成果区
│   ├── 001-dewatermark-ai/     # 客户项目交付成果（按00x序号）
│   │   ├── deliverables/       # 交付物
│   │   ├── documentation/      # 交付文档
│   │   ├── assets/             # 资源文件
│   │   └── versions/           # 版本记录
│   ├── 002-meetingroom-system/ # 会议室管理系统交付成果
│   ├── 003-ai-assistant/       # AI助手项目交付成果
│   ├── 004-memory-system-integration/ # 记忆系统集成交付成果
│   ├── 005-data-analysis-platform/ # 数据分析平台交付成果
│   ├── 006-automation-tools/   # 自动化工具交付成果
│   ├── 007-web-application/    # Web应用交付成果
│   ├── 008-mobile-app/         # 移动应用交付成果
│   ├── 009-api-services/       # API服务交付成果
│   ├── 010-showcase-materials/ # 展示材料交付成果
│   └── README.md               # 交付成果目录说明
├── 📁 03-proc/                 # 🚀 流程与发布工区
│   ├── 001-dewatermark-ai/     # 生产环境部署（按00x序号）
│   ├── 002-meetingroom-system/ # 会议室管理系统生产部署
│   ├── 003-ai-assistant/       # AI助手项目生产部署
│   ├── 004-memory-system-integration/ # 记忆系统集成生产部署
│   └── ...                     # 其他项目生产部署
├── 📁 projects/                # 🛠️ 项目开发工作区
│   ├── 001-dewatermark-ai/     # 开发中的项目（按00x序号）
│   │   ├── docs/               # 项目文档
│   │   ├── src/                # 前端源码（Tauri Web）
│   │   ├── src-tauri/          # 后端源码（Rust）
│   │   ├── servers/            # 多设备部署配置
│   │   ├── assets/             # 项目资源与测试素材
│   │   ├── output/             # 输出结果
│   │   ├── debug/              # 调试信息
│   │   ├── backups/            # 项目备份
│   │   ├── package.json        # 前端依赖配置
│   │   └── README.md           # 项目说明
│   ├── JS-004-本地AI模型部署与Trae IDE集成/ # JavaScript项目示例
│   └── templates/              # 项目模板库
│       └── tauri-python-ai/    # 标准AI项目模板
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
├── 📁 Training/                # 🎓 训练数据与模型训练
├── 📁 utils/                   # 🛠️ 通用工具库
├── 📄 main.py                  # 🚀 主程序入口
├── 📄 requirements.txt         # 📦 Python依赖包
├── 📄 .gitignore              # 🚫 Git忽略规则
├── 📄 Readme.md               # 📖 项目说明
└── 📄 DIRECTORY_MAINTENANCE_GUIDE.md  # 📋 目录维护指南
```

## 🔧 核心模块说明

### 🚀 项目生命周期管理体系

#### 📁 projects/ - 项目开发工作区
- **用途**：项目开发阶段的工作空间
- **命名规范**：`00x-项目名称`（如`001-dewatermark-ai`）
- **内容**：源代码、开发文档、测试数据、调试信息
- **流程**：需求分析 → 架构设计 → 编码实现 → 单元测试 → 集成测试

#### 📁 03-proc/ - 流程与发布工区
- **用途**：项目生产发布与流程管理（含发布产物与过程文档）
- **命名规范**：与projects/保持一致的`00x-项目名称`
- **内容**：发布记录（reports/）、版本发布（releases/）、运维与流程文档
- **流程**：流程编排 → 构建发布 → 上线验证 → 运维监控

#### 📁 output/ - 客户项目交付成果区
- **用途**：存放最终交付给客户的项目成果
- **命名规范**：与projects/保持一致的`00x-项目名称`
- **内容**：交付物、使用文档、安装包、培训材料
- **流程**：成果整理 → 质量检查 → 文档完善 → 客户交付

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

### ⚙️ tools/ - 自动化工具集
全局运维和开发工具：
- **check/**: 环境检查与健康监控
- **config/**: 配置管理工具
- **docs/**: 文档生成与处理工具
- **git/**: 版本控制自动化
- **mcp/**: MCP服务器集成工具
- **project/**: 项目创建与管理工具

### 🤖 models/ - AI模型配置与路径映射

**设计理念**：智能路径映射系统，实际模型存储在 `S:\LLM`，项目内仅保存配置与映射关系

**核心功能**：
- **路径解析**：通过 `utils/model_path_resolver.py` 自动将模型调用转向 `S:\LLM`
- **配置管理**：存储模型的路径映射、API配置和服务接口
- **符号链接**：支持创建指向外部模型的符号链接（需管理员权限）
- **兜底机制**：当外部模型不可用时，可使用项目本地备份

**路径优先级**：
1. 外部配置文件（`config/external_models.json`）
2. 环境变量（`MODELS_PATH`、`SHIMMY_HOME`）
3. 统一模型路径（`S:\LLM\models\{model_name}`）
4. 项目本地路径（兜底方案）

### 🛠️ utils/ - 通用工具库
跨项目的通用功能模块：
- **logger.py**: 统一日志记录
- **tts.py**: 文本转语音功能

### 🎓 Training/ - 训练数据与模型训练
AI模型训练相关资源：
- 训练数据集
- 模型训练脚本
- 训练结果与评估

### 💾 备份存储策略
系统备份与恢复统一由总经办管理：
- 项目备份：存储在 `01-struc/GeneralOffice/bak/`
- 配置备份：存储在 `01-struc/GeneralOffice/bak/`
- 数据备份：存储在 `01-struc/GeneralOffice/bak/`

## 🚀 AI协作意义

### 1. 标准化协作
- 统一的目录结构便于AI Agent理解项目组织
- 标准化的文件命名和分类规则
- 清晰的职责边界和工作流程

### 2. 知识管理
- 集中化的文档管理（01-struc/docs/）
- 结构化的日志存储（01-struc/0B-general-manager/logs/）
- 版本化的配置管理（config/structure_config.yaml）

### 3. 自动化运维
- 统一的工具集管理（tools/）
- 自动化的备份与恢复机制
- 智能化的环境检查与维护

### 4. 项目管理
- 标准化的项目模板（projects/templates/）
- 统一的项目生命周期管理
- 跨项目的资源共享与复用

### 5. 生命周期管控
- **开发阶段**（projects/）：需求到测试的完整开发流程
- **部署阶段**（03-proc/）：发布流程与版本管理
- **交付阶段**（output/）：客户成果整理与交付

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

### 项目生命周期管理
1. **开发阶段**：在`projects/00x-项目名/`中进行开发
2. **部署阶段**：配置`03-proc/00x-项目名/`发布流程与产物
3. **交付阶段**：整理`output/00x-项目名/`交付成果

---

## 📊 项目统计信息

### 目录结构统计
- **项目生命周期目录**: 3个核心目录（projects/、03-proc/、output/）
- **AI智能体**: 6个专业角色
- **部门工作区**: 6个业务部门
- **工具模块**: 16个专业工具类别
- **项目容器**: 动态扩展支持（按00x序号）
- **模型库**: 统一模型管理

### 核心特性
- **项目生命周期管理**: 从开发到交付的全流程管控
- **客户项目标准化**: 统一的00x序号命名规范
- **AI智能体协作**: 6个专业AI Agent协同工作
- **工具链集成**: MCP协议支持与自动化工具

*统计数据来源: 实际目录结构扫描*  
*数据更新时间: 2025年11月2日*

---

*本文档与项目架构设计和动态目录结构清单保持同步更新*  
*最后更新: 2025年11月2日*