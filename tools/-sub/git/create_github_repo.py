#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动创建和配置 GitHub 仓库
"""

import os
import sys
import subprocess

# 添加 tools 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tools'))

from git_tools.git_helper import GitHelper

def run_git_command(command, cwd=None):
    """运行 Git 命令"""
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, 
                              capture_output=True, text=True, encoding='utf-8')
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, result.stderr.strip()
    except Exception as e:
        return False, str(e)

def main():
    print("🚀 配置 YDS-Lab GitHub 仓库...")
    
    try:
        # 使用当前目录作为项目根目录
        project_root = os.path.dirname(__file__)
        git_helper = GitHelper(project_root)
        
        if not git_helper.repo:
            print("❌ 未找到 Git 仓库")
            return
            
        print(f"✅ Git 仓库已连接: {git_helper.project_root}")
        
        # 配置 Git 用户信息
        print("\n📝 配置 Git 用户信息...")
        success, _ = run_git_command('git config user.name "ShilinYang123"', project_root)
        if success:
            print("✅ 已设置用户名: ShilinYang123")
        
        success, _ = run_git_command('git config user.email "shilinyang123@gmail.com"', project_root)
        if success:
            print("✅ 已设置邮箱: shilinyang123@gmail.com")
        
        # 检查当前远程仓库
        remotes = list(git_helper.repo.remotes)
        if remotes:
            print("\n📡 当前远程仓库配置:")
            for remote in remotes:
                print(f"   {remote.name}: {remote.url}")
        
        # 手动配置远程仓库 URL
        github_url = "https://github.com/ShilinYang123/YDS-Lab.git"
        
        try:
            # 如果已存在 origin，先删除
            if 'origin' in [r.name for r in remotes]:
                git_helper.repo.delete_remote('origin')
                print("🗑️ 已删除旧的 origin 远程仓库")
            
            # 添加新的远程仓库
            origin = git_helper.repo.create_remote('origin', github_url)
            print(f"✅ 已添加远程仓库: {github_url}")
            
            # 添加所有文件到暂存区
            print("\n📦 准备提交文件...")
            git_helper.repo.git.add('.')
            print("✅ 已添加所有文件到暂存区")
            
            # 提交更改
            try:
                commit_message = "Initial commit: YDS-Lab AI智能协作系统"
                git_helper.repo.index.commit(commit_message)
                print(f"✅ 已提交更改: {commit_message}")
            except Exception as e:
                if "nothing to commit" in str(e):
                    print("ℹ️ 没有新的更改需要提交")
                else:
                    print(f"⚠️ 提交失败: {e}")
            
            # 推送到远程仓库
            print("\n🚀 推送到 GitHub...")
            print("⚠️ 注意：首次推送需要在 GitHub 上手动创建仓库")
            print(f"   请访问: https://github.com/new")
            print(f"   仓库名称: YDS-Lab")
            print(f"   描述: YDS-Lab AI智能协作系统 - 企业级AI开发与协作平台")
            print(f"   设置为公开仓库")
            print(f"   不要初始化 README、.gitignore 或 license")
            
            choice = input("\n是否现在尝试推送? (y/n): ").lower()
            if choice == 'y':
                try:
                    # 尝试推送
                    origin.push(refspec='master:main', force=True)
                    print("✅ 成功推送到 GitHub!")
                except Exception as e:
                    print(f"❌ 推送失败: {e}")
                    print("\n💡 可能的解决方案:")
                    print("1. 确保在 GitHub 上已创建 YDS-Lab 仓库")
                    print("2. 检查网络连接")
                    print("3. 确保有推送权限")
                    
                    # 提供手动推送命令
                    print("\n🔧 手动推送命令:")
                    print(f"cd {project_root}")
                    print("git push -u origin master:main")
            
        except Exception as e:
            print(f"❌ 配置远程仓库失败: {e}")
            
    except Exception as e:
        print(f"❌ 操作失败: {e}")

if __name__ == "__main__":
    main()