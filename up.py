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
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import yaml
import re

class YDSLabStructureUpdater:
    """YDS-Lab目录结构更新器"""
    
    def __init__(self, project_root: str = "S:/YDS-Lab"):
        self.project_root = Path(project_root)
        # 配置文件集中至 /config，禁止回退到 /tools/structure_config.yaml
        cfg_new = self.project_root / "config" / "structure_config.yaml"
        self.config_file = cfg_new
        # 正式与候选清单路径（统一新路径 01-struc/0B-general-manager；旧路径仅作为历史记录，不再回退）
        self.formal_file = (
            self.project_root
            / "01-struc" / "0B-general-manager" / "Docs" / "YDS-AI-组织与流程"
            / "《动态目录结构清单》.md"
        )
        self.candidate_file = (
            self.project_root
            / "01-struc" / "0B-general-manager" / "Docs" / "YDS-AI-组织与流程"
            / "《动态目录结构清单（候选）》.md"
        )
        # 默认输出为候选清单，需批准后方可发布为正式清单
        self.output_file = self.candidate_file
        # 归档与审批默认设置（日志统一至 01-struc/0B-general-manager/logs/structure）
        self.archive_dir = (
            self.project_root / "01-struc" / "0B-general-manager" / "logs" / "structure"
        )
        self.require_approval = True
        self.approval_env_var = "YDS_APPROVE_STRUCTURE"
        self.approval_sentinel = (
            self.project_root
            / "01-struc" / "0B-general-manager" / "Docs" / "YDS-AI-组织与流程"
            / "APPROVE_UPDATE_STRUCTURE"
        )
        # 需要在架构设计文档中永久记录的维护说明（新路径优先）
        self.architecture_doc = (
            self.project_root
            / "01-struc" / "0B-general-manager" / "Docs" / "YDS-AI-组织与流程"
            / "项目架构设计.md"
        )
        self.architecture_doc_old = (
            self.project_root
            / "Struc" / "GeneralOffice" / "Docs" / "YDS-AI-组织与流程"
            / "项目架构设计.md"
        )
        # 旧路径的正式清单（用于归档历史版本）
        self.formal_old = (
            self.project_root
            / "Struc" / "GeneralOffice" / "Docs" / "YDS-AI-组织与流程"
            / "《动态目录结构清单》.md"
        )
        self.venv_path = str(self.project_root / ".venv")
        venv_display = (
            self.venv_path[0].upper() + self.venv_path[1:]
            if len(self.venv_path) >= 2 and self.venv_path[1] == ':' and self.venv_path[0].isalpha()
            else self.venv_path
        )
        self.maintenance_note = (
            f"维护说明：近期策略调整——已将 `.venv`（{venv_display}）纳入 `.gitignore` 忽略，"
            f"并在结构扫描中排除，确保本地虚拟环境不进入版本库且不参与目录结构统计。"
        )
        
        # 默认配置 - 严格按照《规范与流程.md》第3.3节规定
        self.default_config = {
            'exclude_dirs': [
                # 规范文档第3.3节：完全排除的目录
                '.git',           # Git版本控制目录
                '__pycache__',    # Python缓存目录
                '.venv', 'venv', 'env',  # 虚拟环境目录
                # 备份目录：完全排除
                'bak', 'backup', 'backups', 'Backup', 'Backups',
                # 额外的开发环境目录（保持兼容性）
                '.vscode', '.idea', '.pytest_cache',
                'node_modules', '.env'
            ],
            'exclude_files': [
                # 规范文档第3.3节：完全排除的文件
                '*.pyc', '*.pyo', '*.pyd',  # Python编译缓存文件
                '*.log', '*.tmp', '*.temp',  # 临时和日志文件
                '.DS_Store', 'Thumbs.db',   # 系统文件
                # 额外的常见排除文件（保持兼容性）
                '*.bak', '*.swp', 'desktop.ini',
                '*.so', '*.dll'
            ],
            'special_handling': {
                # 规范文档第2.2节：特殊目录处理规则
                'Log': {'max_depth': 2, 'show_files': False},      # Log目录：最大深度2层，不显示具体文件
                'archive': {'max_depth': 1, 'show_files': False},  # 归档目录：最大深度1层，不显示具体文件
                'archives': {'max_depth': 1, 'show_files': False},  # 归档目录：最大深度1层，不显示具体文件
                'logs': {'max_depth': 2, 'show_files': False}      # 日志目录：最大深度2层，不显示具体文件
            },
            'hidden_dirs_handling': {
                # 隐藏目录（以"."开头）：仅显示目录本身，不扫描内容
                'max_depth': 0, 'show_files': False
            }
        }
        
        self.load_config()

    def emit_longmemory_event(self, event_type: str, topic: str, payload: Dict[str, Any]) -> None:
        """调用 LongMemory 事件记录工具，将事件写入本地并可选上报HTTP。

        该方法为软依赖：record_event.py 不存在时不会中断主流程。
        """
        try:
            script = self.project_root / 'tools' / 'LongMemory' / 'record_event.py'
            if not script.exists():
                print(f"[LongMemory] 未找到事件记录脚本: {script}")
                return
            cmd = [sys.executable, str(script), '--type', event_type, '--topic', topic,
                   '--source', 'tools/up.py', '--payload', json.dumps(payload, ensure_ascii=False)]
            subprocess.run(cmd, check=False)
        except Exception as e:
            print(f"[LongMemory] 事件记录失败（忽略不影响主流程）: {e}")
        
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
                yaml.dump(
                    self.default_config,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    indent=2,
                )
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
        
        # 检查隐藏目录（以"."开头）
        if dir_name.startswith('.'):
            return self.default_config.get('hidden_dirs_handling', {})
        
        # 大小写不敏感匹配
        dir_name_lower = dir_name.lower()
        for key, value in special.items():
            if key.lower() == dir_name_lower:
                return value
                
        return None
        
    def scan_directory(
        self,
        path: Path,
        max_depth: int = None,
        show_files: bool = True,
        current_depth: int = 0,
        parent_special_handling: Optional[Dict] = None,
    ) -> List[str]:
        """扫描目录结构"""
        items = []
        
        if max_depth is not None and current_depth >= max_depth:
            return items
            
        try:
            # 获取目录内容并排序
            entries = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
            
            for entry in entries:
                if entry.is_dir():
                    # 检查是否应该排除目录
                    if self.should_exclude_dir(entry.name):
                        continue
                        
                    # 检查特殊处理规则
                    special = self.get_special_handling(entry.name)
                    
                    # 如果当前目录有特殊规则，使用它；否则继承父级规则
                    effective_special = special or parent_special_handling
                    
                    if effective_special:
                        sub_max_depth = effective_special.get('max_depth')
                        sub_show_files = effective_special.get('show_files', True)
                        # 调整最大深度：如果是特殊目录的根，从当前深度开始计算
                        if special:  # 这是特殊目录的根
                            adjusted_max_depth = current_depth + sub_max_depth if sub_max_depth else None
                        else:  # 继承父级规则
                            adjusted_max_depth = max_depth
                    else:
                        sub_max_depth = max_depth
                        sub_show_files = show_files
                        adjusted_max_depth = max_depth
                        
                    # 添加目录
                    indent = "  " * current_depth
                    items.append(f"{indent}{entry.name}/")
                    
                    # 递归扫描子目录
                    scan_kwargs = {
                        'path': entry,
                        'max_depth': adjusted_max_depth,
                        'show_files': sub_show_files,
                        'current_depth': current_depth + 1,
                        'parent_special_handling': effective_special,
                    }
                    sub_items = self.scan_directory(**scan_kwargs)
                    items.extend(sub_items)
                    
                elif entry.is_file() and show_files:
                    # 检查是否应该排除文件
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

        # 规范化项目根路径显示（大写盘符）
        display_root = str(self.project_root)
        if len(display_root) >= 2 and display_root[1] == ':' and display_root[0].isalpha():
            display_root = display_root[0].upper() + display_root[1:]

        markdown_content = f"""# 《动态目录结构清单》

> 本文档由目录结构更新工具自动生成  
> 生成时间: {current_time}  
> 项目根目录: `{display_root}`
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

### 🧪 03-dev/ - 开发工作区（优先）
具体项目的开发空间（优先目录）：
- **active/**: 活跃项目（若存在）
- **templates/**: 项目模板（优先）
- **docs/**: 开发文档与交付总结（如 DELIVERY_SUMMARY.md）
 - 说明：03-dev 为唯一标准工作区。旧路径 projects/ 已废弃，不再作为回退或创建目标。



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
 - 项目模板化（仅 03-dev/templates/）

### 4. 协作效率
- 多Agent并行工作支持
- 任务分解和分配机制
- 实时状态同步和监控

## ⚙️ 配置说明

目录结构扫描配置文件: `config/structure_config.yaml`

### 排除规则
- **目录排除**: {', '.join(self.default_config['exclude_dirs'])}
- **文件排除**: {', '.join(self.default_config['exclude_files'])}

### 特殊处理
- **bak/**: 限制扫描深度，不显示文件详情
- **logs/**: 限制扫描深度，不显示文件详情  
- **archive/**: 仅显示一级目录

## 📝 更新说明

本文档通过 `tools/update_structure.py` 自动生成和更新。

{self.maintenance_note}

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

    def ensure_architecture_maintenance_note(self):
        """确保在《项目架构设计.md》中永久包含维护说明，并去重旧格式（新路径优先，旧路径兼容）"""
        try:
            target_doc = None
            if self.architecture_doc.exists():
                target_doc = self.architecture_doc
            elif self.architecture_doc_old.exists():
                target_doc = self.architecture_doc_old
            else:
                return
            with open(target_doc, 'r', encoding='utf-8') as f:
                content = f.read()

            # 先清理已有的维护说明（大小写不敏感），避免重复
            pattern = r"\n?维护说明：近期策略调整——已将\s+`\.venv`[^\n]*\n?"
            content_cleaned = re.sub(pattern, "\n", content, flags=re.IGNORECASE | re.MULTILINE)

            # 如果清理后依然已包含当前维护说明，则无需再次插入
            if self.maintenance_note in content_cleaned:
                new_content = content_cleaned
            else:
                insert_after = "本文档通过 `tools/update_structure.py` 自动生成和更新。"
                if insert_after in content_cleaned:
                    new_content = content_cleaned.replace(insert_after, insert_after + "\n\n" + self.maintenance_note)
                else:
                    marker = "## 📝 更新说明"
                    if marker in content_cleaned:
                        new_content = content_cleaned.replace(marker, marker + "\n\n" + self.maintenance_note)
                    else:
                        new_content = content_cleaned + "\n\n" + self.maintenance_note

            with open(target_doc, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"已在项目架构设计文档中记录维护说明：{target_doc}")
        except Exception as e:
            print(f"维护说明写入项目架构设计文档失败：{e}")
        
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
            print(f"候选目录结构清单已更新: {self.candidate_file}")
            
            # 判断是否发布为正式清单（仅允许新哨兵文件）
            env_approved = os.environ.get(self.approval_env_var, "0") in ("1", "true", "True")
            sentinel_approved = self.approval_sentinel.exists()
            should_finalize = finalize or (env_approved or sentinel_approved)
            
            archive_path_value = None
            if should_finalize:
                # 归档旧正式清单（若存在）
                self.archive_dir.mkdir(parents=True, exist_ok=True)
                # 归档旧正式清单：优先新路径，其次旧路径
                if self.formal_file.exists():
                    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                    archive_path = self.archive_dir / f"动态目录结构清单_旧版_{ts}.md"
                    try:
                        # 同时打开旧正式清单与归档文件进行内容复制
                        with open(self.formal_file, 'r', encoding='utf-8') as rf:
                            with open(archive_path, 'w', encoding='utf-8') as wf:
                                wf.write(rf.read())
                        print(f"已归档旧正式清单: {archive_path}")
                        archive_path_value = str(archive_path)
                    except Exception as ae:
                        print(f"归档失败，但继续发布: {ae}")
                elif self.formal_old.exists():
                    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                    archive_path = self.archive_dir / f"动态目录结构清单_旧版_{ts}.md"
                    try:
                        with open(self.formal_old, 'r', encoding='utf-8') as rf:
                            with open(archive_path, 'w', encoding='utf-8') as wf:
                                wf.write(rf.read())
                        print(f"已归档旧正式清单(旧路径): {archive_path}")
                        archive_path_value = str(archive_path)
                    except Exception as ae:
                        print(f"归档失败，但继续发布: {ae}")
                
                # 生成正式清单内容（无候选水印）并写入
                self.output_file = self.formal_file
                self.output_file.parent.mkdir(parents=True, exist_ok=True)
                formal_md = self.generate_structure_markdown()
                with open(self.formal_file, 'w', encoding='utf-8') as f:
                    f.write(formal_md)
                print(f"正式目录结构清单已发布: {self.formal_file}")
            else:
                print("未获批准，已生成候选清单但未更新正式清单。")
                hint = (
                    f"如需发布，请使用 --finalize 参数或设置环境变量 {self.approval_env_var}=1，"
                    f"或创建哨兵文件: {self.approval_sentinel}"
                )
                print(hint)
            
            # 确保项目架构设计文档永久包含维护说明
            self.ensure_architecture_maintenance_note()
            
            # 获取详细统计信息
            structure_items = self.scan_directory(self.project_root)
            total_items = len(structure_items)
            dir_count = len([item for item in structure_items if item.strip().endswith('/')])
            file_count = total_items - dir_count
            
            print(f"扫描完成，共处理 {total_items} 个项目")
            print(f"   目录数量: {dir_count}")
            print(f"   文件数量: {file_count}")

            # LongMemory 事件记录
            try:
                payload = {
                    'finalize': bool(should_finalize),
                    'approved_env': bool(env_approved),
                    'approved_sentinel': bool(sentinel_approved),
                    'candidate_file': str(self.candidate_file),
                    'formal_file': str(self.formal_file) if should_finalize else None,
                    'archive_file': archive_path_value,
                    'output_file': str(self.output_file),
                    'stats': {
                        'total_items': total_items,
                        'dir_count': dir_count,
                        'file_count': file_count,
                    },
                    'timestamp': datetime.now().isoformat(),
                }
                event_type = 'structure_publish' if should_finalize else 'structure_candidate_update'
                self.emit_longmemory_event(event_type, 'yds.structure', payload)
            except Exception as e:
                print(f"[LongMemory] 结构更新事件写入失败（忽略）: {e}")
            
            return True
            
        except Exception as e:
            print(f"更新失败: {e}")
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