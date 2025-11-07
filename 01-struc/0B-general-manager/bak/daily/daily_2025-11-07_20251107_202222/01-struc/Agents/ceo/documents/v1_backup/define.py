# CrewAI-GM-define
# 供 main.py 或 Crew 调用，定义总经理 Agent 实例

import sys
import os

# 修复导入路径，使能导入 Struc.* 以及项目根下的 models.*
struc_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
repo_root = os.path.dirname(struc_root)
for p in (struc_root, repo_root):
    if p not in sys.path:
        sys.path.insert(0, p)

# 现在可以安全导入
try:
    from crewai import Agent
    CREWAI_AVAILABLE = True
except Exception:
    CREWAI_AVAILABLE = False
    Agent = None
from Struc.Agents.ceo.prompt import GENERAL_MANAGER_PROMPT
from Struc.Agents.ceo.tools import (
    schedule_emergency_meeting,
    approve_budget,
    archive_meeting
)
from models.services.llm_router import get_llm_response

if CREWAI_AVAILABLE:
    general_manager = Agent(
        role="CrewAI-GM-GeneralManager",
        goal="统筹YDS公司高效运转，确保DeWatermark项目30天内上线并盈利",
        backstory=GENERAL_MANAGER_PROMPT,
        tools=[
            schedule_emergency_meeting,
            approve_budget,
            archive_meeting
        ],
        verbose=True,
        allow_delegation=True
    )
else:
    general_manager = None


def run_daily_check():
    """CEO 日常检查：调用本地 Ollama 生成开场总结"""
    prompt = (
        "你作为 YDS AI 公司的总经理，请生成一份简短的今日晨会开场总结，"
        "语气专业且鼓舞人心，提及项目进展顺利、团队协作高效。"
    )
    return get_llm_response(prompt, model="qwen:1.8b")