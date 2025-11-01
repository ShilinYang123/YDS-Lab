#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YDS-Lab GitHub仓库创建和推送脚本
"""

import os
import sys
import subprocess
import json
from pathlib import Path

# 添加 tools 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tools'))

try:
    from git_tools.git_helper import GitHelper
except ImportError:
    print("警告: 无法导入 GitHelper，将使用系统 Git 命令")
    GitHelper = None

def run_git_command(command):
    """执行Git命令"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8')
        if result.returncode == 0:
            print(f"✓ 成功: {command}")
            if result.stdout.strip():
                print(f"  输出: {result.stdout.strip()}")
            return True
        else:
            print(f"✗ 失败: {command}")
            print(f"  错误: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"✗ 执行命令时出错: {command}")
        print(f"  异常: {str(e)}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("YDS-Lab GitHub仓库创建和推送脚本")
    print("=" * 60)
    
    # 检查是否在正确的目录
    if not os.path.exists('tools') or not os.path.exists('projects'):
        print("错误: 请在YDS-Lab项目根目录下运行此脚本")
        return False
    
    # 配置Git用户信息
    print("\n1. 配置Git用户信息...")
    run_git_command('git config user.name "ShilinYang123"')
    run_git_command('git config user.email "shilinyang123@gmail.com"')
    
    # 初始化Git仓库（如果尚未初始化）
    print("\n2. 初始化Git仓库...")
    if not os.path.exists('.git'):
        run_git_command('git init')
    
    # 添加远程仓库
    print("\n3. 配置远程仓库...")
    # 先移除可能存在的origin
    run_git_command('git remote remove origin')
    # 添加新的origin
    if run_git_command('git remote add origin https://github.com/ShilinYang123/YDS-Lab.git'):
        print("✓ 远程仓库配置成功")
    
    # 创建.gitignore文件
    print("\n4. 创建.gitignore文件...")
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Temporary files
*.tmp
*.temp
temp/

# Sensitive data
*.key
*.pem
config/secrets.json
.env

# Backup files
*.bak
bak/
backup/
"""
    
    try:
        with open('.gitignore', 'w', encoding='utf-8') as f:
            f.write(gitignore_content)
        print("✓ .gitignore文件创建成功")
    except Exception as e:
        print(f"✗ 创建.gitignore文件失败: {e}")
    
    # 添加所有文件到暂存区
    print("\n5. 添加文件到暂存区...")
    if run_git_command('git add .'):
        print("✓ 文件添加到暂存区成功")
    
    # 提交更改
    print("\n6. 提交更改...")
    commit_message = "Initial commit: YDS-Lab AI智能协作系统"
    if run_git_command(f'git commit -m "{commit_message}"'):
        print("✓ 提交成功")
    
    # 设置主分支
    print("\n7. 设置主分支...")
    run_git_command('git branch -M main')
    
    # 推送到GitHub
    print("\n8. 推送到GitHub...")
    print("注意: 需要在GitHub上手动创建仓库 'YDS-Lab'")
    print("仓库URL: https://github.com/ShilinYang123/YDS-Lab")
    print("\n推送命令:")
    print("git push -u origin main")
    
    # 尝试推送
    print("\n尝试推送...")
    if run_git_command('git push -u origin main'):
        print("✓ 推送成功!")
        print("\n🎉 YDS-Lab仓库创建和推送完成!")
    else:
        print("\n推送失败，可能的原因:")
        print("1. GitHub仓库尚未创建")
        print("2. 认证失败")
        print("3. 网络连接问题")
        print("\n请手动执行以下步骤:")
        print("1. 在GitHub上创建名为 'YDS-Lab' 的公共仓库")
        print("2. 运行: git push -u origin main")
    
    print("\n" + "=" * 60)
    return True

if __name__ == "__main__":
    main()