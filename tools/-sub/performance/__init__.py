#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能优化工具包
采用惰性导入，避免在包初始化时引入不存在或重依赖子模块。
"""

__version__ = "1.0.0"
__author__ = "杨世林 雨俊 3AI工作室"
__description__ = "性能测试、分析和优化工具"

import importlib

_SUBMODULES = [
    "performance_tester",
    "performance_analyzer",
]

def __getattr__(name):
    if name in _SUBMODULES:
        return importlib.import_module(f".{name}", __name__)
    raise AttributeError(f"module 'tools.performance' has no attribute '{name}'")

def __dir__():
    return sorted(list(globals().keys()) + _SUBMODULES)

__all__ = _SUBMODULES