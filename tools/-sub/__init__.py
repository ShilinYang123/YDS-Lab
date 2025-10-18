#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YDS-Lab 工具包
高效办公助手系统 - 工具集合
作者：杨世林 雨俊 3AI工作室
日期：2025-10-12
"""

__version__ = "1.0.0"
__author__ = "杨世林 雨俊 3AI工作室"
__description__ = "YDS-Lab 高效办公助手系统工具包"

# 按需惰性导入子模块，避免在导入单个子模块时引入重依赖（如 pandas、gitpython 等）
import importlib

_SUBMODULES = [
    "api",
    "backup",
    "config",
    "data",
    "database",
    "deployment",
    "docs",
    "documentation",
    "env",
    "git",
    "integration",
    "logging",
    "mcp",
    "monitoring",
    "performance",
    "project",
    "quality",
    "security",
    "testing",
    "version",
]

def __getattr__(name):
    if name in _SUBMODULES:
        return importlib.import_module(f".{name}", __name__)
    raise AttributeError(f"module 'tools' has no attribute '{name}'")

def __dir__():
    return sorted(list(globals().keys()) + _SUBMODULES)

__all__ = _SUBMODULES