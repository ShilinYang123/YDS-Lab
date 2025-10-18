#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码质量工具包
提供质量检查与分析工具的惰性导入，避免在包初始化阶段引入不存在或重依赖模块。
"""

__version__ = "1.0.0"
__author__ = "杨世林 雨俊 3AI工作室"
__description__ = "代码质量检查、分析和改进工具"

import importlib

_SUBMODULES = [
    "quality_checker",
]

def __getattr__(name):
    if name in _SUBMODULES:
        return importlib.import_module(f".{name}", __name__)
    raise AttributeError(f"module 'tools.quality' has no attribute '{name}'")

def __dir__():
    return sorted(list(globals().keys()) + _SUBMODULES)

__all__ = _SUBMODULES