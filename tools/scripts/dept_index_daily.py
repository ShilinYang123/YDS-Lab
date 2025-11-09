#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from datetime import datetime

ROOT = r"S:\\YDS-Lab\\01-struc"
CATEGORIES = [
    "规章制度",
    "流程与SOP",
    "模板",
    "会议纪要",
    "项目资料",
]

def list_dept_docs(root):
    for name in sorted(os.listdir(root)):
        dept_path = os.path.join(root, name)
        if not os.path.isdir(dept_path):
            continue
        docs_path = os.path.join(dept_path, "docs")
        if os.path.isdir(docs_path):
            yield name, docs_path

def safe_rel(docs_path, full_path):
    rel = os.path.relpath(full_path, docs_path)
    return rel.replace("\\", "/")

def generate_index(docs_path, dept_name):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []
    lines.append("# 部门文档自动索引")
    lines.append("")
    lines.append(f"- 部门目录: {dept_name}")
    lines.append(f"- 生成时间: {ts}")
    lines.append(f"- 根路径: {docs_path}")
    lines.append("")

    for cat in CATEGORIES:
        cat_path = os.path.join(docs_path, cat)
        lines.append(f"## {cat}")
        if os.path.isdir(cat_path):
            files = []
            for dirpath, dirnames, filenames in os.walk(cat_path):
                for fn in filenames:
                    if os.path.splitext(fn)[1].lower() in {".md", ".docx", ".xlsx", ".pptx", ".pdf", ".txt"}:
                        files.append(os.path.join(dirpath, fn))
            if not files:
                lines.append("- （暂无文件）")
            else:
                for fp in sorted(files):
                    rel = safe_rel(docs_path, fp)
                    name = os.path.basename(fp)
                    lines.append(f"- [{name}]({rel})")
        else:
            try:
                os.makedirs(cat_path, exist_ok=True)
            except Exception:
                pass
            lines.append("- （目录新建，暂无文件）")
        lines.append("")

    index_path = os.path.join(docs_path, "INDEX.md")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return index_path

def main():
    count = 0
    for dept_name, docs_path in list_dept_docs(ROOT):
        index_path = generate_index(docs_path, dept_name)
        print(f"已生成: {index_path}")
        count += 1
    print(f"部门文档索引生成完成，共处理 {count} 个部门。")

if __name__ == "__main__":
    main()