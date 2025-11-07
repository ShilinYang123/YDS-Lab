# 0B-general-manager

总经理办公室（General Manager Office）

目录定位与职责
- 战略执行与跨部门协同
- 目标拆解与绩效管理
- 资源统筹与风险应对

组织协作接口
- 关联可执行角色：`01-struc/Agents/ceo/`（CEO/总经理角色），协同 `01-struc/Agents/resource_admin/` 进行文档与资源治理。
- 工作流参考：`01-struc/Agents/collaboration_workflows.yaml`

文档与日志归档
- 统一文档归档路径：`01-struc/docs/`
- 统一日志归档路径：`01-struc/0B-general-manager/logs/`
- 建议在本目录建立 `notes/` 用于办公室备忘；生产文档与日志统一归档至以上路径。

路径约定
- 严禁使用旧路径 `GeneralOffice/Docs`；已统一为 `01-struc/docs/` 与 `01-struc/0B-general-manager/logs/`
- Windows 绝对路径示例：`S:\YDS-Lab\01-struc\docs\`

运行参与说明
- 本目录不包含可执行代码；执行由相关 Agents 完成（主要为 CEO/总经理与资源管理员）。

版本与备份
- 历史备份位于 `backups/legacy/`，不参与运行；详见 `backups/legacy/README.md`。
- 如需恢复历史内容，请在变更记录中注明来源与日期。

快速索引
- CEO/总经理可执行角色：`01-struc/Agents/ceo/`
- 资源管理员：`01-struc/Agents/resource_admin/`
- 协作工作流：`01-struc/Agents/collaboration_workflows.yaml`
- 统一文档归档：`01-struc/docs/`
- 统一日志：`01-struc/0B-general-manager/logs/`

Trae 平台适配说明
- 与平台协作规范保持一致：提示词统一使用 YAML 多行块标量；路径引用统一为 `01-struc/docs/` 与 `01-struc/0B-general-manager/logs/`。
- 需要平台验证时，使用 `tools/final_system_validation.py` 进行一致性检查。
