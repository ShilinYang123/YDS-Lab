import os
from datetime import datetime

def schedule_emergency_meeting(reason: str) -> str:
    """触发紧急会议"""
    return f"🚨【紧急会议】因 {reason}，立即召开临时会议"

def approve_budget(amount: float, purpose: str) -> str:
    """审批预算（>¥500）"""
    return f"✅ 总经理批准预算：¥{amount:.2f}，用途：{purpose}"

def archive_meeting(content: str) -> str:
    """归档会议记录"""
    filename = f"MTG-{datetime.now().strftime('%Y%m%d-%H%M')}.md"
    path = f"Struc/GeneralOffice/meetings/{filename}"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"📁 已归档至：{path}"