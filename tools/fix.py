#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
编码修复工具 (fix.py)
简化版高级编码维护工具
功能：修复项目编码问题
"""

import os
import sys
import json
import chardet
import codecs
import shutil
from pathlib import Path
from typing import Dict, List

def detect_encoding(file_path: Path) -> tuple:
    """检测文件编码"""
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read()
        
        if not raw_data:
            return 'empty', 1.0
        
        # 首先尝试UTF-8
        try:
            raw_data.decode('utf-8')
            return 'utf-8', 1.0
        except UnicodeDecodeError:
            pass
        
        # 使用chardet检测
        detection = chardet.detect(raw_data)
        encoding = detection.get('encoding', 'utf-8')
        confidence = detection.get('confidence', 0)
        
        return encoding, confidence
        
    except Exception as e:
        return 'unknown', 0.0

def fix_file_encoding(file_path: Path, backup_dir: Path = None) -> Dict:
    """修复单个文件编码"""
    result = {
        "file": str(file_path),
        "original_encoding": "unknown",
        "fixed": False,
        "error": None
    }
    
    try:
        # 检测原始编码
        original_encoding, confidence = detect_encoding(file_path)
        result["original_encoding"] = original_encoding
        
        # 如果已经是UTF-8，跳过
        if original_encoding == 'utf-8':
            result["fixed"] = True
            result["note"] = "已经是UTF-8编码"
            return result
        
        # 创建备份
        if backup_dir:
            backup_path = backup_dir / f"{file_path.name}.backup"
            shutil.copy2(file_path, backup_path)
        
        # 读取原始内容
        with open(file_path, 'rb') as f:
            raw_content = f.read()
        
        # 解码原始内容
        if original_encoding != 'unknown':
            try:
                content = raw_content.decode(original_encoding)
            except (UnicodeDecodeError, LookupError):
                # 尝试常见中文编码
                for encoding in ['gbk', 'gb2312', 'gb18030', 'big5']:
                    try:
                        content = raw_content.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    result["error"] = "无法解码文件"
                    return result
        else:
            result["error"] = "无法检测编码"
            return result
        
        # 以UTF-8编码写回
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        result["fixed"] = True
        result["new_encoding"] = "utf-8"
        
    except Exception as e:
        result["error"] = str(e)
    
    return result

def fix_project_encoding(project_path: str = None, create_backup: bool = True) -> Dict:
    """修复项目编码问题"""
    if project_path is None:
        project_path = Path.cwd()
    else:
        project_path = Path(project_path)
    
    results = {
        "total_files": 0,
        "fixed_files": 0,
        "failed_files": 0,
        "skipped_files": 0,
        "details": []
    }
    
    # 创建备份目录
    backup_dir = None
    if create_backup:
        backup_dir = project_path / "bak" / "encoding_fixes"
        backup_dir.mkdir(parents=True, exist_ok=True)
    
    # 支持的文件类型
    supported_ext = ['.py', '.yaml', '.yml', '.json', '.md', '.txt']
    
    for file_path in project_path.rglob("*"):
        if any(part in ("bak", "logs", "rep", "backups") for part in file_path.parts):
            continue
        if file_path.is_file() and file_path.suffix in supported_ext:
            results["total_files"] += 1
            
            # 修复文件编码
            fix_result = fix_file_encoding(file_path, backup_dir)
            results["details"].append(fix_result)
            
            if fix_result["fixed"]:
                results["fixed_files"] += 1
            elif fix_result.get("error"):
                results["failed_files"] += 1
            else:
                results["skipped_files"] += 1
    
    return results

def main():
    """主函数"""
    # 参数处理
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--help', '-h', '/?']:
            print("🔧 YDS-Lab 编码修复工具")
            print("用法: python fix.py [目录路径]")
            print("说明: 修复项目中的编码问题，自动转换为UTF-8")
            print("注意: 会自动创建备份，安全修复")
            return 0
        path = sys.argv[1]
    else:
        path = None
    
    print("🔧 开始修复项目编码问题...")
    results = fix_project_encoding(path)
    
    print(f"📊 修复完成：")
    print(f"   总文件数：{results['total_files']}")
    print(f"   修复成功：{results['fixed_files']}")
    print(f"   修复失败：{results['failed_files']}")
    print(f"   跳过文件：{results['skipped_files']}")
    
    if results["failed_files"] > 0:
        print("\n❌ 修复失败的文件：")
        for detail in results["details"]:
            if detail.get("error") and not detail["fixed"]:
                print(f"   {detail['file']}: {detail['error']}")
    
    # 保存结果
    out_dir = project_path / "rep" / "encoding_analysis"
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / "encoding_fix_results.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 结果已保存到：{output_path}")

if __name__ == "__main__":
    main()
