#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YDS-Lab 日志管理工具包
提供统一的日志管理、分析、清理和监控功能
适配YDS-Lab项目结构和AI Agent协作需求

主要功能:
- 统一日志配置和管理
- 日志分析和统计
- 日志清理和归档
- 实时日志监控
- 日志告警机制
"""

from .log_manager import LogManager

__version__ = "1.0.0"
__author__ = "杨世林 雨俊 3AI工作室"
__description__ = "YDS-Lab日志管理工具包"

__all__ = ["LogManager"]