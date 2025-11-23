# -*- coding: utf-8 -*-
"""
文档治理（document_governance）工具集
职责：统一文档命名、路径治理、版本与归档策略。
"""

import os
from typing import List, Dict


def check_naming_convention(paths: List[str]) -> Dict:
    """
    检查给定路径下文件是否遵循中文命名与约定（示例：仅检查是否包含空格或明显的占位名）。
    返回：{"status": "ok"|"warn", "violations": [str], "checked": int}
    """
    violations = []
    checked = 0
    for base in paths:
        if not os.path.exists(base):
            continue
        for root, dirs, files in os.walk(base):
            for f in files:
                checked += 1
                name = f
                if "  " in name or name.lower().startswith("readme"):
                    violations.append(os.path.join(root, f))
    return {
        "status": "warn" if violations else "ok",
        "violations": violations,
        "checked": checked,
    }


def generate_governance_report(paths: List[str]) -> str:
    """生成治理报告的简要文本。"""
    result = check_naming_convention(paths)
    header = "文档治理报告\n"
    body = f"检查文件数: {result['checked']}\n"
    if result["status"] == "ok":
        body += "命名规范检查通过，无显著问题。\n"
    else:
        body += "发现命名不规范文件如下：\n" + "\n".join(result["violations"]) + "\n"
    return header + body