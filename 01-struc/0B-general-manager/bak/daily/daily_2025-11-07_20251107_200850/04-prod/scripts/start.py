#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
生产环境启动入口（统一入口）

说明：
- 历史上生产启动逻辑位于 tools/production/start.py。
- 为与 04-prod 目录语义一致，这里提供统一入口并调用旧位置脚本。
- 后续将把核心实现迁移至此文件，并将 tools/production/start.py 作为兼容包装器或移除。
"""

from pathlib import Path
import runpy

def main():
    project_root = Path(__file__).resolve().parents[2]
    legacy_start = project_root / "tools" / "production" / "start.py"
    if legacy_start.exists():
        # 直接运行旧启动脚本以保持兼容
        runpy.run_path(str(legacy_start))
    else:
        print("未找到旧版启动脚本 tools/production/start.py。请检查项目结构或更新启动入口。")

if __name__ == "__main__":
    main()