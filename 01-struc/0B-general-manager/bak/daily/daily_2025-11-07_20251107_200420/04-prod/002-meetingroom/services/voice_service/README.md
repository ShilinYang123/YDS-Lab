# MeetingRoom 语音服务（002-meetingroom/services/voice_service）

该目录为会议室项目（编号 002）的语音服务生产包。基于 03-dev/JS001-meetingroom/servers/voice_service.py 服务化封装，提供生产环境可执行的结构与启动脚本；统一归位至 04-prod/002-meetingroom/services/voice_service。

## 目录结构

- config/
  - voice_service_config.json：语音服务配置（端口、采样率、模型/驱动等）。
  - yds_ai_config.yaml：通用系统配置（如需要）。
- src/
  - voice_service.py：服务主程序（从开发版复制）。
- scripts/
  - start.py：生产环境启动脚本（Python）。
- docs/
  - 运维说明与变更记录：包含部署、日志、健康检查与告警策略（建议按版本维护 CHANGELOG）。
  - 迁移提示：本目录替代旧的 04-prod/002-voice-service 结构，请统一在此维护。

## 启动方式

1. 确认已安装依赖（参考仓库根目录 requirements.txt）：
   ```bash
   pip install -r requirements.txt
   ```
2. 在本目录运行：
   ```bash
   python scripts/start.py
   ```

默认会加载 `config/voice_service_config.json`。如需自定义配置路径，可使用环境变量：

- VOICE_SERVICE_CONFIG：配置文件绝对或相对路径

## 配置说明

- `config/voice_service_config.json`：生产环境参数（端口、线程、日志级别、鉴权等）。
- `config/yds_ai_config.yaml`：如服务依赖通用系统配置，可在此维护。

## 运维建议

- 将启动命令挂入系统服务或计划任务（Windows 可使用 Task Scheduler 或 NSSM）。
- 建议将服务日志与审计记录纳入 04-prod/reports。后续可扩展为以项目编号归档日志（002-meetingroom 对应目录），并以服务名 voice_service 分目录。

## 变更管理

  - 开发到生产的差异仅体现在目录结构与启动方式，源代码保持与 03-dev/JS001-meetingroom/servers/voice_service.py 同步。
  - 若曾经使用 04-prod/002-voice-service，请迁移到本目录并在旧目录 README 中加入迁移说明（如仍存在）。
- 如需在生产引入额外的守护/监控，请在 scripts/ 与 docs/ 下新增对应说明与脚本。