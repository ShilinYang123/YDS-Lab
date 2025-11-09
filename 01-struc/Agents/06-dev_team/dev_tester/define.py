# CrewAI-DV-define
# 供 main.py 或 Crew 调用，定义测试工程师 Agent 实例

import sys
import os

# 修复导入路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from crewai import Agent
from Struc.Agents.dev_team.dev_tester.prompt import DEV_TESTER_PROMPT
from Struc.Agents.dev_team.dev_tester.tools import (
    run_functional_test,
    measure_performance,
    generate_test_report
)

dev_tester = Agent(
    role="CrewAI-DV-Tester",
    goal="确保DeWatermark AI MVP版本功能稳定、用户体验流畅，7天内完成全面测试",
    backstory=DEV_TESTER_PROMPT,
    tools=[
        run_functional_test,
        measure_performance,
        generate_test_report
    ],
    verbose=True
)