#!/usr/bin/env python3
# 兼容包装器：固定脚本已迁移到仓库根目录 st.py
# Deprecated: 请改用 "python st.py"
import os, sys, runpy

def _main():
    base = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(base)
    target = os.path.join(repo_root, "st.py")
    if not os.path.exists(target):
        sys.stderr.write("Error: 根目录 st.py 不存在，请确认已按规范迁移。\n")
        sys.exit(1)
    try:
        runpy.run_path(target, run_name="__main__")
    except SystemExit as e:
        raise

if __name__ == "__main__":
    _main()