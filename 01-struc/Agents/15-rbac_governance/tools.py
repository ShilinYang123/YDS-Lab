# -*- coding: utf-8 -*-
"""
RBAC治理（rbac_governance）工具集
职责：角色/权限模型治理，权限边界检查与变更审计。
"""

import os
import json
from typing import Dict, Any


def load_rbac_config(config_path: str = "config/rbac_config.json") -> Dict[str, Any]:
    """加载RBAC配置（JSON）。若不存在则返回空结构。"""
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"roles": [], "permissions": []}


def validate_permissions(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """
    简单校验：角色是否存在重复ID、权限是否为空。
    返回：{"status": "ok"|"warn", "issues": [str]}
    """
    issues = []
    role_ids = set()
    for r in cfg.get("roles", []):
        rid = r.get("id")
        if rid in role_ids:
            issues.append(f"重复的角色ID: {rid}")
        role_ids.add(rid)
    if not cfg.get("permissions"):
        issues.append("权限集合为空或缺失")
    return {"status": "ok" if not issues else "warn", "issues": issues}


def audit_changes(old_cfg: Dict[str, Any], new_cfg: Dict[str, Any]) -> Dict[str, Any]:
    """对比两份RBAC配置，输出简单的增删改摘要。"""
    def idset(cfg, key):
        return {x.get("id") for x in cfg.get(key, [])}
    old_roles, new_roles = idset(old_cfg, "roles"), idset(new_cfg, "roles")
    added = list(new_roles - old_roles)
    removed = list(old_roles - new_roles)
    return {"added_roles": added, "removed_roles": removed}