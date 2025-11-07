#!/usr/bin/env python3
"""
Git PATH 环境变量配置脚本
自动将 Git 安装路径添加到系统 PATH 环境变量中
"""

import os
import sys
import subprocess
import winreg
from pathlib import Path

class GitPathSetup:
    def __init__(self):
        self.git_paths = [
            r"C:\Program Files\Git\bin",
            r"C:\Program Files\Git\cmd",
            r"C:\Program Files (x86)\Git\bin", 
            r"C:\Program Files (x86)\Git\cmd"
        ]
        
    def find_git_installation(self):
        """查找 Git 安装路径"""
        found_paths = []
        
        for path in self.git_paths:
            git_exe = Path(path) / "git.exe"
            if git_exe.exists():
                found_paths.append(path)
                print(f"✅ 找到 Git 安装路径: {path}")
        
        return found_paths
    
    def get_current_path(self):
        """获取当前用户 PATH 环境变量"""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as key:
                path_value, _ = winreg.QueryValueEx(key, "PATH")
                return path_value
        except FileNotFoundError:
            return ""
    
    def get_system_path(self):
        """获取系统 PATH 环境变量"""
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                              r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment") as key:
                path_value, _ = winreg.QueryValueEx(key, "PATH")
                return path_value
        except Exception as e:
            print(f"⚠️ 无法读取系统 PATH: {e}")
            return ""
    
    def add_to_user_path(self, git_paths):
        """将 Git 路径添加到用户 PATH 环境变量"""
        current_path = self.get_current_path()
        path_list = [p.strip() for p in current_path.split(';') if p.strip()]
        
        added_paths = []
        for git_path in git_paths:
            if git_path not in path_list:
                path_list.append(git_path)
                added_paths.append(git_path)
        
        if added_paths:
            new_path = ';'.join(path_list)
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, 
                                  winreg.KEY_SET_VALUE) as key:
                    winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)
                
                print(f"✅ 成功添加到用户 PATH:")
                for path in added_paths:
                    print(f"   - {path}")
                return True
            except Exception as e:
                print(f"❌ 添加到用户 PATH 失败: {e}")
                return False
        else:
            print("ℹ️ Git 路径已存在于用户 PATH 中")
            return True
    
    def check_path_in_system(self, git_paths):
        """检查 Git 路径是否已在系统 PATH 中"""
        system_path = self.get_system_path()
        system_paths = [p.strip().lower() for p in system_path.split(';') if p.strip()]
        
        for git_path in git_paths:
            if git_path.lower() in system_paths:
                print(f"ℹ️ Git 路径已存在于系统 PATH: {git_path}")
                return True
        return False
    
    def test_git_command(self):
        """测试 git 命令是否可用"""
        try:
            result = subprocess.run(['git', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✅ Git 命令测试成功: {result.stdout.strip()}")
                return True
            else:
                print(f"❌ Git 命令测试失败: {result.stderr}")
                return False
        except FileNotFoundError:
            print("❌ Git 命令不可用 (需要重启终端或重新登录)")
            return False
        except Exception as e:
            print(f"❌ Git 命令测试出错: {e}")
            return False
    
    def setup(self):
        """执行 Git PATH 设置"""
        print("=== Git PATH 环境变量配置 ===\n")
        
        # 1. 查找 Git 安装
        git_paths = self.find_git_installation()
        if not git_paths:
            print("❌ 未找到 Git 安装，请先安装 Git")
            return False
        
        # 2. 检查系统 PATH
        if self.check_path_in_system(git_paths):
            print("✅ Git 已在系统 PATH 中，无需配置")
            return self.test_git_command()
        
        # 3. 添加到用户 PATH
        success = self.add_to_user_path(git_paths)
        if not success:
            return False
        
        # 4. 提示重启
        print("\n📋 配置完成！请执行以下操作之一:")
        print("   1. 重启终端/命令提示符")
        print("   2. 重新登录 Windows")
        print("   3. 重启计算机")
        print("\n然后就可以直接使用 'git' 命令了！")
        
        return True

def main():
    """主函数"""
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print("Git PATH 环境变量配置脚本")
        print("用法: python setup_git_path.py")
        print("功能: 自动将 Git 安装路径添加到用户 PATH 环境变量")
        return
    
    setup = GitPathSetup()
    success = setup.setup()
    
    if success:
        print("\n🎉 Git PATH 配置成功！")
    else:
        print("\n💥 Git PATH 配置失败，请检查错误信息")
        sys.exit(1)

if __name__ == "__main__":
    main()