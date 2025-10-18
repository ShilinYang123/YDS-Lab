#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 Git 远程仓库配置
"""

import os
import sys

# 添加 tools 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tools'))

from git_tools.git_helper import GitHelper

def main():
    print("🔍 检查 Git 远程仓库配置...")
    
    try:
        # 使用当前目录作为项目根目录
        project_root = os.path.dirname(__file__)
        git_helper = GitHelper(project_root)
        
        # 检查远程仓库
        if git_helper.repo:
            print(f"✅ Git 仓库已初始化: {git_helper.project_root}")
            
            # 获取远程仓库列表
            remotes = list(git_helper.repo.remotes)
            if remotes:
                print(f"📡 远程仓库配置:")
                for remote in remotes:
                    print(f"   {remote.name}: {remote.url}")
            else:
                print("⚠️ 未配置远程仓库")
                print("💡 建议配置 GitHub 远程仓库:")
                print("   git remote add origin https://github.com/your-username/YDS-Lab.git")
        else:
            print("❌ 未找到 Git 仓库")
            
    except Exception as e:
        print(f"❌ 检查失败: {e}")

if __name__ == "__main__":
    main()