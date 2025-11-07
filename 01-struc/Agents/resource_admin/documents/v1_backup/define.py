# CrewAI-RA-define
# 供 main.py 或 Crew 调用，定义资源与行政总监 Agent 实例

import sys
import os

# 修复导入路径，使能导入 Struc.* 以及项目根下的 models.*
struc_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
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
from Struc.Agents.resource_admin.prompt import RESOURCE_ADMIN_PROMPT
from Struc.Agents.resource_admin.tools import (
    review_contract,
    check_compliance,
    allocate_resource
)
from models.services.llm_router import get_llm_response

if CREWAI_AVAILABLE:
    resource_admin = Agent(
        role="CrewAI-RA-ResourceAdmin",
        goal="确保YDS公司运营合规、资源高效利用，为DeWatermark项目提供行政与法务支持",
        backstory=RESOURCE_ADMIN_PROMPT,
        tools=[
            review_contract,
            check_compliance,
            allocate_resource
        ],
        verbose=True
    )
else:
    resource_admin = None


def get_admin_update():
    """资源与行政部更新：调用本地 Ollama 生成动态报告"""
    prompt = (
        "你是 YDS AI 公司的资源与行政总监，请生成一段今日资源与行政更新，涵盖合同审查、"
        "合规检查与资源分配，简洁、专业、可执行。"
    )
    return get_llm_response(prompt, model="qwen:1.8b")