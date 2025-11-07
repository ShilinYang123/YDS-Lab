# 002-meetingroom

本目录为 MeetingRoom 项目的生产包根目录。根据编号规范，相关子服务（如语音服务）统一纳入本项目目录下进行管理。

目录结构（当前已纳入）：
- services/voice_service/
  - src/voice_service.py
  - config/voice_service_config.json, yds_ai_config.yaml
  - scripts/start.py
  - docs/, README.md

运维建议：
- 各子服务的启动脚本统一置于其内部 scripts/ 目录；项目级的部署文档与流程可放在本 README 与 docs/ 下。
- 项目产出（日志、报告、发布包）建议在项目内部归档后，再按需汇总到 04-prod/reports 或 04-prod/releases。

后续扩展：
- 若 MeetingRoom 还需其他子模块（UI、调度、协作代理等），建议按 services/ 或 modules/ 方式纳入，并保持统一配置与启动规范。