#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
额外项目实际位置分析工具
准确显示额外项目在项目结构中的实际位置
"""

import os
import sys
from pathlib import Path

# 添加当前目录到Python路径，确保可以导入ch.py
sys.path.insert(0, str(Path(__file__).parent))

from ch import YDSLabStructureChecker

def analyze_extra_items_locations():
    """分析额外项目的实际位置"""
    print("🔍 正在分析YDS-Lab额外项目的实际位置...")
    
    # 创建检查器实例
    checker = YDSLabStructureChecker(use_preview=True)
    
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
    print("=" * 100)
    
    # 分析每个额外项目的实际位置
    for item in sorted(extra_items):
        item_path = item.strip().rstrip('/')  # 移除末尾的/和空格
        
        # 构建完整路径
        if item_path.startswith('YDS-Lab/'):
            full_path = checker.project_root / item_path[8:]  # 移除YDS-Lab/
        else:
            full_path = checker.project_root / item_path
        
        print(f"\n📄 项目名称: {item}")
        print(f"📍 相对路径: {item_path}")
        print(f"🔍 完整路径: {full_path}")
        
        # 检查文件/目录是否存在
        if full_path.exists():
            if full_path.is_file():
                stat = full_path.stat()
                size = stat.st_size
                mtime = stat.st_mtime
                from datetime import datetime
                mod_time = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                print(f"✅ 状态: 存在 (文件)")
                print(f"📏 大小: {size:,} 字节")
                print(f"🕒 修改时间: {mod_time}")
            elif full_path.is_dir():
                print(f"✅ 状态: 存在 (目录)")
                # 计算目录中的项目数量
                try:
                    item_count = len(list(full_path.rglob("*")))
                    print(f"📊 目录内容: {item_count} 个项目")
                except:
                    print(f"📊 目录内容: 无法访问")
            else:
                print(f"❓ 状态: 存在 (其他类型)")
        else:
            print(f"❌ 状态: 不存在")
            
            # 尝试找到相似或相关的文件
            parent_dir = full_path.parent
            if parent_dir.exists() and parent_dir.is_dir():
                similar_files = []
                try:
                    for f in parent_dir.iterdir():
                        if f.name.startswith(item_path.split('/')[-1][:5]):  # 前5个字符匹配
                            similar_files.append(f.name)
                except:
                    pass
                
                if similar_files:
                    print(f"💡 在父目录中找到相似文件:")
                    for similar in similar_files[:3]:  # 最多显示3个
                        print(f"   - {similar}")
        
        print("-" * 80)
    
    print(f"\n📊 总计: {len(extra_items)} 个额外项目")
    
    # 按目录层级分析
    print("\n📂 按目录层级分析:")
    level_counts = {}
    for item in extra_items:
        level = item.count('/')  # 计算层级深度
        level_counts[level] = level_counts.get(level, 0) + 1
    
    for level in sorted(level_counts.keys()):
        indent = "  " * level
        print(f"{indent}层级 {level}: {level_counts[level]} 个项目")
    
    print("\n💡 处理建议:")
    print("1. 对于'不存在'的项目，检查是否被移动或重命名")
    print("2. 对于文档文件，考虑移动到合适的docs/子目录")
    print("3. 对于临时文件，考虑删除或移动到bak/目录")
    print("4. 对于重要文件，考虑更新标准结构清单以包含它们")
    
    return True

if __name__ == "__main__":
    success = analyze_extra_items_locations()
    sys.exit(0 if success else 1)