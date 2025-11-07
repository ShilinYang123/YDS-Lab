#!/usr/bin/env python3
"""测试过滤功能"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from update_structure import YDSLabStructureUpdater

def test_filter():
    updater = YDSLabStructureUpdater()
    
    # 测试文件过滤
    test_files = [
        'test.log',
        'app.log', 
        'debug.tmp',
        'backup.bak',
        'normal.py',
        'config.yaml'
    ]
    
    print("=== 文件过滤测试 ===")
    for file_name in test_files:
        should_exclude = updater.should_exclude_file(file_name)
        print(f"{file_name:<15} -> {'排除' if should_exclude else '保留'}")
    
    print("\n=== 配置信息 ===")
    print("exclude_files:", updater.default_config.get('exclude_files', []))

if __name__ == "__main__":
    test_filter()