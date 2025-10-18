#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全工具包
高效办公助手系统 - 安全检查和防护工具
作者：雨侠
日期：2025-10-12
"""

__version__ = "1.0.0"
__author__ = "雨侠"
__description__ = "安全检查、漏洞扫描和防护工具"

from .security_scanner import SecurityScanner

__all__ = [
    "SecurityScanner"
]