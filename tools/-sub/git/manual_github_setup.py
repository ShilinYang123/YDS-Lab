#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动 GitHub 仓库设置指南
"""

import os
import sys
import subprocess
import webbrowser

# 添加 tools 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tools'))

from git_tools.git_helper import GitHelper

def run_git_command(command, cwd=None):
    """运行 Git 命令"""
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, 
                              capture_output=True, text=True, encoding='gbk')
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, result.stderr.strip()
    except Exception as e:
        return False, str(e)

def main():
    print("🚀 YDS-Lab GitHub 仓库手动设置指南")
    print("=" * 50)
    
    project_root = os.path.dirname(__file__)
    
    print("\n📋 步骤 1: 在 GitHub 上创建仓库")
    print("-" * 30)
    print("1. 访问 GitHub: https://github.com/new")
    print("2. 仓库名称: YDS-Lab")
    print("3. 描述: YDS-Lab AI智能协作系统 - 企业级AI开发与协作平台")
    print("4. 设置为 Public (公开)")
    print("5. 不要勾选 'Add a README file'")
    print("6. 不要勾选 'Add .gitignore'")
    print("7. 不要勾选 'Choose a license'")
    print("8. 点击 'Create repository'")
    
    choice = input("\n是否现在打开 GitHub 创建页面? (y/n): ").lower()
    if choice == 'y':
        webbrowser.open('https://github.com/new')
    
    input("\n按 Enter 键继续（确保已在 GitHub 上创建了仓库）...")
    
    print("\n🔧 步骤 2: 配置本地 Git")
    print("-" * 30)
    
    # 配置 Git 用户信息
    print("配置 Git 用户信息...")
    run_git_command('git config user.name "ShilinYang123"', project_root)
    run_git_command('git config user.email "shilinyang123@gmail.com"', project_root)
    print("✅ Git 用户信息已配置")
    
    # 检查 Git 状态
    success, output = run_git_command('git status', project_root)
    if success:
        print("✅ Git 仓库状态正常")
    else:
        print(f"⚠️ Git 状态检查: {output}")
    
    # 添加远程仓库
    print("\n配置远程仓库...")
    github_url = "https://github.com/ShilinYang123/YDS-Lab.git"
    
    # 删除现有的 origin（如果存在）
    run_git_command('git remote remove origin', project_root)
    
    # 添加新的 origin
    success, output = run_git_command(f'git remote add origin {github_url}', project_root)
    if success:
        print(f"✅ 已添加远程仓库: {github_url}")
    else:
        print(f"⚠️ 添加远程仓库: {output}")
    
    # 检查远程仓库
    success, output = run_git_command('git remote -v', project_root)
    if success:
        print("📡 远程仓库配置:")
        print(output)
    
    print("\n📦 步骤 3: 准备和提交文件")
    print("-" * 30)
    
    # 添加所有文件
    success, output = run_git_command('git add .', project_root)
    if success:
        print("✅ 已添加所有文件到暂存区")
    else:
        print(f"⚠️ 添加文件: {output}")
    
    # 检查暂存状态
    success, output = run_git_command('git status --porcelain', project_root)
    if success and output:
        file_count = len(output.split('\n'))
        print(f"📁 暂存区文件数量: {file_count}")
    
    # 提交更改
    commit_message = "Initial commit: YDS-Lab AI智能协作系统"
    success, output = run_git_command(f'git commit -m "{commit_message}"', project_root)
    if success:
        print(f"✅ 已提交更改: {commit_message}")
    else:
        if "nothing to commit" in output:
            print("ℹ️ 没有新的更改需要提交")
        else:
            print(f"⚠️ 提交失败: {output}")
    
    print("\n🚀 步骤 4: 推送到 GitHub")
    print("-" * 30)
    print("⚠️ 注意：推送可能需要 GitHub 认证")
    print("如果提示输入用户名和密码：")
    print("- 用户名: ShilinYang123")
    print("- 密码: 使用 Personal Access Token (不是 GitHub 密码)")
    
    choice = input("\n是否现在尝试推送? (y/n): ").lower()
    if choice == 'y':
        print("正在推送...")
        success, output = run_git_command('git push -u origin master', project_root)
        if success:
            print("🎉 成功推送到 GitHub!")
            print(f"🔗 仓库地址: {github_url}")
        else:
            print(f"❌ 推送失败: {output}")
            
            print("\n🔧 故障排除:")
            print("1. 确保在 GitHub 上已创建 YDS-Lab 仓库")
            print("2. 检查网络连接")
            print("3. 可能需要生成新的 Personal Access Token:")
            print("   - 访问: https://github.com/settings/tokens")
            print("   - 点击 'Generate new token (classic)'")
            print("   - 选择 'repo' 权限")
            print("   - 复制生成的 token 作为密码使用")
            
            print("\n📋 手动推送命令:")
            print(f"cd {project_root}")
            print("git push -u origin master")
    
    print("\n✅ 设置完成!")
    print("如果推送成功，你的 YDS-Lab 项目现在应该在 GitHub 上可见了。")

if __name__ == "__main__":
    main()