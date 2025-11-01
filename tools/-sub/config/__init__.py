#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理工具包
高效办公助手系统 - 配置文件管理工具
作者：杨世林 雨俊 3AI工作室
"""

__version__ = "1.1.0"
__author__ = "杨世林 雨俊 3AI工作室"
__description__ = "配置文件管理与验证工具（适配YDS-Lab顶层设计）"

# 统一导出配置管理器，兼容旧代码中的 ConfigManager 命名
from .config_manager import YDSConfigManager as ConfigManager

def get_config_manager(project_root=None):
    """获取配置管理器实例（统一入口）
    - 兼容不同模块的调用方式
    - 支持自定义项目根目录
    """
    return ConfigManager(project_root=project_root)

__all__ = [
    "ConfigManager",
    "get_config_manager",
]