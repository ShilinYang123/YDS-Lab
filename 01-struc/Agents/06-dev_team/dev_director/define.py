# CrewAI-DV-define
# 供 main.py 或 Crew 调用，定义开发总监 Agent 实例

import sys
import os

# 修复导入路径，使能导入 Struc.* 以及项目根下的 models.*
struc_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
repo_root = os.path.dirname(struc_root)
for p in (struc_root, repo_root):
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from crewai import Agent
    CREWAI_AVAILABLE = True
except Exception:
    CREWAI_AVAILABLE = False
    Agent = None
from Struc.Agents.dev_team.dev_director.prompt import DEV_DIRECTOR_PROMPT
from Struc.Agents.dev_team.dev_director.tools import (
    assign_task,
    check_device_availability,
    estimate_development_time
)
from models.services.llm_router import get_llm_response

if CREWAI_AVAILABLE:
    dev_director = Agent(
        role="CrewAI-DV-DevDirector",
        goal="确保DeWatermark AI在7天内完成MVP，21天内正式上线，技术方案稳定可靠",
        backstory=DEV_DIRECTOR_PROMPT,
        tools=[
            assign_task,
            check_device_availability,
            estimate_development_time
        ],
        verbose=True,
        allow_delegation=True
    )
else:
    dev_director = None


def get_dev_update():
    """开发部更新：调用本地 Ollama 生成动态报告"""
    prompt = (
        "你是 YDS AI 公司的开发总监，请生成一段今日项目开发更新，涵盖MVP进度、"
        "集成测试与核心功能验收，语言简洁、明确，并体现团队协作。"
    )
    return get_llm_response(prompt, model="qwen:1.8b")