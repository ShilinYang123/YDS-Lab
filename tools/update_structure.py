#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YDS-Lab 目录结构更新工具

功能：
- 扫描项目目录结构
- 生成标准化目录清单
- 支持排除规则
- 输出Markdown格式

适配YDS-Lab项目结构和AI Agent协作需求
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Optional
import yaml

class YDSLabStructureUpdater:
    """YDS-Lab目录结构更新器"""
    
    def __init__(self, project_root: str = "s:/YDS-Lab"):
        self.project_root = Path(project_root)
        self.config_file = self.project_root / "tools" / "structure_config.yaml"
        # 正式与候选清单路径
        self.formal_file = self.project_root / "Struc" / "GeneralOffice" / "Docs" / "YDS-AI-组织与流程" / "《动态目录结构清单》.md"
        self.candidate_file = self.project_root / "Struc" / "GeneralOffice" / "Docs" / "YDS-AI-组织与流程" / "《动态目录结构清单（候选）》.md"
        # 默认输出为候选清单，需批准后方可发布为正式清单
        self.output_file = self.candidate_file
        # 归档与审批默认设置
        self.archive_dir = self.project_root / "Struc" / "GeneralOffice" / "logs" / "structure"
        self.require_approval = True
        self.approval_env_var = "YDS_APPROVE_STRUCTURE"
        self.approval_sentinel = self.project_root / "Struc" / "GeneralOffice" / "Docs" / "YDS-AI-组织与流程" / "APPROVE_UPDATE_STRUCTURE"
        
        # 默认配置
        self.default_config = {
            'exclude_dirs': [
                '.git', '.vscode', '.idea', '__pycache__', '.pytest_cache',
                'node_modules', '.env', '.venv', 'venv', 'env',
                '.DS_Store', 'Thumbs.db', '*.tmp', '*.temp'
            ],
            'exclude_files': [
                '*.pyc', '*.pyo', '*.pyd', '*.so', '*.dll',
                '*.log', '*.tmp', '*.temp', '*.bak', '*.swp',
                '.DS_Store', 'Thumbs.db', 'desktop.ini'
            ],
            'special_handling': {
                'bak': {'max_depth': 2, 'show_files': False},
                'logs': {'max_depth': 2, 'show_files': False},
                'archive': {'max_depth': 1, 'show_files': False}
            }
        }
        
        self.load_config()
        
    def load_config(self):
        """加载配置文件"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    # 合并配置
                    for key, value in config.items():
                        if key in self.default_config:
                            if isinstance(value, dict):
                                self.default_config[key].update(value)
                            else:
                                self.default_config[key] = value
            else:
                # 创建默认配置文件
                self.save_config()
        except Exception as e:
            print(f"配置文件加载失败，使用默认配置: {e}")
            
    def save_config(self):
        """保存配置文件"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.default_config, f, default_flow_style=False, 
                         allow_unicode=True, indent=2)
        except Exception as e:
            print(f"配置文件保存失败: {e}")
            
    def should_exclude_dir(self, dir_name: str) -> bool:
        """检查目录是否应该排除"""
        exclude_dirs = self.default_config.get('exclude_dirs', [])
        return any(
            dir_name == pattern or 
            (pattern.startswith('*') and dir_name.endswith(pattern[1:])) or
            (pattern.endswith('*') and dir_name.startswith(pattern[:-1]))
            for pattern in exclude_dirs
        )
        
    def should_exclude_file(self, file_name: str) -> bool:
        """检查文件是否应该排除"""
        exclude_files = self.default_config.get('exclude_files', [])
        return any(
            file_name == pattern or
            (pattern.startswith('*') and file_name.endswith(pattern[1:])) or
            (pattern.endswith('*') and file_name.startswith(pattern[:-1]))
            for pattern in exclude_files
        )
        
    def get_special_handling(self, dir_name: str) -> Optional[Dict]:
        """获取特殊目录的处理规则"""
        special = self.default_config.get('special_handling', {})
        return special.get(dir_name.lower())
        
    def scan_directory(self, path: Path, max_depth: int = None, 
                      show_files: bool = True, current_depth: int = 0) -> List[str]:
        """扫描目录结构"""
        items = []
        
        if max_depth is not None and current_depth >= max_depth:
            return items
            
        try:
            # 获取目录内容并排序
            entries = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
            
            for entry in entries:
                if entry.is_dir():
                    if self.should_exclude_dir(entry.name):
                        continue
                        
                    # 检查特殊处理规则
                    special = self.get_special_handling(entry.name)
                    if special:
                        sub_max_depth = special.get('max_depth')
                        sub_show_files = special.get('show_files', True)
                    else:
                        sub_max_depth = max_depth
                        sub_show_files = show_files
                        
                    # 添加目录
                    indent = "  " * current_depth
                    items.append(f"{indent}{entry.name}/")
                    
                    # 递归扫描子目录
                    sub_items = self.scan_directory(
                        entry, sub_max_depth, sub_show_files, current_depth + 1
                    )
                    items.extend(sub_items)
                    
                elif entry.is_file() and show_files:
                    if self.should_exclude_file(entry.name):
                        continue
                        
                    indent = "  " * current_depth
                    items.append(f"{indent}{entry.name}")
                    
        except PermissionError:
            indent = "  " * current_depth
            items.append(f"{indent}[权限不足]")
        except Exception as e:
            indent = "  " * current_depth
            items.append(f"{indent}[错误: {str(e)}]")
            
        return items
        
    def generate_structure_markdown(self) -> str:
        """生成目录结构的Markdown文档"""
        print("正在扫描YDS-Lab目录结构...")
        
        # 扫描整个项目结构
        structure_items = self.scan_directory(self.project_root)
        
        # 统计信息
        total_items = len(structure_items)
        dir_count = len([item for item in structure_items if item.strip().endswith('/')])
        file_count = total_items - dir_count
        
        # 生成Markdown内容
        current_time = datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')
        
        # 标题与状态说明（候选/正式）
        is_candidate = (self.output_file == self.candidate_file)
        status_line = "状态: 候选稿（仅用于校验，非标准）" if is_candidate else "状态: 正式版本（标准尺子）"

        markdown_content = f"""# 《动态目录结构清单》

> 本文档由目录结构更新工具自动生成  
> 生成时间: {current_time}  
> 项目根目录: `{self.project_root}`
> {status_line}

## 📊 统计信息

- **总项目数**: {total_items}
- **目录数量**: {dir_count}
- **文件数量**: {file_count}
- **扫描深度**: 自适应（特殊目录有深度限制）

## 📁 目录结构

```
YDS-Lab/
{chr(10).join(structure_items)}
```

## 🔧 核心模块说明

### 📚 Docs/ - 文档中心
YDS AI公司的知识管理中心，包含：
- **YDS-AI-组织与流程/**: AI Agent协作流程和组织架构文档
- **技术文档/**: 技术规范、API文档、架构设计
- **项目文档/**: 项目计划、需求分析、设计文档
- **用户文档/**: 用户手册、操作指南

### 🤖 ai/ - AI智能协作层
CrewAI多智能体协作系统：
- **agents/**: AI Agent定义和配置
- **tasks/**: 任务模板和工作流
- **tools/**: AI专用工具和插件
- **memory/**: 知识库和记忆存储

### 🛠️ tools/ - 工具资产库
项目开发和管理工具集：
- **核心工具**: update_structure.py, check_structure.py, start.py, finish.py
- **配置文件**: structure_config.yaml, tool_config.json
- **辅助脚本**: 各类自动化脚本

### 📦 projects/ - 项目工作区
具体项目的开发空间：
- **active/**: 活跃项目
- **templates/**: 项目模板
- **archive/**: 已完成项目归档

### 🌍 env/ - 环境配置
开发环境和部署配置：
- **development/**: 开发环境配置
- **production/**: 生产环境配置
- **docker/**: 容器化配置

### 📋 meta/ - 元数据管理
项目元信息和配置：
- **configs/**: 全局配置文件
- **schemas/**: 数据结构定义
- **templates/**: 文档和代码模板

## 🚀 AI协作意义

### 1. 标准化协作
- 统一的目录结构便于AI Agent理解项目组织
- 标准化的文件命名和分类规则
- 清晰的职责边界和工作流程

### 2. 知识管理
- 集中化的文档管理（Docs/）
- 结构化的知识存储（ai/memory/）
- 版本化的配置管理（meta/configs/）

### 3. 自动化支持
- 工具驱动的开发流程（tools/）
- 环境一致性保障（env/）
- 项目模板化（projects/templates/）

### 4. 协作效率
- 多Agent并行工作支持
- 任务分解和分配机制
- 实时状态同步和监控

## ⚙️ 配置说明

目录结构扫描配置文件: `tools/structure_config.yaml`

### 排除规则
- **目录排除**: {', '.join(self.default_config['exclude_dirs'])}
- **文件排除**: {', '.join(self.default_config['exclude_files'])}

### 特殊处理
- **bak/**: 限制扫描深度，不显示文件详情
- **logs/**: 限制扫描深度，不显示文件详情  
- **archive/**: 仅显示一级目录

## 📝 更新说明

本文档通过 `tools/update_structure.py` 自动生成和更新。

### 手动更新命令
```bash
cd S:\\YDS-Lab
python tools\\update_structure.py
```

### 自动更新触发
- 项目结构发生重大变化时
- 新增核心目录或模块时
- 定期维护更新（建议每周）

---

*本文档是YDS-Lab项目的核心组织文档，请保持其准确性和时效性。*
"""

        return markdown_content
        
    def update_structure_document(self, finalize: bool = False):
        """更新目录结构文档"""
        try:
            print("开始更新YDS-Lab目录结构文档...")
            
            # 写入候选清单
            self.output_file = self.candidate_file
            self.output_file.parent.mkdir(parents=True, exist_ok=True)
            candidate_md = self.generate_structure_markdown()
            with open(self.candidate_file, 'w', encoding='utf-8') as f:
                f.write(candidate_md)
            print(f"✅ 候选目录结构清单已更新: {self.candidate_file}")
            
            # 判断是否发布为正式清单
            env_approved = os.environ.get(self.approval_env_var, "0") in ("1", "true", "True")
            sentinel_approved = self.approval_sentinel.exists()
            should_finalize = finalize or (env_approved or sentinel_approved)
            
            if should_finalize:
                # 归档旧正式清单（若存在）
                self.archive_dir.mkdir(parents=True, exist_ok=True)
                if self.formal_file.exists():
                    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                    archive_path = self.archive_dir / f"动态目录结构清单_旧版_{ts}.md"
                    try:
                        # 同时打开旧正式清单与归档文件进行内容复制
                        with open(self.formal_file, 'r', encoding='utf-8') as rf, open(archive_path, 'w', encoding='utf-8') as wf:
                            wf.write(rf.read())
                        print(f"📦 已归档旧正式清单: {archive_path}")
                    except Exception as ae:
                        print(f"⚠️ 归档失败，但继续发布: {ae}")
                
                # 生成正式清单内容（无候选水印）并写入
                self.output_file = self.formal_file
                self.output_file.parent.mkdir(parents=True, exist_ok=True)
                formal_md = self.generate_structure_markdown()
                with open(self.formal_file, 'w', encoding='utf-8') as f:
                    f.write(formal_md)
                print(f"✅ 正式目录结构清单已发布: {self.formal_file}")
            else:
                print("⛔ 未获批准，已生成候选清单但未更新正式清单。")
                print(f"如需发布，请使用 --finalize 参数或设置环境变量 {self.approval_env_var}=1，或创建哨兵文件: {self.approval_sentinel}")
            
            # 获取详细统计信息
            structure_items = self.scan_directory(self.project_root)
            total_items = len(structure_items)
            dir_count = len([item for item in structure_items if item.strip().endswith('/')])
            file_count = total_items - dir_count
            
            print(f"📊 扫描完成，共处理 {total_items} 个项目")
            print(f"   📁 目录数量: {dir_count}")
            print(f"   📄 文件数量: {file_count}")
            
            return True
            
        except Exception as e:
            print(f"❌ 更新失败: {e}")
            return False

def main():
    """主函数"""
    import argparse
    parser = argparse.ArgumentParser(description="更新YDS-Lab目录结构清单（默认生成候选稿，需批准才发布正式清单）")
    parser.add_argument("--project-root", default="s:/YDS-Lab", help="项目根目录路径")
    parser.add_argument("--finalize", action="store_true", help="发布为正式清单（需有批准）")
    args = parser.parse_args()
    
    updater = YDSLabStructureUpdater(args.project_root)
    success = updater.update_structure_document(finalize=args.finalize)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()