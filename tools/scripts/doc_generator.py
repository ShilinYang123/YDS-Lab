#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YDS-Lab 文档生成器
用于自动化生成和维护项目文档
"""

import os
import re
import json
import ast
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


def create_project_structure_doc(project_root: Path) -> str:
    """生成项目结构文档"""
    structure = analyze_project_structure(project_root)
    
    doc_content = f"""# YDS-Lab 项目结构文档

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 项目概览

YDS-Lab 是一个多智能体协作系统，包含以下主要组件：

{generate_structure_overview(structure)}

## 目录结构

{generate_directory_tree(structure)}

## 模块说明

{generate_module_descriptions(structure)}

## 配置文件

{generate_config_files_description(structure)}

---
*本文档由自动化工具生成，最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    return doc_content


def analyze_project_structure(project_root: Path) -> Dict[str, Any]:
    """分析项目结构"""
    structure = {
        'root_files': [],
        'directories': {},
        'python_files': [],
        'config_files': [],
        'total_files': 0,
        'total_python_files': 0
    }
    
    # 分析根目录
    for item in project_root.iterdir():
        if item.is_file():
            structure['root_files'].append({
                'name': item.name,
                'size': item.stat().st_size,
                'modified': datetime.fromtimestamp(item.stat().st_mtime).strftime('%Y-%m-%d')
            })
            structure['total_files'] += 1
            
            if item.suffix == '.py':
                structure['total_python_files'] += 1
                structure['python_files'].append(str(item.relative_to(project_root)))
            elif item.suffix in ['.json', '.yaml', '.yml', '.toml', '.ini', '.cfg']:
                structure['config_files'].append(item.name)
                
        elif item.is_dir() and item.name not in ['__pycache__', '.git', '.venv', 'venv']:
            dir_info = analyze_directory(item)
            structure['directories'][item.name] = dir_info
            structure['total_files'] += dir_info['file_count']
            structure['total_python_files'] += dir_info['python_count']
            
    return structure


def analyze_directory(dir_path: Path) -> Dict[str, Any]:
    """分析目录内容"""
    info = {
        'file_count': 0,
        'python_count': 0,
        'subdirs': [],
        'files': [],
        'description': get_directory_description(dir_path.name)
    }
    
    try:
        for item in dir_path.rglob('*'):
            if item.is_file():
                info['file_count'] += 1
                if item.suffix == '.py':
                    info['python_count'] += 1
                    
        # 获取直接子目录和文件
        for item in dir_path.iterdir():
            if item.is_dir() and item.name not in ['__pycache__', '.git']:
                info['subdirs'].append(item.name)
            elif item.is_file():
                info['files'].append(item.name)
                
    except (PermissionError, OSError):
        pass
        
    return info


def get_directory_description(dir_name: str) -> str:
    """获取目录描述"""
    descriptions = {
        '01-struc': '项目核心结构目录，包含主要的智能体系统',
        '02-assets': '项目资源文件，包括图片、文档等',
        '03-dev': '开发中的项目和实验性功能',
        '04-prod': '生产环境的项目和功能',
        '05-archive': '归档的旧项目和备份',
        '06-temp': '临时文件和工作目录',
        'tools': '项目工具脚本和辅助程序',
        'config': '配置文件目录',
        'docs': '项目文档',
        'backups': '备份文件',
        'logs': '日志文件'
    }
    return descriptions.get(dir_name, '未分类目录')


def generate_structure_overview(structure: Dict[str, Any]) -> str:
    """生成结构概览"""
    overview = f"""- 总文件数: {structure['total_files']}
- Python文件数: {structure['total_python_files']}
- 主要目录: {len(structure['directories'])} 个"""
    
    if structure['config_files']:
        overview += f"\n- 配置文件: {len(structure['config_files'])} 个"
        
    return overview


def generate_directory_tree(structure: Dict[str, Any], max_depth: int = 3) -> str:
    """生成目录树"""
    tree_lines = []
    
    def add_tree_items(items: List[str], prefix: str = "") -> None:
        for i, item in enumerate(sorted(items)):
            is_last = i == len(items) - 1
            current_prefix = "└── " if is_last else "├── "
            tree_lines.append(f"{prefix}{current_prefix}{item}")
            
    # 根目录文件
    if structure['root_files']:
        tree_lines.append(".")
        root_files = [f["name"] for f in structure['root_files']]
        add_tree_items(root_files)
        
    # 主要目录
    if structure['directories']:
        if not tree_lines:
            tree_lines.append(".")
        
        dir_names = sorted(structure['directories'].keys())
        for i, dir_name in enumerate(dir_names):
            is_last = i == len(dir_names) - 1
            prefix = "└── " if is_last else "├── "
            tree_lines.append(f"{prefix}{dir_name}/")
            
            # 显示子目录（简化版）
            dir_info = structure['directories'][dir_name]
            if dir_info['subdirs']:
                sub_prefix = "    " if is_last else "│   "
                for j, subdir in enumerate(sorted(dir_info['subdirs'])[:3]):
                    sub_is_last = j == min(2, len(dir_info['subdirs']) - 1)
                    sub_prefix_symbol = "└── " if sub_is_last else "├── "
                    tree_lines.append(f"{sub_prefix}{sub_prefix_symbol}{subdir}/")
                    
                if len(dir_info['subdirs']) > 3:
                    tree_lines.append(f"{sub_prefix}└── ... ({len(dir_info['subdirs']) - 3} 更多)")
                    
    return "\n".join(tree_lines)


def generate_module_descriptions(structure: Dict[str, Any]) -> str:
    """生成模块说明"""
    descriptions = []
    
    for dir_name, dir_info in structure['directories'].items():
        if dir_info['python_count'] > 0:
            descriptions.append(f"### {dir_name}/")
            descriptions.append(f"{dir_info['description']}")
            descriptions.append(f"- Python文件数: {dir_info['python_count']}")
            descriptions.append(f"- 总文件数: {dir_info['file_count']}")
            
            if dir_info['subdirs']:
                descriptions.append(f"- 子目录: {', '.join(dir_info['subdirs'][:5])}")
                if len(dir_info['subdirs']) > 5:
                    descriptions.append(f"  ... 还有 {len(dir_info['subdirs']) - 5} 个")
                    
            descriptions.append("")
            
    return "\n".join(descriptions) if descriptions else "暂无模块说明"


def generate_config_files_description(structure: Dict[str, Any]) -> str:
    """生成配置文件说明"""
    if not structure['config_files']:
        return "暂无配置文件"
        
    descriptions = []
    for config_file in structure['config_files']:
        descriptions.append(f"- **{config_file}**: 配置文件")
        
    return "\n".join(descriptions)


def create_readme_template() -> str:
    """创建README模板"""
    return """# YDS-Lab 项目

## 项目简介

YDS-Lab 是一个多智能体协作系统，旨在提供高效、智能的自动化解决方案。

## 项目结构

```
项目根目录/
├── 01-struc/          # 核心结构
├── 02-assets/         # 项目资源
├── 03-dev/            # 开发项目
├── 04-prod/           # 生产项目
├── tools/             # 工具脚本
├── docs/              # 项目文档
└── config/            # 配置文件
```

## 快速开始

### 环境要求

- Python 3.8+
- 相关依赖包

### 安装步骤

1. 克隆项目
2. 安装依赖
3. 运行配置脚本

### 基本使用

```bash
# 运行主程序
python ch.py

# 查看帮助
python ch.py --help
```

## 文档

- [项目结构](docs/project_structure.md)
- [API文档](docs/api_documentation.md)
- [配置说明](docs/configuration.md)

## 贡献指南

欢迎提交Issue和Pull Request。

## 许可证

[许可证信息]

---
*最后更新: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "*"


def save_documentation(content: str, filename: str, docs_dir: Path) -> Path:
    """保存文档"""
    # 确保docs目录存在
    docs_dir.mkdir(exist_ok=True)
    
    doc_path = docs_dir / filename
    with open(doc_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    return doc_path


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='YDS-Lab 文档生成器')
    parser.add_argument('--type', choices=['structure', 'readme', 'all'], 
                       default='all', help='生成的文档类型')
    parser.add_argument('--output', type=str, help='输出目录')
    
    args = parser.parse_args()
    
    # 自动查找项目根目录
    project_root = Path.cwd()
    
    # 确保输出目录存在
    docs_dir = Path(args.output) if args.output else project_root / "docs"
    docs_dir.mkdir(exist_ok=True)
    
    print(f"开始生成文档到: {docs_dir}")
    
    generated_files = []
    
    try:
        if args.type in ['structure', 'all']:
            print("生成项目结构文档...")
            structure_doc = create_project_structure_doc(project_root)
            structure_path = save_documentation(structure_doc, "project_structure.md", docs_dir)
            generated_files.append(structure_path)
            print(f"✅ 项目结构文档已生成: {structure_path}")
            
        if args.type in ['readme', 'all']:
            print("生成README模板...")
            readme_content = create_readme_template()
            readme_path = save_documentation(readme_content, "README.md", docs_dir)
            generated_files.append(readme_path)
            print(f"✅ README模板已生成: {readme_path}")
            
        print(f"\n文档生成完成！共生成 {len(generated_files)} 个文件:")
        for file_path in generated_files:
            print(f"  - {file_path}")
            
        return 0
        
    except Exception as e:
        print(f"文档生成失败: {e}")
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())