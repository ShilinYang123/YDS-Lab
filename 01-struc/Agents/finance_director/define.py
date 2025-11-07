# CrewAI-FN-define
# 供 main.py 或 Crew 调用，定义财务总监 Agent 实例

import sys
import os

# 修复导入路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from crewai import Agent
from Struc.Agents.finance_director.prompt import FINANCE_DIRECTOR_PROMPT
from Struc.Agents.finance_director.tools import (
    calculate_budget,
    predict_revenue,
    check_break_even
)

finance_director = Agent(
    role="CrewAI-FN-FinanceDirector",
    goal="确保DeWatermark AI项目财务健康，30天内实现正向现金流",
    backstory=FINANCE_DIRECTOR_PROMPT,
    tools=[
        calculate_budget,
        predict_revenue,
        check_break_even
    ],
    verbose=True
)