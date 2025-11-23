#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
额外项目映射分析工具
分析"不存在"的额外项目实际存在于哪个目录
"""

import os
import sys
from pathlib import Path

def find_actual_locations():
    """查找额外项目的实际位置"""
    
    # 定义要查找的文件列表
    files_to_find = [
        "02-1YDS-Lab标准目录结构（顶层设计）.md",
        "02-2治理原则图示（阴阳五行协同图）.md", 
        "2.Trae 长效记忆系统自动记录功能全流程升级方案（终版）.md",
        "2.Trae 长效记忆系统自动记录功能全流程升级方案（终版）.pdf",
        "JS001-智能会议室系统开发任务书（本地部署优化版）.md",
        "LLM路由与后端选择（Shimmy-Ollama）使用说明.md",
        "Trae平台多智能体开发团队构建指南（最终完整版）.docx",
        "Trae平台多智能体开发团队构建指南（最终完整版）.md",
        "Trae平台多智能体开发团队构建指南（最终完整版）.pdf",
        "《动态目录结构清单（候选）》.md",
        "开发任务书（长记忆系统开发）.md",
        "治理原则图示（阴阳五行协同图）.html",
        "治理原则图示（阴阳五行协同图）.pdf"
    ]
    
    project_root = Path("s:/YDS-Lab")
    
    print("🔍 正在查找额外项目的实际位置...")
    print("=" * 100)
    
    found_files = {}
    not_found_files = []
    
    for filename in files_to_find:
        print(f"\n📄 查找: {filename}")
        found = False
        
        # 在整个项目中递归查找
        for root, dirs, files in os.walk(project_root):
            # 跳过备份目录
            if 'bak' in Path(root).parts:
                continue
                
            if filename in files:
                full_path = Path(root) / filename
                rel_path = full_path.relative_to(project_root)
                
                print(f"✅ 找到: {rel_path}")
                print(f"📍 完整路径: {full_path}")
                
                # 获取文件信息
                stat = full_path.stat()
                size = stat.st_size
                from datetime import datetime
                mtime = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                
                print(f"📏 大小: {size:,} 字节")
                print(f"🕒 修改时间: {mtime}")
                
                # 分析文件应该在的位置
                suggested_location = suggest_proper_location(filename, rel_path)
                if suggested_location:
                    print(f"💡 建议位置: {suggested_location}")
                
                found_files[filename] = {
                    'current_path': str(rel_path),
                    'full_path': str(full_path),
                    'size': size,
                    'modified': mtime
                }
                found = True
                break
        
        if not found:
            print("❌ 未找到")
            not_found_files.append(filename)
    
    print("\n" + "=" * 100)
    print("📊 汇总报告:")
    print(f"✅ 找到: {len(found_files)} 个文件")
    print(f"❌ 未找到: {len(not_found_files)} 个文件")
    
    if found_files:
        print("\n📋 找到的文件列表:")
        for filename, info in found_files.items():
            print(f"  📄 {filename}")
            print(f"     当前位置: {info['current_path']}")
            print(f"     建议操作: 考虑移动到合适目录或更新标准清单")
    
    if not_found_files:
        print(f"\n❓ 未找到的文件列表:")
        for filename in not_found_files:
            print(f"  📄 {filename}")
            print(f"     状态: 可能已被删除或重命名")
    
    print("\n💡 总体建议:")
    print("1. 对于存在于错误位置的文件，考虑移动到合适的docs/子目录")
    print("2. 更新标准结构清单以包含这些重要文档")
    print("3. 对于确实不需要的文件，可以从标准清单中移除")
    print("4. 保持项目根目录整洁，避免散落文档文件")

def suggest_proper_location(filename, current_path):
    """建议文件应该在的位置"""
    
    # 根据文件名内容判断类型
    if "治理原则图示" in filename or "顶层设计" in filename:
        return "01-struc/docs/01-战略规划/"
    elif "Trae" in filename and ("多智能体" in filename or "开发团队" in filename):
        return "01-struc/docs/02-组织流程/"
    elif "Trae" in filename and "长效记忆" in filename:
        return "02-task/001-长记忆系统开发/"
    elif "JS001" in filename or "智能会议室" in filename:
        return "02-task/002-meetingroom/"
    elif "LLM路由" in filename or "Shimmy-Ollama" in filename:
        return "01-struc/docs/03-技术规范/"
    elif "动态目录结构清单" in filename:
        return "01-struc/docs/02-组织流程/"
    elif "开发任务书" in filename and "长记忆" in filename:
        return "02-task/001-长记忆系统开发/"
    else:
        return None

if __name__ == "__main__":
    find_actual_locations()