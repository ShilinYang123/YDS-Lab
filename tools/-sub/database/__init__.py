#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库管理工具包
高效办公助手系统 - 数据库连接和管理工具
作者：雨侠
日期：2025-10-12
"""

__version__ = "1.0.0"
__author__ = "雨侠"
__description__ = "数据库连接、管理和操作工具"

from .db_manager import DatabaseManager

__all__ = [
    "DatabaseManager"
]