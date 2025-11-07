#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能监控系统补丁包自动安装脚本
版本: v1.0
作者: 雨俊
"""

import os
import sys
import shutil
import json
from pathlib import Path
from datetime import datetime

class PatchInstaller:
    def __init__(self):
        self.patch_dir = Path(__file__).parent.parent
        self.target_dir = None
        self.backup_dir = None
        
    def detect_target_directory(self):
        """自动检测目标安装目录"""
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
        """创建备份"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir = self.target_dir / f"backup_智能监控系统_{timestamp}"
        
        print(f"📦 创建备份目录: {self.backup_dir}")
        self.backup_dir.mkdir(exist_ok=True)
        
        # 备份start.py
        if (self.target_dir / "tools" / "start.py").exists():
            shutil.copy2(
                self.target_dir / "tools" / "start.py",
                self.backup_dir / "start.py"
            )
            print("✓ 已备份 start.py")
        
        # 备份LongMemory目录（如果存在）
        longmemory_dir = self.target_dir / "tools" / "LongMemory"
        if longmemory_dir.exists():
            backup_longmemory = self.backup_dir / "LongMemory"
            shutil.copytree(longmemory_dir, backup_longmemory, dirs_exist_ok=True)
            print("✓ 已备份 LongMemory 目录")
    
    def install_files(self):
        """安装文件"""
        print("🚀 开始安装智能监控系统...")
        
        # 安装start.py
        src_start = self.patch_dir / "src" / "tools" / "start.py"
        dst_start = self.target_dir / "tools" / "start.py"
        
        if src_start.exists():
            shutil.copy2(src_start, dst_start)
            print("✓ 已安装 start.py")
        
        # 安装LongMemory文件
        src_longmemory = self.patch_dir / "src" / "tools" / "LongMemory"
        dst_longmemory = self.target_dir / "tools" / "LongMemory"
        
        if src_longmemory.exists():
            # 确保目标目录存在
            dst_longmemory.mkdir(exist_ok=True)
            
            # 复制所有文件
            for file_path in src_longmemory.glob("*"):
                if file_path.is_file():
                    shutil.copy2(file_path, dst_longmemory / file_path.name)
                    print(f"✓ 已安装 {file_path.name}")
    
    def verify_installation(self):
        """验证安装"""
        print("🔍 验证安装...")
        
        required_files = [
            "tools/start.py",
            "tools/LongMemory/intelligent_monitor.py",
            "tools/LongMemory/smart_error_detector.py",
            "tools/LongMemory/proactive_reminder.py",
            "tools/LongMemory/intelligent_monitor_config.json"
        ]
        
        all_ok = True
        for file_path in required_files:
            full_path = self.target_dir / file_path
            if full_path.exists():
                print(f"✓ {file_path}")
            else:
                print(f"✗ {file_path} - 缺失!")
                all_ok = False
        
        return all_ok
    
    def test_system(self):
        """测试系统"""
        print("🧪 测试智能监控系统...")
        
        try:
            # 切换到目标目录
            os.chdir(self.target_dir)
            
            # 运行测试
            import subprocess
            result = subprocess.run([
                sys.executable, "tools/LongMemory/test_intelligent_monitor.py"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✓ 智能监控系统测试通过")
                return True
            else:
                print(f"✗ 测试失败: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"✗ 测试异常: {e}")
            return False
    
    def run(self):
        """运行安装程序"""
        print("=" * 50)
        print("🤖 智能监控系统补丁包安装程序 v1.0")
        print("=" * 50)
        
        # 1. 检测目标目录
        if not self.detect_target_directory():
            print("❌ 未找到3AI系统目录!")
            print("请确保:")
            print("1. 3AI系统已正确安装")
            print("2. 在正确的目录运行此脚本")
            return False
        
        # 2. 确认安装
        response = input(f"\n📍 将安装到: {self.target_dir}\n是否继续? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            print("❌ 安装已取消")
            return False
        
        try:
            # 3. 创建备份
            self.create_backup()
            
            # 4. 安装文件
            self.install_files()
            
            # 5. 验证安装
            if not self.verify_installation():
                print("❌ 安装验证失败!")
                return False
            
            # 6. 测试系统
            if not self.test_system():
                print("⚠️  系统测试失败，但文件已安装")
            
            print("\n" + "=" * 50)
            print("🎉 智能监控系统安装成功!")
            print("=" * 50)
            print(f"📦 备份位置: {self.backup_dir}")
            print("🚀 现在可以运行: python tools/start.py --work")
            print("📚 查看文档: docs/使用说明.md")
            
            return True
            
        except Exception as e:
            print(f"❌ 安装失败: {e}")
            print(f"📦 可从备份恢复: {self.backup_dir}")
            return False

if __name__ == "__main__":
    installer = PatchInstaller()
    success = installer.run()
    sys.exit(0 if success else 1)