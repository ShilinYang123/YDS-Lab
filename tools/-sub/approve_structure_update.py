#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YDS-Lab 结构清单批准发布工具

用途：
- 对《动态目录结构清单（候选）》与正式清单进行差异预览
- 在明确批准下，将候选清单发布为正式清单，并归档旧版本

批准方式（任一满足即可）：
- 命令行参数 --yes
- 环境变量 YDS_APPROVE_STRUCTURE=1
- 在 Docs/YDS-AI-组织与流程/ 下创建哨兵文件 APPROVE_UPDATE_STRUCTURE
"""

import os
import sys
import argparse
import difflib
from pathlib import Path
from datetime import datetime


def read_text(path: Path) -> str:
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def write_text(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def archive_current(formal_file: Path, archive_dir: Path) -> Path:
    if formal_file.exists():
        archive_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        archive_path = archive_dir / f"动态目录结构清单_旧版_{ts}.md"
        write_text(archive_path, read_text(formal_file))
        return archive_path
    return None


def main():
    parser = argparse.ArgumentParser(description="批准发布结构清单（候选 -> 正式）")
    parser.add_argument("--project-root", default="s:/YDS-Lab", help="项目根目录路径")
    parser.add_argument("--yes", action="store_true", help="确认批准并发布")
    args = parser.parse_args()

    project_root = Path(args.project_root)
    formal_file = project_root / "Struc" / "GeneralOffice" / "Docs" / "YDS-AI-组织与流程" / "《动态目录结构清单》.md"
    candidate_file = project_root / "Struc" / "GeneralOffice" / "Docs" / "YDS-AI-组织与流程" / "《动态目录结构清单（候选）》.md"
    archive_dir = project_root / "Struc" / "GeneralOffice" / "logs" / "structure"
    sentinel_file = project_root / "Struc" / "GeneralOffice" / "Docs" / "YDS-AI-组织与流程" / "APPROVE_UPDATE_STRUCTURE"

    if not candidate_file.exists():
        print(f"❌ 候选清单不存在，请先运行 update_structure.py 生成：{candidate_file}")
        sys.exit(1)

    formal_text = read_text(formal_file) if formal_file.exists() else ""
    candidate_text = read_text(candidate_file)

    diff_lines = list(difflib.unified_diff(
        formal_text.splitlines(keepends=True),
        candidate_text.splitlines(keepends=True),
        fromfile=str(formal_file), tofile=str(candidate_file)
    ))

    # 输出差异到日志/归档目录
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    diff_path = archive_dir / f"结构清单差异_{ts}.diff"
    archive_dir.mkdir(parents=True, exist_ok=True)
    write_text(diff_path, ''.join(diff_lines) if diff_lines else "(无差异)")
    print(f"🔍 差异已生成：{diff_path}")

    approved = args.yes or os.environ.get("YDS_APPROVE_STRUCTURE", "0") in ("1", "true", "True") or sentinel_file.exists()
    if not approved:
        print("⛔ 未获批准，已完成差异预览但不会发布正式清单。")
        print("如需发布，可：")
        print("- 使用参数 --yes")
        print("- 设置环境变量 YDS_APPROVE_STRUCTURE=1")
        print(f"- 创建哨兵文件：{sentinel_file}")
        sys.exit(2)

    # 执行归档与发布
    archived = archive_current(formal_file, archive_dir)
    if archived:
        print(f"📦 已归档旧正式清单：{archived}")

    write_text(formal_file, candidate_text)
    print(f"✅ 正式目录结构清单已发布：{formal_file}")
    sys.exit(0)


if __name__ == "__main__":
    main()