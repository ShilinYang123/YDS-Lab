#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目管理工具包
高效办公助手系统 - 项目创建和管理工具
作者：雨侠
日期：2025-10-12
"""

__version__ = "1.0.0"
__author__ = "雨侠"
__description__ = "项目创建、管理和配置工具"

from .project_creator import ProjectCreator

__all__ = [
    "ProjectCreator"
]