#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YDS-Lab GitHub推送脚本
使用系统Git命令推送到GitHub
"""

import os
import subprocess
import sys

# Git可执行文件路径
GIT_PATH = r"C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\Common7\IDE\CommonExtensions\Microsoft\TeamFoundation\Team Explorer\Git\cmd\git.exe"

def run_git_command(command_args):
    """执行Git命令"""
    try:
        full_command = [GIT_PATH] + command_args
        result = subprocess.run(full_command, capture_output=True, text=True, encoding='utf-8', cwd=os.getcwd())
        
        print(f"执行命令: git {' '.join(command_args)}")
        
        if result.returncode == 0:
            print("✓ 成功")
            if result.stdout.strip():
                print(f"输出:\n{result.stdout}")
            return True
        else:
            print("✗ 失败")
            if result.stderr.strip():
                print(f"错误:\n{result.stderr}")
            return False
    except Exception as e:
        print(f"✗ 执行命令时出错: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("YDS-Lab GitHub推送脚本")
    print("=" * 60)
    
    # 检查Git可执行文件
    if not os.path.exists(GIT_PATH):
        print(f"错误: Git可执行文件不存在: {GIT_PATH}")
        return False
    
    print("✓ Git可执行文件找到")
    
    # 配置Git用户信息
    print("\n1. 配置Git用户信息...")
    run_git_command(['config', 'user.name', 'ShilinYang123'])
    run_git_command(['config', 'user.email', 'shilinyang123@gmail.com'])
    
    # 检查远程仓库
    print("\n2. 检查远程仓库...")
    if not run_git_command(['remote', 'get-url', 'origin']):
        print("添加远程仓库...")
        run_git_command(['remote', 'add', 'origin', 'https://github.com/ShilinYang123/YDS-Lab.git'])
    
    # 添加文件
    print("\n3. 添加文件到暂存区...")
    run_git_command(['add', '.'])
    
    # 提交
    print("\n4. 提交更改...")
    run_git_command(['commit', '-m', 'Initial commit: YDS-Lab AI智能协作系统'])
    
    # 设置主分支
    print("\n5. 设置主分支...")
    run_git_command(['branch', '-M', 'main'])
    
    # 推送
    print("\n6. 推送到GitHub...")
    print("注意: 请确保已在GitHub上创建 'YDS-Lab' 仓库")
    print("仓库URL: https://github.com/ShilinYang123/YDS-Lab")
    
    if run_git_command(['push', '-u', 'origin', 'main']):
        print("\n🎉 推送成功!")
    else:
        print("\n推送失败，可能需要:")
        print("1. 在GitHub上手动创建 'YDS-Lab' 仓库")
        print("2. 配置GitHub认证")
        print("3. 检查网络连接")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()