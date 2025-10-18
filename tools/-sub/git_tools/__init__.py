#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git管理工具包
高效办公助手系统 - Git版本控制工具
作者：雨侠
日期：2025-10-12
"""

__version__ = "1.0.0"
__author__ = "雨侠"
__description__ = "Git版本控制和仓库管理工具"

from .git_helper import GitHelper

__all__ = [
    "GitHelper"
]