# -*- coding: utf-8 -*-
"""
监控与告警（monitor_alerting）工具集
职责：系统监控指标采集与告警规则执行。
"""

import os
from typing import Dict, Any


def collect_metrics() -> Dict[str, Any]:
    """采集基础指标（示例：检测监控脚本是否存在）。"""
    metrics = {
        "metrics_fast_ps1_exists": os.path.exists("tools/LongMemory/metrics_fast.ps1"),
        "health_check_py_exists": os.path.exists("tools/LongMemory/health_check.py"),
    }
    return {"status": "ok", "metrics": metrics}


def trigger_alert(rule: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
    """触发告警（占位）：根据规则与指标简单返回告警结果。"""
    active = False
    if rule == "missing_scripts":
        m = metrics.get("metrics", {})
        active = not (m.get("metrics_fast_ps1_exists") and m.get("health_check_py_exists"))
    return {"rule": rule, "active": active, "status": "ok"}