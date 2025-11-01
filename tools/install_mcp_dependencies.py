#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP依赖安装器
功能：安装所有MCP服务器所需的依赖项
"""

import subprocess
import sys
import os
from pathlib import Path

class MCPDependencyInstaller:
    """MCP依赖安装器"""
    
    def __init__(self):
        self.dependencies = {
            "GitHub": ["PyGithub", "requests", "gitpython"],
            "Excel": ["openpyxl", "pandas", "xlsxwriter"],
            "Figma": ["requests", "pillow", "figma-api"],
            "Builder": ["docker", "pyyaml", "jinja2"],
            "FileSystem": ["watchdog", "send2trash"],
            "Database": ["sqlalchemy", "sqlite3", "pymongo"]
        }
        
    def install_all_dependencies(self):
        """安装所有依赖"""
        print("🔧 开始安装MCP服务器依赖项...")
        print("=" * 60)
        
        all_deps = set()
        for server, deps in self.dependencies.items():
            all_deps.update(deps)
            
        # 移除内置模块
        builtin_modules = {"sqlite3", "subprocess", "pathlib", "shutil", "asyncio", "logging", "json", "datetime", "typing"}
        all_deps = all_deps - builtin_modules
        
        print(f"📦 需要安装的依赖项: {len(all_deps)} 个")
        print("-" * 40)
        
        success_count = 0
        failed_deps = []
        
        for dep in sorted(all_deps):
            print(f"📦 安装: {dep}")
            
            try:
                # 尝试安装依赖
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", dep
                ], capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    print(f"✅ {dep} 安装成功")
                    success_count += 1
                else:
                    print(f"❌ {dep} 安装失败: {result.stderr}")
                    failed_deps.append(dep)
                    
            except subprocess.TimeoutExpired:
                print(f"⏰ {dep} 安装超时")
                failed_deps.append(dep)
            except Exception as e:
                print(f"❌ {dep} 安装异常: {e}")
                failed_deps.append(dep)
                
        print("\n" + "=" * 60)
        print(f"📊 安装结果:")
        print(f"✅ 成功: {success_count}/{len(all_deps)} ({success_count/len(all_deps)*100:.1f}%)")
        
        if failed_deps:
            print(f"❌ 失败: {len(failed_deps)} 个")
            print("失败的依赖项:")
            for dep in failed_deps:
                print(f"  - {dep}")
                
            # 尝试替代安装方法
            print("\n🔄 尝试替代安装方法...")
            self._try_alternative_installation(failed_deps)
        else:
            print("🎉 所有依赖项安装成功！")
            
    def _try_alternative_installation(self, failed_deps: list):
        """尝试替代安装方法"""
        alternatives = {
            "figma-api": ["figma-python", "pyfigma"],
            "docker": ["docker-py", "python-docker"],
            "PyGithub": ["github3.py", "pygithub3"]
        }
        
        for dep in failed_deps:
            if dep in alternatives:
                print(f"\n🔄 尝试 {dep} 的替代方案...")
                
                for alt in alternatives[dep]:
                    try:
                        result = subprocess.run([
                            sys.executable, "-m", "pip", "install", alt
                        ], capture_output=True, text=True, timeout=300)
                        
                        if result.returncode == 0:
                            print(f"✅ 替代方案 {alt} 安装成功")
                            break
                        else:
                            print(f"❌ 替代方案 {alt} 安装失败")
                            
                    except Exception as e:
                        print(f"❌ 替代方案 {alt} 安装异常: {e}")
                        
    def create_requirements_files(self):
        """为每个MCP服务器创建requirements.txt"""
        print("\n🔧 更新MCP服务器requirements.txt文件...")
        print("=" * 60)
        
        project_root = Path(__file__).parent.parent
        mcp_cluster = project_root / "Struc" / "MCPCluster"
        
        for server, deps in self.dependencies.items():
            server_path = mcp_cluster / server
            requirements_path = server_path / "requirements.txt"
            
            if server_path.exists():
                print(f"📝 更新 {server}/requirements.txt")
                
                with open(requirements_path, 'w', encoding='utf-8') as f:
                    for dep in sorted(deps):
                        f.write(f"{dep}\n")
                        
                print(f"✅ {server} requirements.txt 更新完成")
            else:
                print(f"⚠️ {server} 目录不存在，跳过")
                
    def verify_installation(self):
        """验证安装结果"""
        print("\n🔍 验证依赖安装结果...")
        print("=" * 60)
        
        all_deps = set()
        for deps in self.dependencies.values():
            all_deps.update(deps)
            
        # 移除内置模块
        builtin_modules = {"sqlite3", "subprocess", "pathlib", "shutil", "asyncio", "logging", "json", "datetime", "typing"}
        all_deps = all_deps - builtin_modules
        
        success_count = 0
        failed_imports = []
        
        for dep in sorted(all_deps):
            try:
                # 尝试导入模块
                if dep == "PyGithub":
                    import github
                elif dep == "figma-api":
                    # figma-api可能有不同的导入名称
                    try:
                        import figma
                    except ImportError:
                        import pyfigma
                elif dep == "docker":
                    import docker
                elif dep == "openpyxl":
                    import openpyxl
                elif dep == "pandas":
                    import pandas
                elif dep == "pillow":
                    import PIL
                elif dep == "requests":
                    import requests
                elif dep == "xlsxwriter":
                    import xlsxwriter
                elif dep == "gitpython":
                    import git
                elif dep == "pyyaml":
                    import yaml
                elif dep == "jinja2":
                    import jinja2
                elif dep == "watchdog":
                    import watchdog
                elif dep == "send2trash":
                    import send2trash
                elif dep == "sqlalchemy":
                    import sqlalchemy
                elif dep == "pymongo":
                    import pymongo
                else:
                    __import__(dep)
                    
                print(f"✅ {dep} 导入成功")
                success_count += 1
                
            except ImportError as e:
                print(f"❌ {dep} 导入失败: {e}")
                failed_imports.append(dep)
            except Exception as e:
                print(f"⚠️ {dep} 验证异常: {e}")
                failed_imports.append(dep)
                
        print(f"\n📊 验证结果: {success_count}/{len(all_deps)} ({success_count/len(all_deps)*100:.1f}%)")
        
        if failed_imports:
            print(f"❌ 导入失败的依赖: {failed_imports}")
            return False
        else:
            print("🎉 所有依赖验证成功！")
            return True

def main():
    """主函数"""
    print("🔧 YDS-Lab MCP依赖安装器")
    print("=" * 60)
    
    installer = MCPDependencyInstaller()
    
    # 安装依赖
    installer.install_all_dependencies()
    
    # 更新requirements文件
    installer.create_requirements_files()
    
    # 验证安装
    success = installer.verify_installation()
    
    if success:
        print("\n🎉 MCP依赖安装和验证完成！")
        print("现在可以运行MCP服务器了。")
    else:
        print("\n⚠️ 部分依赖安装失败，请手动检查和安装。")

if __name__ == "__main__":
    main()