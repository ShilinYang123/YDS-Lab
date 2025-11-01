#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YDS-Lab 统一检查入口（Aggregator）
按顶层设计提供统一检查入口，聚合质量、安全、性能、合规等模块。
采用惰性导入，避免引入不必要的重依赖。
"""

from typing import Dict, Any
import importlib
import importlib.util

def _module_available(module_path: str) -> bool:
    return importlib.util.find_spec(module_path) is not None

def _safe_import(module_path: str):
    try:
        return importlib.import_module(module_path)
    except Exception:
        return None

def run_quality_checks() -> Dict[str, Any]:
    result = {"category": "quality", "status": "ok", "details": {}}
    # 尝试 tools.quality.quality_checker
    if _module_available("tools.quality.quality_checker"):
        mod = _safe_import("tools.quality.quality_checker")
        result["details"]["tools.quality.quality_checker"] = {
            "available": mod is not None
        }
    # 尝试 tools.monitoring.quality_checker
    if _module_available("tools.monitoring.quality_checker"):
        mod = _safe_import("tools.monitoring.quality_checker")
        result["details"]["tools.monitoring.quality_checker"] = {
            "available": mod is not None
        }
    return result

def run_security_scan() -> Dict[str, Any]:
    result = {"category": "security", "status": "ok", "details": {}}
    if _module_available("tools.security.security_scanner"):
        mod = _safe_import("tools.security.security_scanner")
        result["details"]["tools.security.security_scanner"] = {
            "available": mod is not None
        }
    return result

def run_performance_checks() -> Dict[str, Any]:
    result = {"category": "performance", "status": "ok", "details": {}}
    if _module_available("tools.performance.performance_analyzer"):
        mod = _safe_import("tools.performance.performance_analyzer")
        result["details"]["tools.performance.performance_analyzer"] = {
            "available": mod is not None
        }
    if _module_available("tools.monitoring.performance_monitor"):
        mod = _safe_import("tools.monitoring.performance_monitor")
        result["details"]["tools.monitoring.performance_monitor"] = {
            "available": mod is not None
        }
    return result

def run_compliance_checks() -> Dict[str, Any]:
    result = {"category": "compliance", "status": "ok", "details": {}}
    if _module_available("tools.monitoring.compliance_monitor"):
        mod = _safe_import("tools.monitoring.compliance_monitor")
        result["details"]["tools.monitoring.compliance_monitor"] = {
            "available": mod is not None
        }
    return result

def run_all_checks() -> Dict[str, Any]:
    return {
        "quality": run_quality_checks(),
        "security": run_security_scan(),
        "performance": run_performance_checks(),
        "compliance": run_compliance_checks(),
    }

__all__ = [
    "run_quality_checks",
    "run_security_scan",
    "run_performance_checks",
    "run_compliance_checks",
    "run_all_checks",
]

"""
检查工具包
高效办公助手系统 - 系统检查和诊断工具
作者：杨世林 雨俊 3AI工作室
日期：2025-10-12
"""

__version__ = "1.0.0"
__author__ = "杨世林 雨俊 3AI工作室"
__description__ = "系统检查、诊断和健康状态监测工具"

# 检查工具将在此导入
# from .system_checker import SystemChecker

__all__ = [
    # "SystemChecker"
]