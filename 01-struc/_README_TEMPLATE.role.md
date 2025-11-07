# 顶层角色目录 README 模板

将本模板复制到目标角色目录并按需替换尖括号中的占位符。

示例文件名：`README.md`

---

# <ROLE_DIR_NAME>

<ROLE_CN_NAME>（<ROLE_EN_NAME>）

目录定位与职责
- <职责一>
- <职责二>
- <职责三>

组织协作接口
- 关联可执行角色：<例如 `01-struc/Agents/ceo/` 或 `01-struc/Agents/resource_admin/`>
- 工作流参考：`01-struc/Agents/collaboration_workflows.yaml`

文档与日志归档
- 统一文档归档路径：`01-struc/docs/`
- 统一日志归档路径：`01-struc/0B-general-manager/logs/`
- 建议在本目录建立 `notes/` 用于办公室备忘；生产文档与日志统一归档至以上路径。

路径约定
- 严禁使用旧路径 `GeneralOffice/Docs`；已统一为 `01-struc/docs/` 与 `01-struc/0B-general-manager/logs/`
- Windows 绝对路径示例：`S:\\YDS-Lab\\01-struc\\docs\\`

运行参与说明
- 本目录通常不包含可执行代码；执行由相关 Agents 完成。

版本与备份
- 历史备份位于 `backups/legacy/`，不参与运行；详见 `backups/legacy/README.md`。
- 如需恢复历史内容，请在变更记录中注明来源与日期。

快速索引
- 相关 Agents 入口：`01-struc/Agents/<agent_name>/`
- 协作工作流：`01-struc/Agents/collaboration_workflows.yaml`
- 统一文档归档：`01-struc/docs/`
- 统一日志：`01-struc/0B-general-manager/logs/`

Trae 平台适配说明
- 与平台协作规范保持一致：提示词统一使用 YAML 多行块标量；路径引用统一为 `01-struc/docs/` 与 `01-struc/0B-general-manager/logs/`。
- 需要平台验证时，使用 `tools/final_system_validation.py` 进行一致性检查。