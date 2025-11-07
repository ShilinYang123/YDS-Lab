项目名称：Trae平台多智能体开发团队构建（开发目录说明）

目标
- 搭建面向 Trae 平台的多智能体协同开发目录结构，统一文档与代码规范，保障快速交付。

目录结构说明（一级）
- docs：项目中文文档（项目说明、实施计划、角色分工、里程碑与验收等）
- design：系统架构与交互设计、技术选型与依赖说明
- src：源代码（agents、mcp、services、utils 等）
- configs：配置文件（YAML/JSON 等）
- scripts：工具与初始化脚本
- tests：测试（unit、integration）
- examples：示例与演示
- deployments：部署目录（dev、staging、prod）
- reports：报告与验证结果
- templates：统一文档模板

快速开始
1) 在 scripts 目录编写初始化脚本，并在《开发环境初始化脚本说明》中记录使用方法。
2) 在 docs 目录完善《项目说明书》《实施计划》《角色职责与分工》《里程碑与验收标准》。
3) 在 src 目录新增模块代码，建议按 agents/mcp/services/utils 分类组织。
4) 在 tests 目录补充单元与集成测试用例。

约定与规范
- 文档命名一律用中文（遵循您的要求）。
- 代码规范遵循仓库通用规则，必要时加入 flake8/pytest 等质量保障工具。
- 每次结构或脚本变更后执行 up.py --finalize 更新《动态目录结构清单》。