# CrewAI-PL-define
# 供 main.py 或 Crew 调用，定义企划总监 Agent 实例

import sys
import os

# 修复导入路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 现在可以安全导入
from crewai import Agent
from Struc.Agents.planning_director.prompt import PLANNING_DIRECTOR_PROMPT
from Struc.Agents.planning_director.tools import (
    market_research,
    generate_swot_analysis,
    estimate_market_size
)

planning_director = Agent(
    role="CrewAI-PL-PlanningDirector",
    goal="为DeWatermark AI提供精准市场定位与可行性分析，确保产品满足真实需求",
    backstory=PLANNING_DIRECTOR_PROMPT,
    tools=[
        market_research,
        generate_swot_analysis,
        estimate_market_size
    ],
    verbose=True
)