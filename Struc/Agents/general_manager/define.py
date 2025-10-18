# CrewAI-GM-define
# 供 main.py 或 Crew 调用，定义总经理 Agent 实例

import sys
import os

# 修复导入路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 现在可以安全导入
from crewai import Agent
from Struc.Agents.general_manager.prompt import GENERAL_MANAGER_PROMPT
from Struc.Agents.general_manager.tools import (
    schedule_emergency_meeting,
    approve_budget,
    archive_meeting
)

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