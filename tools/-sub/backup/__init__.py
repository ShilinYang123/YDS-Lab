#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YDS-Lab 备份工具入口（兼容层）
按顶层设计提供备份脚本入口，当前为占位实现。
后续将实现：
- 全量备份（full_backup）
- 增量备份（incremental_backup）
- 恢复（restore）
"""

from .full_backup import run_full_backup
from .incremental_backup import run_incremental_backup
from .restore import run_restore

__all__ = [
    "run_full_backup",
    "run_incremental_backup",
    "run_restore",
]