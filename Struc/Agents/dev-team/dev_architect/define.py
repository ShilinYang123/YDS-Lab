# CrewAI-DV-define
# 供 main.py 或 Crew 调用，定义架构师 Agent 实例

import sys
import os

# 修复导入路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from crewai import Agent
from Struc.Agents.dev_team.dev_architect.prompt import DEV_ARCHITECT_PROMPT
from Struc.Agents.dev_team.dev_architect.tools import (
    generate_architecture_diagram,
    define_module_interface,
    evaluate_tech_stack
)

dev_architect = Agent(
    role="CrewAI-DV-Architect",
    goal="为DeWatermark AI设计稳定、可扩展、易维护的技术架构，确保7天内MVP可开发",
    backstory=DEV_ARCHITECT_PROMPT,
    tools=[
        generate_architecture_diagram,
        define_module_interface,
        evaluate_tech_stack
    ],
    verbose=True
)