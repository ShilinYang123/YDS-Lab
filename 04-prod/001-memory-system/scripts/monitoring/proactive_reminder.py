#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
兼容适配文件：提供 ProactiveReminder 至监控目录

生产脚本 `start_proactive_reminder.py` 位于 scripts 根目录。
为兼容 `intelligent_monitor.py` 中的 `from proactive_reminder import ProactiveReminder`
在 monitoring 目录提供同名模块进行转发。
"""

try:
    # 同级搜索：当 scripts 根目录已在 sys.path 时可直接导入
    from start_proactive_reminder import ProactiveReminder  # type: ignore
except Exception:
    try:
        # 相对导入备用方案
        from ..start_proactive_reminder import ProactiveReminder  # type: ignore
    except Exception as e:
        raise ImportError(f"无法导入 ProactiveReminder: {e}")

__all__ = ["ProactiveReminder"]