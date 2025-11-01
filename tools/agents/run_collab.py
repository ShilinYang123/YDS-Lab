#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YDS-Lab 多Agent部门协作编排器（轻量版，无依赖 CrewAI）

用途：
- 基于各部门现有 prompt 与 models.services.llm_router 路由能力，顺序生成部门汇报
- 汇总为一次“每日晨会/紧急会议”的会议纪要，并调用 CEO 工具归档到 Struc/GeneralOffice/meetings

运行示例：
  python tools/agents/run_collab.py --meeting daily
  python tools/agents/run_collab.py --meeting emergency --reason "开发进度延迟2天"

前置：
- 本地已启动可用的模型后端（Shimmy 或 Ollama）。参见 models/services/llm_router.py
"""

import os
import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# 动态修复导入路径，支持从任意工作目录运行
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# 导入部门提示词与工具
from Struc.Agents.ceo.prompt import GENERAL_MANAGER_PROMPT
from Struc.Agents.ceo.tools import archive_meeting, schedule_emergency_meeting

from Struc.Agents.planning_director.prompt import PLANNING_DIRECTOR_PROMPT
from Struc.Agents.finance_director.prompt import FINANCE_DIRECTOR_PROMPT
from Struc.Agents.marketing_director.prompt import MARKETING_DIRECTOR_PROMPT
from Struc.Agents.resource_admin.prompt import RESOURCE_ADMIN_PROMPT
from Struc.Agents.dev_team.dev_director.prompt import DEV_DIRECTOR_PROMPT

from models.services.llm_router import route_chat


STRATEGY_DOC = REPO_ROOT / "Struc" / "GeneralOffice" / "Docs" / "YDS-AI-战略规划" / "YDS AI公司建设与项目实施完整方案（V1.0）.md"


def read_strategy_brief(max_chars: int = 4000) -> str:
    """读取战略规划文档，截取前 max_chars 字符作为上下文。"""
    try:
        text = STRATEGY_DOC.read_text(encoding="utf-8", errors="ignore")
        return text[:max_chars].strip()
    except Exception:
        return ""


DEFAULT_MODEL = "qwen2:0.5b"


def call_agent(system_prompt: str, user_instruction: str, model: str = None) -> str:
    """统一的部门调用封装（OpenAI 风格 messages）。"""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_instruction},
    ]
    return route_chat(model=(model or DEFAULT_MODEL), messages=messages)


def _meeting_meta_block(
    meeting_type: str,
    project: str,
    participants: List[str],
    agenda: List[str],
    extra_meta_lines: Optional[List[str]] = None,
) -> str:
    now = datetime.now()
    human_time = now.strftime("%Y-%m-%d %H:%M")
    parts = [
        "【会议信息】",
        f"- 会议类型：{meeting_type}",
        f"- 项目：{project}",
        f"- 时间：{human_time}",
        f"- 参会角色：{', '.join(participants)}",
    ]
    if agenda:
        parts.append(f"- 议程：{', '.join(agenda)}")
    if extra_meta_lines:
        parts.extend(extra_meta_lines)
    return "\n".join(parts) + "\n"


def _summarize_actions(all_sections_md: str, model: str = None) -> str:
    """对部门汇总内容进行行动项与决策汇总（仅输出Markdown表格）。"""
    system_prompt = (
        "你是严谨的会议秘书。\n"
        "- 只输出一个Markdown表格，不能有任何其他文字或标题。\n"
        "- 表头：编号 | 事项 | 责任部门/人 | 优先级 | 截止日期 | 依赖 | 风险与应对 | 下一步。\n"
        "- 优先级取值仅限 高/中/低。截止日期格式 YYYY-MM-DD。最多8条。\n"
        "- 如信息不足，可基于常识轻量补全，但避免凭空捏造具体数据或姓名。\n"
    )
    instruction = (
        "基于以下‘部门汇报摘要’，生成‘行动项与决策’表格：\n\n" + all_sections_md
    )
    return call_agent(system_prompt, user_instruction=instruction, model=model)


def _fallback_actions_table(project: str) -> str:
    """当模型未按要求输出Markdown表格时，生成保底行动项表格。"""
    today = datetime.now().date()
    def d(n):
        return (today + timedelta(days=n)).strftime("%Y-%m-%d")
    rows = [
        ("1", "确认各部门关键结论与风险，发布会议纪要", "总经理/总经办", "高", d(0), "今日汇报内容", "信息遗漏导致误判→由各部门复核", "归档纪要并分发") ,
        ("2", "开发阻塞点排查与缓解方案落地", "开发总监", "高", d(1), "研发资源/问题清单", "核心模块迟滞→临时降级方案与并行排查", "提交修复计划与责任人"),
        ("3", "滚动更新预算与现金流日记账", "财务总监", "中", d(1), "收入与成本数据", "现金流断裂→预案与费用冻结线", "推送更新报表与建议"),
        ("4", "首月推广优先级与渠道分配", "企划/市场", "中", d(2), "投放预算/物料", "投放ROI低→小流量A/B测试", "确定本周渠道与素材清单"),
        ("5", "合同/合规与资源清单复核", "资源与行政", "中", d(2), "合同模板/权限表", "条款风险→法务条款加注与审批", "出具检查单与修订建议"),
    ]
    header = "| 编号 | 事项 | 责任部门/人 | 优先级 | 截止日期 | 依赖 | 风险与应对 | 下一步 |\n|---|---|---|---|---|---|---|---|"
    body = "\n".join(["| " + " | ".join(r) + " |" for r in rows])
    return header + "\n" + body


def _normalize_actions_table(text: str, project: str) -> str:
    """若不包含Markdown表格结构，则回退为保底表格。"""
    if "|" in text and ("编号" in text or "事项" in text) and "---" in text:
        # 看起来是Markdown表格，直接返回
        return text.strip()
    return _fallback_actions_table(project)


def make_daily_meeting_content(
    context_brief: str,
    reason: str = "",
    project: str = "DeWatermark AI",
    actions_model: str = None,
    participants: Optional[List[str]] = None,
    agenda: Optional[List[str]] = None,
    extra_meta_lines: Optional[List[str]] = None,
) -> str:
    """生成每日晨会会议纪要（串行调用各部门）。"""
    now = datetime.now()
    human_time = now.strftime("%Y-%m-%d %H:%M")

    # CEO 开场
    ceo_opening = call_agent(
        GENERAL_MANAGER_PROMPT.replace("{meeting_type}", "每日晨会"),
        user_instruction=(
            "你正在主持每日晨会。参考下方战略规划摘要进行组织：\n\n" + context_brief
        ),
    )

    # 各部门汇报
    plan_report = call_agent(
        PLANNING_DIRECTOR_PROMPT,
        user_instruction=(
            "请基于以下背景，为 DeWatermark AI 输出今日市场/企划汇报：\n\n" + context_brief
        ),
    )

    finance_report = call_agent(
        FINANCE_DIRECTOR_PROMPT,
        user_instruction=(
            "请基于以下背景，给出成本结构、收入预测与盈亏分析的今日更新：\n\n" + context_brief
        ),
    )

    dev_report = call_agent(
        DEV_DIRECTOR_PROMPT,
        user_instruction=(
            "请先整合架构师/编码工程师/测试工程师的内部同步，再输出开发部今日汇报：\n\n" + context_brief
        ),
    )

    marketing_report = call_agent(
        MARKETING_DIRECTOR_PROMPT,
        user_instruction=(
            "请基于以下背景，输出首月推广计划与用户增长的今日进展：\n\n" + context_brief
        ),
    )

    admin_report = call_agent(
        RESOURCE_ADMIN_PROMPT,
        user_instruction=(
            "请基于以下背景，输出合同/法务/资源协调与流程支持的今日更新：\n\n" + context_brief
        ),
    )

    # 先构造部门汇总块，供行动项总结器使用
    dept_sections = (
        "【部门汇报摘要】\n"
        + f"- 企划部：\n{plan_report}\n\n"
        + f"- 财务部：\n{finance_report}\n\n"
        + f"- 开发部：\n{dev_report}\n\n"
        + f"- 市场部：\n{marketing_report}\n\n"
        + f"- 资源行政部：\n{admin_report}\n"
    )

    # 行动项与决策
    actions_table = _summarize_actions(dept_sections, model=actions_model)
    actions_table = _normalize_actions_table(actions_table, project)

    # 会议纪要合成（遵循CEO输出模板的结构关键字）
    content = []
    content.append(_meeting_meta_block(
        meeting_type="每日晨会",
        project=project,
        participants=(participants or ["总经理(CEO)", "企划总监", "财务总监", "开发总监", "市场总监", "资源与行政"]),
        agenda=(agenda or ["开场说明", "部门汇报", "行动项与决策"]),
        extra_meta_lines=extra_meta_lines,
    ))
    content.append(f"【晨会开场】\n{ceo_opening}\n")
    content.append(dept_sections + "\n")
    content.append(f"【行动项与决策】\n{actions_table}\n")
    content.append(f"【会议时间】\n{human_time}\n")

    return "\n".join(content).strip()


def make_emergency_meeting_content(
    context_brief: str,
    reason: str,
    project: str = "DeWatermark AI",
    actions_model: str = None,
    participants: Optional[List[str]] = None,
    agenda: Optional[List[str]] = None,
    extra_meta_lines: Optional[List[str]] = None,
) -> str:
    """生成紧急会议纪要。"""
    now = datetime.now()
    human_time = now.strftime("%Y-%m-%d %H:%M")

    # 触发紧急会议的提示
    trigger_hint = schedule_emergency_meeting(reason)

    ceo_opening = call_agent(
        GENERAL_MANAGER_PROMPT.replace("{meeting_type}", "紧急会议"),
        user_instruction=(
            f"你正在主持紧急会议，触发原因：{reason}。请直入主题、明确行动项。\n\n" + context_brief
        ),
    )

    # 重点拉取开发、财务与资源行政
    dev_report = call_agent(
        DEV_DIRECTOR_PROMPT,
        user_instruction=(
            "请直报当前阻塞点、缓解方案与所需资源：\n\n" + context_brief
        ),
    )

    finance_report = call_agent(
        FINANCE_DIRECTOR_PROMPT,
        user_instruction=(
            "请评估解决方案的预算影响，并给出决策建议：\n\n" + context_brief
        ),
    )

    admin_report = call_agent(
        RESOURCE_ADMIN_PROMPT,
        user_instruction=(
            "请给出资源协调与合规风险提示，必要时提供流程模板：\n\n" + context_brief
        ),
    )

    dept_sections = (
        "【关键部门汇报】\n"
        + f"- 开发部：\n{dev_report}\n\n"
        + f"- 财务部：\n{finance_report}\n\n"
        + f"- 资源行政部：\n{admin_report}\n"
    )

    actions_table = _summarize_actions(dept_sections, model=actions_model)
    actions_table = _normalize_actions_table(actions_table, project)

    content = []
    content.append(_meeting_meta_block(
        meeting_type="紧急会议",
        project=project,
        participants=(participants or ["总经理(CEO)", "开发总监", "财务总监", "资源与行政"]),
        agenda=(agenda or ["触发说明", "关键部门汇报", "行动项与决策"]),
        extra_meta_lines=extra_meta_lines,
    ))
    content.append(f"【会议触发】\n{trigger_hint}\n")
    content.append(f"【会议开场】\n{ceo_opening}\n")
    content.append(dept_sections + "\n")
    content.append(f"【行动项与决策】\n{actions_table}\n")
    content.append(f"【会议时间】\n{human_time}\n")

    return "\n".join(content).strip()


def main():
    parser = argparse.ArgumentParser(description="YDS-Lab 多Agent部门协作编排器")
    parser.add_argument("--meeting", choices=["daily", "emergency"], default="daily", help="会议类型")
    parser.add_argument("--reason", default="", help="紧急会议原因（meeting=emergency 时必填）")
    parser.add_argument("--model", default="qwen2:0.5b", help="默认模型（可为 Ollama/本地别名或 Shimmy 模型ID/别名）")
    parser.add_argument("--project", default="DeWatermark AI", help="会议关联项目名称")
    parser.add_argument("--actions-model", default=None, help="用于生成‘行动项与决策’的模型（不填则与 --model 相同）")
    parser.add_argument("--participants", default=None, help="自定义参会角色（逗号分隔）")
    parser.add_argument("--agenda", default=None, help="自定义议程（逗号分隔）")
    parser.add_argument("--project-id", default=None, help="绑定项目目录（例如：001-dewatermark-ai），写入会议信息")
    args = parser.parse_args()

    # 为 call_agent 指定默认模型（通过闭包或全局覆盖）
    global route_chat, DEFAULT_MODEL
    _orig_route_chat = route_chat
    DEFAULT_MODEL = args.model or DEFAULT_MODEL

    def _route_chat_with_model(model: str, messages: List[Dict], **kwargs):
        # 保持兼容：若未显式传入 model，则使用 DEFAULT_MODEL
        return _orig_route_chat(model=(model or DEFAULT_MODEL), messages=messages, **kwargs)

    # 替换为带默认模型的封装
    route_chat = _route_chat_with_model  # type: ignore

    context_brief = read_strategy_brief()

    def _parse_csv_list(s: Optional[str]) -> Optional[List[str]]:
        if not s:
            return None
        return [x.strip() for x in s.split(",") if x.strip()]

    participants = _parse_csv_list(args.participants)
    agenda = _parse_csv_list(args.agenda)

    # 绑定项目目录（可选），写入元信息
    extra_meta_lines: List[str] = []
    if args.project_id:
        proj_dir = REPO_ROOT / "projects" / args.project_id
        if proj_dir.exists():
            extra_meta_lines.append(f"- 项目目录：projects/{args.project_id}")
        else:
            extra_meta_lines.append(f"- 项目目录：未找到（期望：projects/{args.project_id}）")

    if args.meeting == "emergency":
        if not args.reason:
            print("[错误] 紧急会议需要 --reason 指定触发原因")
            sys.exit(2)
        content = make_emergency_meeting_content(
            context_brief,
            reason=args.reason,
            project=args.project,
            actions_model=args.actions_model or DEFAULT_MODEL,
            participants=participants,
            agenda=agenda,
            extra_meta_lines=extra_meta_lines or None,
        )
    else:
        content = make_daily_meeting_content(
            context_brief,
            project=args.project,
            actions_model=args.actions_model or DEFAULT_MODEL,
            participants=participants,
            agenda=agenda,
            extra_meta_lines=extra_meta_lines or None,
        )

    # 归档
    saved = archive_meeting(content)
    print(saved)
    print("\n—— 会议纪要预览 ——\n")
    print(content[:2000] + ("\n..." if len(content) > 2000 else ""))


if __name__ == "__main__":
    main()