# -*- coding: utf-8 -*-
"""
长记忆系统健康（longmemory_health）工具集
职责：长记忆系统健康检查、指标采集与异常恢复建议。
"""

import os
from typing import Dict, Any


def health_check() -> Dict[str, Any]:
    """基础健康检查：相关脚本与报告文件存在性。"""
    exists = {
        "health_check_py": os.path.exists("tools/LongMemory/health_check.py"),
        "record_event_py": os.path.exists("tools/LongMemory/record_event.py"),
        "final_validation_report_json": os.path.exists("final_validation_report.json"),
        "final_validation_report_md": os.path.exists("final_validation_report.md"),
    }
    status = "ok" if all(exists.values()) else "warn"
    return {"status": status, "exists": exists}


def summarize() -> str:
    """输出健康检查的文本摘要。"""
    result = health_check()
    lines = ["长记忆系统健康检查摘要"]
    lines.append(f"状态: {result['status']}")
    for k, v in result["exists"].items():
        lines.append(f"- {k}: {'存在' if v else '缺失'}")
    return "\n".join(lines)