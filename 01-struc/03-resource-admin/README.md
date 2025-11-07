# 03-resource-admin

资源行政部门（Resource & Admin Department）

目录定位与职责
- 文档治理（统一归档路径与版本合规）
- 资产与资源管理（配置、密钥、访问控制）
- 系统运行维护（脚本校验与执行结果归档）

组织协作接口
- 关联可执行角色：`01-struc/Agents/resource_admin/`（资源行政智能体）；协同各部门 Agents（如 CEO、企划总监、财务总监、开发团队、市场总监）进行治理与支持。
- 工作流参考：`01-struc/Agents/collaboration_workflows.yaml`

文档与日志归档
- 统一文档归档路径：`01-struc/docs/`
- 统一日志归档路径：`01-struc/0B-general-manager/logs/`
- 建议在本目录建立 `notes/` 用于部门备忘；生产文档与日志统一归档至以上路径。

路径约定
- 严禁使用旧路径 `GeneralOffice/Docs`；已统一为 `01-struc/docs/` 与 `01-struc/0B-general-manager/logs/`
- Windows 绝对路径示例：`S:\\YDS-Lab\\01-struc\\docs\\`

运行参与说明
- 本目录通常不包含可执行代码；执行由相关 Agents 完成（资源管理员为主）。
- 平台校验脚本位于 `tools/final_system_validation.py`，由资源管理员发起执行并归档报告。

版本与备份
- 历史备份位于 `backups/legacy/`，不参与运行；详见 `backups/legacy/README.md`。
- 如需恢复历史内容，请在变更记录中注明来源与日期。

快速索引
- 资源管理员智能体：`01-struc/Agents/resource_admin/`
- 协作工作流：`01-struc/Agents/collaboration_workflows.yaml`
- 统一文档归档：`01-struc/docs/`
- 统一日志：`01-struc/0B-general-manager/logs/`
- 平台校验脚本：`tools/final_system_validation.py`

Trae 平台适配说明
- 与平台协作规范保持一致：提示词统一使用 YAML 多行块标量；路径引用统一为 `01-struc/docs/` 与 `01-struc/0B-general-manager/logs/`。
- 需要平台验证时，使用 `tools/final_system_validation.py` 进行一致性检查；报告输出为 `final_validation_report.json` 与 `final_validation_report.md`。