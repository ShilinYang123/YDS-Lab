#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
额外项目详细列表工具
用于列出ch.py检查中发现的所有额外项目及其具体位置
"""

import os
import sys
from pathlib import Path

# 添加当前目录到Python路径，确保可以导入ch.py
sys.path.insert(0, str(Path(__file__).parent))

from ch import YDSLabStructureChecker

def list_extra_items_detailed():
    """详细列出所有额外项目及其位置"""
    print("🔍 正在扫描YDS-Lab额外项目...")
    
    # 创建检查器实例
    checker = YDSLabStructureChecker()
    
    # 运行环境验证
    if not checker.validate_environment():
        print("❌ 环境验证失败")
        return False
    
    # 解析标准结构
    print("📋 解析标准目录结构...")
    standard_items = checker.parse_whitelist_structure()
    if not standard_items:
        print("❌ 无法获取标准结构")
        return False
    
    # 扫描当前结构
    print("📂 扫描当前目录结构...")
    current_items = checker.scan_directory(checker.project_root)
    print(f"实际扫描到 {len(current_items)} 个项目")
    
    # 结构对比
    print("🔍 开始结构对比分析...")
    comparison_result = checker.compare_structures(standard_items, current_items)
    
    # 获取额外项目
    extra_items = comparison_result['extra']
    
    if not extra_items:
        print("✅ 未发现额外项目")
        return True
    
    print(f"\n📋 发现 {len(extra_items)} 个额外项目：")
    print("=" * 80)
    
    # 按类型分类
    categories = {
        '🗂️ 备份文件': [],
        '📝 文档文件': [],
        '🔧 配置文件': [],
        '📊 日志文件': [],
        '🎯 临时文件': [],
        '📁 其他目录': [],
        '📄 其他文件': []
    }
    
    # 分类额外项目
    for item in sorted(extra_items):
        item_lower = item.lower()
        item_path = item.strip()
        
        # 确定完整路径
        if item_path.endswith('/'):
            # 目录
            full_path = checker.project_root / item_path.rstrip('/')
            categories['📁 其他目录'].append((item_path, str(full_path)))
        elif any(keyword in item_lower for keyword in ['backup', 'bak', 'old', 'copy']):
            categories['🗂️ 备份文件'].append((item_path, str(checker.project_root / item_path)))
        elif any(keyword in item_lower for keyword in ['.md', '.txt', '.doc', '.pdf', 'readme', 'doc']):
            categories['📝 文档文件'].append((item_path, str(checker.project_root / item_path)))
        elif any(keyword in item_lower for keyword in ['.yaml', '.yml', '.json', '.ini', '.cfg', 'config']):
            categories['🔧 配置文件'].append((item_path, str(checker.project_root / item_path)))
        elif any(keyword in item_lower for keyword in ['.log', 'log', 'logs']):
            categories['📊 日志文件'].append((item_path, str(checker.project_root / item_path)))
        elif any(keyword in item_lower for keyword in ['temp', 'tmp', 'cache', '.cache']):
            categories['🎯 临时文件'].append((item_path, str(checker.project_root / item_path)))
        else:
            categories['📄 其他文件'].append((item_path, str(checker.project_root / item_path)))
    
    # 输出分类结果
    for category, items in categories.items():
        if items:
            print(f"\n{category} ({len(items)} 个):")
            print("-" * 60)
            for item_name, full_path in items:
                print(f"📍 {item_name}")
                print(f"   完整路径: {full_path}")
                # 检查是否存在
                if Path(full_path).exists():
                    if Path(full_path).is_file():
                        size = Path(full_path).stat().st_size
                        print(f"   类型: 文件 | 大小: {size:,} 字节")
                    else:
                        print(f"   类型: 目录")
                else:
                    print(f"   类型: 不存在")
                print()
    
    print("=" * 80)
    print(f"📊 总计: {len(extra_items)} 个额外项目")
    print("\n💡 建议:")
    print("1. 检查这些额外项目是否仍然需要")
    print("2. 考虑将不需要的项目移动到 bak/ 目录")
    print("3. 对于重要文档，考虑归档到合适的目录")
    print("4. 临时文件可以考虑删除")
    
    return True

if __name__ == "__main__":
    success = list_extra_items_detailed()
    sys.exit(0 if success else 1)