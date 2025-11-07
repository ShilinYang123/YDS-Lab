# 多Agent协作运行指南（YDS-Lab）

本指南用于说明如何使用轻量协作编排器 tools/agents/run_collab.py 在不依赖 CrewAI 的情况下，快速组织“每日晨会/紧急会议”并自动生成、归档标准化会议纪要。

适用人群：总经办、技术负责人、运维同学，以及需要集成多部门 AI Agent 协作流程的开发者。

---

## 1. 架构与文件位置

- 协作编排器：
  - 路径：tools/agents/run_collab.py
  - 作用：按固定顺序调度各部门 Agent（CEO/企划/财务/开发/市场/资源行政），生成会议纪要并归档。

- 部门 Agent Prompt：
  - CEO：01-struc/Agents/ceo/prompt.py
  - 企划：01-struc/Agents/planning_director/prompt.py
  - 财务：01-struc/Agents/finance_director/prompt.py
  - 开发：01-struc/Agents/dev_team/dev_director/prompt.py
  - 市场：01-struc/Agents/marketing_director/prompt.py
  - 资源行政：01-struc/Agents/resource_admin/prompt.py

- LLM 路由（后端适配）：
  - 路径：models/services/llm_router.py
  - 说明：统一封装模型调用，可路由至 Shimmy / Ollama / OpenAI 兼容接口等后端。

- 战略规划摘要来源（作为会议上下文）：
  - 路径：01-struc/docs/YDS-AI-战略规划/
  - 默认读取：YDS AI公司建设与项目实施完整方案（V1.0）.md（前若干字符）

- 会议纪要归档：
  - 归档函数：01-struc/Agents/ceo/tools.py::archive_meeting
  - 保存位置：
- Markdown：01-struc/docs/meetings/MTG-YYYYMMDD-HHMM.md
- JSON：01-struc/docs/meetings/MTG-YYYYMMDD-HHMM.json（自动同步生成，包含结构化区块与表格解析）

参考文档：01-struc/docs/LLM路由与后端选择（Shimmy-Ollama）使用说明.md

---

## 2. 前置条件

1) 模型后端已就绪：
   - 已在本机启动 Shimmy / Ollama / 其他 OpenAI 兼容推理后端。
   - 按照“LLM 路由与后端选择”文档完成 llm_router 配置。

2) Python 环境：
   - Python 3.10+（建议）
   - 无额外第三方依赖，脚本通过内部路由直接调用模型。

3) 仓库目录结构：
   - 本脚本会在运行时自动注入 REPO_ROOT 至 sys.path，支持从任意工作目录执行。

---

## 3. 快速上手（Windows PowerShell 示例）

在仓库根目录执行：

1) 每日晨会（默认项目名 DeWatermark AI）

```
python tools/agents/run_collab.py --meeting daily --project "DeWatermark AI"
```

2) 紧急会议（必须提供原因 --reason）

```
python tools/agents/run_collab.py --meeting emergency --reason "开发进度延迟2天" --project "DeWatermark AI"
```

3) 指定默认模型（与 llm_router 后端保持一致）

```
python tools/agents/run_collab.py --meeting daily --model "qwen2:7b-instruct"
```

4) 为“行动项与决策”指定单独模型（可与 --model 不同）

```
python tools/agents/run_collab.py --meeting daily --actions-model "qwen2:7b-instruct"
```

脚本会在控制台打印归档路径，并输出前 2000 字的预览。

5) 自定义参会角色与议程（逗号分隔）

```
python tools/agents/run_collab.py --meeting daily \
  --participants "总经理(CEO),企划总监,财务总监,开发总监,市场总监,资源与行政" \
  --agenda "开场说明,部门汇报,行动项与决策"
```

6) 绑定项目目录（用于元信息标注与后续扩展）

```
python tools/agents/run_collab.py --meeting daily --project "DeWatermark AI" --project-id "001-dewatermark-ai"
```

---

## 4. 产物说明

- 保存路径：01-struc/docs/meetings/
- 命名规范：MTG-YYYYMMDD-HHMM.md
- 内容结构：
  1) 【会议信息】会议类型/项目/时间/参会角色/议程
  2) 【晨会开场】（或【会议触发】/【会议开场】）
  3) 【部门汇报摘要】（Daily 包含 企划/财务/开发/市场/资源行政；Emergency 侧重 开发/财务/资源行政）
  4) 【行动项与决策】Markdown 表格（见下文）
  5) 【会议时间】

示例（表头固定）：

```
| 编号 | 事项 | 责任部门/人 | 优先级 | 截止日期 | 依赖 | 风险与应对 | 下一步 |
|---|---|---|---|---|---|---|---|
| 1 | 示例事项 | 示例部门 | 高 | 2025-10-30 | 示例依赖 | 示例风险 | 示例下一步 |
```

---

## 5. “行动项与决策”生成逻辑

- 专用“会议秘书”System Prompt：严格要求“只输出Markdown表格”。
- 可通过 --actions-model 为本节单独指定模型，避免受其它段落风格影响。
- 内置表格回退机制：
  - 若大模型未按要求输出表格（缺少“|”或“---”或表头），将自动回退到内置的保底表格，确保结构稳定。
- 优先级取值限定为：高/中/低；日期格式：YYYY-MM-DD；最多 8 条。

---

## 6. 常见问题与排错

1) 提示“紧急会议需要 --reason”：
   - 只有在 --meeting emergency 时必须提供 --reason。

2) 提示找不到模块（ModuleNotFoundError）：
   - 本脚本已自动修正导入路径，如仍报错，请确认从仓库根目录执行，或检查工具路径是否被移动。

3) 模型未响应或生成风格不一致：
   - 检查 llm_router 对应后端是否已启动。
   - 使用 --model/--actions-model 指定更稳健的后端或模型别名。

4) 产物未生成：
   - 确认 01-struc/Agents/ceo/tools.py::archive_meeting 存在且有写权限。
   - 自 2025-10-28 起，同时生成 Markdown 与 JSON 两类产物（JSON 生成失败不影响 Markdown 产物）。

---

## 7. 扩展与二次开发

1) 新增部门：
   - 在 01-struc/Agents/<dept>/prompt.py 中提供系统提示词，
   - 在 run_collab.py 相应场景（daily/emergency）中插入调用；
   - 追加到【会议信息】参会角色与【部门汇报摘要】列表。

2) 调整议程或参会名单：
   - 修改 run_collab.py 中 _meeting_meta_block 的 agenda 或 participants。

3) 调整“行动项与决策”口径：
   - 修改 _summarize_actions 的 system prompt 要求（表头、字段含义等）。

4) 定时化：
   - 可用 Windows 任务计划程序定时执行脚本：
     - PowerShell：scripts/schedule_daily_meeting.ps1（支持参数透传 --project/--model/--actions-model/--participants/--agenda/--project-id）
     - 批处理：scripts/schedule_daily_meeting.bat（调用上方 PowerShell 脚本）
- 日志输出默认写入：01-struc/0B-general-manager/logs/daily_meeting_YYYYMMDD-HHMM.log

---

## 8. 与既有工具的关系

- generate_meeting_log.py（tools/docs/）提供模板化日志生成与导出功能，适合按“会议类型/参会人/格式”快速出模板；
- run_collab.py 聚焦“基于部门 Agent 自动输出内容 + 汇总行动项 + 统一归档”，适合“日常自动化晨会/应急纪要”。

两者可并行使用：前者用于资料模板化与外发格式，后者负责自动拉取各部门当日结论并固化记录。

---

## 9. CLI 参数参考

```
--meeting        daily|emergency       会议类型（默认 daily）
--reason         <string>              紧急会议原因（仅 emergency 必填）
--project        <string>              项目名称（默认 "DeWatermark AI"）
--model          <string>              默认模型（llm_router 路由别名或模型ID）
--actions-model  <string>              “行动项与决策”独立模型（默认与 --model 相同）
--participants   <csv>                 自定义参会角色，逗号分隔（覆盖默认参会名单）
--agenda         <csv>                 自定义会议议程，逗号分隔（覆盖默认议程）
--project-id     <string>              绑定项目目录（如 001-dewatermark-ai），将写入【会议信息】
```

---

## 10. 变更记录

- 2025-10-28
  - 首版：支持每日/紧急会议；新增会议信息块；支持“行动项与决策”专属模型与回退表格机制。
  - 新增：CLI 自定义 --participants/--agenda；可选绑定 --project-id。
  - 新增：会议纪要 JSON 同步归档（含结构化区块与表格解析）。
  - 新增：定时执行脚本 scripts/schedule_daily_meeting.ps1/.bat。