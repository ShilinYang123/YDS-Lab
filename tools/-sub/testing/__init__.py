#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试工具包
高效办公助手系统 - 自动化测试工具
作者：杨世林 雨俊 3AI工作室
日期：2025-10-12
"""

__version__ = "1.0.0"
__author__ = "杨世林 雨俊 3AI工作室"
__description__ = "自动化测试、单元测试和集成测试工具"

from .test_runner import TestRunner

__all__ = [
    "TestRunner"
]