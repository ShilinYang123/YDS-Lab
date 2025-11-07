# CrewAI-MK-define
# 供 main.py 或 Crew 调用，定义市场业务总监 Agent 实例

import sys
import os

# 修复导入路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from crewai import Agent
from Struc.Agents.marketing_director.prompt import MARKETING_DIRECTOR_PROMPT
from Struc.Agents.marketing_director.tools import (
    generate_social_copy,
    analyze_user_feedback,
    estimate_conversion_rate
)

marketing_director = Agent(
    role="CrewAI-MK-MarketingDirector",
    goal="为DeWatermark AI制定高效推广策略，30天内获取500+用户并实现5%付费转化",
    backstory=MARKETING_DIRECTOR_PROMPT,
    tools=[
        generate_social_copy,
        analyze_user_feedback,
        estimate_conversion_rate
    ],
    verbose=True
)