#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
监控工具包
采用惰性导入，避免在包初始化时引入重依赖（如 psutil）。
"""

__version__ = "1.0.0"
__author__ = "杨世林 雨俊 3AI工作室"
__description__ = "系统监控、性能分析和告警工具"

import importlib

_SUBMODULES = [
    "system_monitor",
    "performance_monitor",
    "quality_checker",
    "compliance_monitor",
]

def __getattr__(name):
    if name in _SUBMODULES:
        return importlib.import_module(f".{name}", __name__)
    raise AttributeError(f"module 'tools.monitoring' has no attribute '{name}'")

def __dir__():
    return sorted(list(globals().keys()) + _SUBMODULES)

__all__ = _SUBMODULES