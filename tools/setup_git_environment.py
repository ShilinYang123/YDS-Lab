#!/usr/bin/env python3
"""
Git环境自动配置脚本
用于确保Git环境正确配置，解决每日推送失败问题
"""

import os
import sys
import subprocess
from pathlib import Path

def setup_git_path():
    """设置Git PATH环境变量"""
    git_paths = [
        r"C:\Program Files\Git\bin",
        r"C:\Program Files\Git\cmd",
        r"C:\Program Files (x86)\Git\bin",
        r"C:\Program Files (x86)\Git\cmd"
    ]
    
    current_path = os.environ.get('PATH', '')
    path_updated = False
    
    for git_path in git_paths:
        if os.path.exists(git_path) and git_path not in current_path:
            os.environ['PATH'] = git_path + ';' + os.environ['PATH']
            path_updated = True
            print(f"✅ 已添加Git路径: {git_path}")
    
    return path_updated

def check_git_available():
    """检查Git是否可用"""
    try:
        result = subprocess.run(['git', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ Git可用: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Git不可用: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Git检查失败: {e}")
        return False

def setup_git_config():
    """设置Git全局配置"""
    try:
        # 设置用户名
        subprocess.run(['git', 'config', '--global', 'user.name', 'ShilinYang123'], 
                      check=True, timeout=10)
        print("✅ Git全局用户名已设置: ShilinYang123")
        
        # 设置邮箱
        subprocess.run(['git', 'config', '--global', 'user.email', 'yslwin@139.com'], 
                      check=True, timeout=10)
        print("✅ Git全局邮箱已设置: yslwin@139.com")
        
        # 验证配置
        name_result = subprocess.run(['git', 'config', '--global', 'user.name'], 
                                   capture_output=True, text=True, timeout=10)
        email_result = subprocess.run(['git', 'config', '--global', 'user.email'], 
                                    capture_output=True, text=True, timeout=10)
        
        print(f"验证 - 用户名: {name_result.stdout.strip()}")
        print(f"验证 - 邮箱: {email_result.stdout.strip()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Git配置设置失败: {e}")
        return False

def main():
    """主函数"""
    print("🔧 开始配置Git环境...")
    
    # 1. 设置Git PATH
    print("\n1. 配置Git PATH...")
    setup_git_path()
    
    # 2. 检查Git是否可用
    print("\n2. 检查Git可用性...")
    if not check_git_available():
        print("❌ Git不可用，请检查安装")
        return False
    
    # 3. 设置Git配置
    print("\n3. 配置Git用户信息...")
    if not setup_git_config():
        print("❌ Git配置失败")
        return False
    
    print("\n✅ Git环境配置完成！")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)