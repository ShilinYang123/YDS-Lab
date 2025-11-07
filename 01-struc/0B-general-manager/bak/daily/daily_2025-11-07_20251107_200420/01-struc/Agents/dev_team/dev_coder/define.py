# CrewAI-DV-define
# 供 main.py 或 Crew 调用，定义编码工程师 Agent 实例

import sys
import os

# 修复导入路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from crewai import Agent
from Struc.Agents.dev_team.dev_coder.prompt import DEV_CODER_PROMPT
from Struc.Agents.dev_team.dev_coder.tools import (
    generate_tauri_ui,
    generate_python_backend,
    validate_code_security
)

dev_coder = Agent(
    role="CrewAI-DV-Coder",
    goal="为DeWatermark AI生成高质量、安全、可运行的Tauri+Python代码，7天内完成MVP",
    backstory=DEV_CODER_PROMPT,
    tools=[
        generate_tauri_ui,
        generate_python_backend,
        validate_code_security
    ],
    verbose=True
)