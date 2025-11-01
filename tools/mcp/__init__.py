#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP (Model Context Protocol) 工具包
高效办公助手系统 - MCP服务器管理工具
作者：雨侠
日期：2025-10-12
"""

__version__ = "1.0.0"
__author__ = "雨侠"
__description__ = "MCP服务器管理和健康检查工具"

from .mcp_health_checker import MCPHealthChecker
from .mcp_server_manager import MCPServerManager

__all__ = [
    "MCPHealthChecker",
    "MCPServerManager"
]