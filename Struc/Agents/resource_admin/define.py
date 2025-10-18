# CrewAI-RA-define
# 供 main.py 或 Crew 调用，定义资源与行政总监 Agent 实例

import sys
import os

# 修复导入路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from crewai import Agent
from Struc.Agents.resource_admin.prompt import RESOURCE_ADMIN_PROMPT
from Struc.Agents.resource_admin.tools import (
    review_contract,
    check_compliance,
    allocate_resource
)

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