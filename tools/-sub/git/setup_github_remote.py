#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置 GitHub 远程仓库
"""

import os
import sys

# 添加 tools 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tools'))

from git_tools.git_helper import GitHelper

def main():
    print("🔧 配置 GitHub 远程仓库...")
    
    try:
        # 使用当前目录作为项目根目录
        project_root = os.path.dirname(__file__)
        git_helper = GitHelper(project_root)
        
        if git_helper.repo:
            print(f"✅ Git 仓库已连接: {git_helper.project_root}")
            
            # 检查是否已有远程仓库
            remotes = list(git_helper.repo.remotes)
            if remotes:
                print("📡 当前远程仓库配置:")
                for remote in remotes:
                    print(f"   {remote.name}: {remote.url}")
                    
                # 询问是否要更新
                choice = input("是否要更新远程仓库配置? (y/n): ").lower()
                if choice != 'y':
                    print("取消操作")
                    return
            
            # 配置远程仓库
            github_url = input("请输入 GitHub 仓库 URL (例: https://github.com/username/YDS-Lab.git): ").strip()
            
            if not github_url:
                print("❌ 未提供 GitHub URL")
                return
                
            try:
                # 如果已存在 origin，先删除
                if 'origin' in [r.name for r in remotes]:
                    git_helper.repo.delete_remote('origin')
                    print("🗑️ 已删除旧的 origin 远程仓库")
                
                # 添加新的远程仓库
                origin = git_helper.repo.create_remote('origin', github_url)
                print(f"✅ 已添加远程仓库: {github_url}")
                
                # 验证连接
                try:
                    origin.fetch()
                    print("✅ 远程仓库连接验证成功")
                except Exception as e:
                    print(f"⚠️ 远程仓库连接验证失败: {e}")
                    print("这可能是因为仓库不存在或网络问题")
                    
            except Exception as e:
                print(f"❌ 配置远程仓库失败: {e}")
                
        else:
            print("❌ 未找到 Git 仓库")
            
    except Exception as e:
        print(f"❌ 操作失败: {e}")

if __name__ == "__main__":
    main()