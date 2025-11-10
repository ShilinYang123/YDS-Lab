# YDS-Lab 项目结构文档

生成时间: 2025-11-10 09:23:59

## 项目概览

YDS-Lab 是一个多智能体协作系统，包含以下主要组件：

- 总文件数: 65910
- Python文件数: 239
- 主要目录: 16 个
- 配置文件: 1 个

## 目录结构

.
├── .editorconfig
├── .gitignore
├── README.md
├── ch.py
├── fi.py
├── requirements.txt
├── setup.cfg
├── st.py
└── up.py
├── 01-struc/
│   ├── 01-planning/
│   ├── 02-finance/
│   └── 03-resource-admin/
│   └── ... (10 更多)
├── 02-task/
│   ├── 001-长记忆系统开发/
│   ├── 002-meetingroom/
│   └── 003-Trae平台多智能体开发团队构建/
├── 03-dev/
│   ├── 001-dewatermark-ai/
│   ├── 001-memory-system/
│   └── 002-meetingroom/
│   └── ... (3 更多)
├── 04-prod/
│   ├── 001-memory-system/
│   ├── 002-meetingroom/
│   └── releases/
│   └── ... (2 更多)
├── Training/
│   ├── Assessments/
│   ├── Exercises/
│   └── Materials/
│   └── ... (1 更多)
├── backups/
│   ├── daily/
│   └── temp/
├── config/
│   └── security/
├── coverage/
│   └── lcov/
├── docs/
│   ├── logs/
│   ├── 技术标准/
│   └── 系统维护/
├── env/
├── logs/
│   ├── longmemory/
│   └── tmp/
├── models/
├── reports/
├── tmp/
│   ├── backup_staging_20251109-224327/
│   ├── backup_staging_20251109-224712/
│   └── memory_tests/
├── tools/
│   ├── LongMemory/
│   ├── agents/
│   └── archive/
│   └── ... (6 更多)
└── utils/

## 模块说明

### 01-struc/
项目核心结构目录，包含主要的智能体系统
- Python文件数: 84
- 总文件数: 284
- 子目录: 01-planning, 02-finance, 03-resource-admin, 04-dev-team, 05-marketing
  ... 还有 8 个

### 02-task/
未分类目录
- Python文件数: 14
- 总文件数: 37
- 子目录: 001-长记忆系统开发, 002-meetingroom, 003-Trae平台多智能体开发团队构建

### 03-dev/
开发中的项目和实验性功能
- Python文件数: 18
- 总文件数: 15802
- 子目录: 001-dewatermark-ai, 001-memory-system, 002-meetingroom, 003-Trae平台多智能体开发团队构建, scripts
  ... 还有 1 个

### 04-prod/
生产环境的项目和功能
- Python文件数: 11
- 总文件数: 5977
- 子目录: 001-memory-system, 002-meetingroom, releases, reports, scripts

### tmp/
未分类目录
- Python文件数: 62
- 总文件数: 43644
- 子目录: backup_staging_20251109-224327, backup_staging_20251109-224712, memory_tests

### tools/
项目工具脚本和辅助程序
- Python文件数: 41
- 总文件数: 107
- 子目录: agents, archive, check, config, git
  ... 还有 4 个

### utils/
未分类目录
- Python文件数: 5
- 总文件数: 9


## 配置文件

- **setup.cfg**: 配置文件

---
*本文档由自动化工具生成，最后更新: 2025-11-10 09:23:59*
