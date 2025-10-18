# CrewAI-DV-define
# 供 main.py 或 Crew 调用，定义开发总监 Agent 实例

import sys
import os

# 修复导入路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from crewai import Agent
from Struc.Agents.dev_team.dev_director.prompt import DEV_DIRECTOR_PROMPT
from Struc.Agents.dev_team.dev_director.tools import (
    assign_task,
    check_device_availability,
    estimate_development_time
)

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