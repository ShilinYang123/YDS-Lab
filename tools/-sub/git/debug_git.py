#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试 Git 初始化过程
"""

import os
import sys
from pathlib import Path

# 添加 tools 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tools'))

def main():
    print("🔍 调试 Git 初始化过程...")
    
    # 检查当前目录
    current_dir = Path(__file__).parent
    print(f"当前目录: {current_dir}")
    print(f"当前目录绝对路径: {current_dir.resolve()}")
    
    # 检查 .git 目录
    git_dir = current_dir / ".git"
    print(f".git 目录: {git_dir}")
    print(f".git 目录存在: {git_dir.exists()}")
    
    if git_dir.exists():
        print(f".git 目录内容:")
        for item in git_dir.iterdir():
            print(f"  {item.name}")
    
    # 检查 Git 可执行文件
    git_paths = [
        r"C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\Common7\IDE\CommonExtensions\Microsoft\TeamFoundation\Team Explorer\Git\cmd\git.exe",
        r"C:\Program Files\Git\bin\git.exe",
        r"C:\Program Files (x86)\Git\bin\git.exe"
    ]
    
    print("\n检查 Git 可执行文件:")
    for path in git_paths:
        exists = os.path.exists(path)
        print(f"  {path}: {'✅' if exists else '❌'}")
    
    # 尝试导入 GitPython
    print("\n检查 GitPython:")
    try:
        import git
        from git import Repo, InvalidGitRepositoryError
        print("✅ GitPython 可用")
        
        # 尝试连接到仓库
        try:
            repo = Repo(current_dir)
            print(f"✅ 成功连接到 Git 仓库")
            print(f"仓库根目录: {repo.working_dir}")
            print(f"当前分支: {repo.active_branch.name}")
        except InvalidGitRepositoryError:
            print("❌ 当前目录不是有效的 Git 仓库")
        except Exception as e:
            print(f"❌ 连接仓库失败: {e}")
            
    except ImportError:
        print("❌ GitPython 不可用")

if __name__ == "__main__":
    main()