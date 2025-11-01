#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
版本管理工具包
高效办公助手系统 - 版本控制和发布管理工具
作者：杨世林 雨俊 3AI工作室
日期：2025-10-12
"""

__version__ = "1.0.0"
__author__ = "杨世林 雨俊 3AI工作室"
__description__ = "版本控制、发布管理和变更跟踪工具"

from .version_manager import VersionManager

__all__ = [
    "VersionManager"
]