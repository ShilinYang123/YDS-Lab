#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能监控系统补丁包备份脚本
版本: v1.0
作者: 雨俊
"""

import os
import sys
import shutil
import json
from pathlib import Path
from datetime import datetime

class SystemBackup:
    def __init__(self):
        self.target_dir = None
        self.backup_dir = None
        
    def detect_target_directory(self):
        """自动检测目标目录"""
        possible_paths = [
            Path("S:/3AI"),
            Path("C:/3AI"),
            Path("D:/3AI"),
            Path("./3AI"),
            Path("../3AI"),
            Path("../../3AI")
        ]
        
        for path in possible_paths:
            if path.exists() and (path / "tools" / "start.py").exists():
                self.target_dir = path
                print(f"✓ 检测到3AI系统目录: {path}")
                return True
                
        return False
    
    def create_backup(self):
        """创建完整备份"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir = self.target_dir / f"backup_完整系统_{timestamp}"
        
        print(f"📦 创建备份目录: {self.backup_dir}")
        self.backup_dir.mkdir(exist_ok=True)
        
        # 备份关键文件和目录
        backup_items = [
            ("tools/start.py", "start.py"),
            ("tools/LongMemory", "LongMemory"),
            ("logs", "logs"),
            ("03.Output", "03.Output")
        ]
        
        for src_path, backup_name in backup_items:
            src = self.target_dir / src_path
            dst = self.backup_dir / backup_name
            
            if src.exists():
                if src.is_file():
                    shutil.copy2(src, dst)
                    print(f"✓ 已备份文件: {src_path}")
                elif src.is_dir():
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                    print(f"✓ 已备份目录: {src_path}")
        
        # 创建备份信息文件
        backup_info = {
            "backup_time": timestamp,
            "source_directory": str(self.target_dir),
            "backup_directory": str(self.backup_dir),
            "backup_items": [item[0] for item in backup_items if (self.target_dir / item[0]).exists()]
        }
        
        with open(self.backup_dir / "backup_info.json", "w", encoding="utf-8") as f:
            json.dump(backup_info, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 备份信息已保存")
    
    def run(self):
        """运行备份程序"""
        print("=" * 50)
        print("💾 3AI系统备份程序 v1.0")
        print("=" * 50)
        
        # 1. 检测目标目录
        if not self.detect_target_directory():
            print("❌ 未找到3AI系统目录!")
            return False
        
        # 2. 确认备份
        response = input(f"\n📍 将备份: {self.target_dir}\n是否继续? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            print("❌ 备份已取消")
            return False
        
        try:
            # 3. 创建备份
            self.create_backup()
            
            print("\n" + "=" * 50)
            print("🎉 系统备份完成!")
            print("=" * 50)
            print(f"📦 备份位置: {self.backup_dir}")
            print("💡 提示: 请妥善保存备份文件")
            
            return True
            
        except Exception as e:
            print(f"❌ 备份失败: {e}")
            return False

if __name__ == "__main__":
    backup = SystemBackup()
    success = backup.run()
    sys.exit(0 if success else 1)