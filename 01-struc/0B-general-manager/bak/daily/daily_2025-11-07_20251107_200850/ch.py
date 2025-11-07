#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YDS-Lab 目录结构合规性检查工具

功能：
- 增强的目录结构合规性检查
- 详细的日志记录和诊断
- 环境验证和路径处理
- 问题诊断和修复建议

适配YDS-Lab项目和AI Agent协作需求
"""

import os
import sys
import json
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Optional, Tuple
import yaml
import re

class YDSLabStructureChecker:
    """YDS-Lab目录结构合规性检查器"""
    
    def __init__(self, project_root: str = "s:/YDS-Lab", use_preview: bool = False):
        self.project_root = Path(project_root)
        # 配置文件集中至 /config，禁止回退到 /tools/structure_config.yaml
        cfg_new = self.project_root / "config" / "structure_config.yaml"
        self.config_file = cfg_new
        # 正式与候选结构清单文件（统一新路径，不再回退到 Struc/GeneralOffice）
        self.formal_file = self.project_root / "01-struc" / "0B-general-manager" / "Docs" / "YDS-AI-组织与流程" / "《动态目录结构清单》.md"
        self.candidate_file = self.project_root / "01-struc" / "0B-general-manager" / "Docs" / "YDS-AI-组织与流程" / "《动态目录结构清单（候选）》.md"
        use_candidate = use_preview or os.environ.get('YDS_USE_CANDIDATE_STRUCTURE') in ("1", "true", "True")
        self.whitelist_file = self.candidate_file if use_candidate else self.formal_file

        # 日志输出统一到新路径（必要时自动创建目录）
        logs_new = self.project_root / "01-struc" / "0B-general-manager" / "logs"
        self.log_file = logs_new / "structure_check.log"
        
        # 设置日志
        self.setup_logging()
        
        # 默认配置 - 根据《规范与流程.md》统一标准
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
                # 其他常见排除目录
                'node_modules', '.env'
            ],
            'exclude_files': [
                # 规范文档第3.3节：完全排除的文件
                '*.pyc', '*.pyo', '*.pyd',  # Python编译缓存文件
                '*.log', '*.tmp', '*.temp', # 临时和日志文件
                '.DS_Store', 'Thumbs.db',   # 系统文件
                # 额外的常见排除文件（保持兼容性）
                '*.bak', '*.swp', 'desktop.ini',
                '*.so', '*.dll'
            ],
            'special_handling': {
                # 根据规范要求的特殊目录处理
                'Log': {'max_depth': 2, 'show_files': False},  # Struc\Log目录
                'logs': {'max_depth': 2, 'show_files': False}, # 日志目录
                'archive': {'max_depth': 1, 'show_files': False} # 归档目录
            },
            'hidden_dirs_handling': {
                # 隐藏目录（以"."开头）：仅显示目录本身，不扫描内容
                'max_depth': 0, 'show_files': False
            },
            'compliance_thresholds': {
                'severe': 70,    # 低于70%为严重问题
                'minor': 95,     # 低于95%为轻微问题
                'excellent': 100 # 100%为完全合规
            },
            'naming_rules': {
                # Agents目录：禁止编号前缀（如 01-、02_）
                'agents': {
                    'path': 'Agents',
                    'forbidden_number_prefix': True,
                    'exceptions': []
                },
                # 总经办（0B-general-manager）一级子目录：必须编号前缀（如 01-市场部），含例外清单
                'general_office': {
                    'path': '01-struc/0B-general-manager',
                    'required_number_prefix': True,
                    'exceptions': ['Docs', 'logs', 'Log', 'archive', 'archives', 'bak', 'backup', 'Backups']
                }
            }
        }
        
        self.load_config()
        
        # 统计信息
        self.stats = {
            'total_items': 0,
            'compliant_items': 0,
            'missing_items': 0,
            'extra_items': 0,
            'compliance_rate': 0.0,
            'naming_violations': 0
        }
        
    def setup_logging(self):
        """设置日志系统"""
        try:
            # 确保日志目录存在
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 配置日志格式
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(self.log_file, encoding='utf-8'),
                    logging.StreamHandler(sys.stdout)
                ]
            )
            
            self.logger = logging.getLogger(__name__)
            self.logger.info("YDS-Lab结构检查器启动")
            # 预览模式提示
            if ('--preview' in sys.argv) or os.environ.get('YDS_USE_CANDIDATE_STRUCTURE') in ("1", "true", "True"):
                self.logger.info("预览模式：使用候选清单进行比对演练")
            
        except Exception as e:
            print(f"日志系统初始化失败: {e}")
            # 创建一个简单的日志记录器
            self.logger = logging.getLogger(__name__)
            
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
                self.logger.info("配置文件加载成功")
            else:
                # 创建默认配置文件
                self.save_config()
        except Exception as e:
            self.logger.error(f"配置文件加载失败，使用默认配置: {e}")
            
    def save_config(self):
        """保存配置文件"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.default_config, f, default_flow_style=False, 
                         allow_unicode=True, indent=2)
        except Exception as e:
            self.logger.error(f"配置文件保存失败: {e}")
            
    def validate_environment(self) -> bool:
        """验证运行环境"""
        self.logger.info("开始环境验证...")
        
        # 检查项目根目录
        if not self.project_root.exists():
            self.logger.error(f"项目根目录不存在: {self.project_root}")
            return False
            
        # 检查参考结构文档（正式或候选）
        if not self.whitelist_file.exists():
            self.logger.error(f"参考结构文档不存在: {self.whitelist_file}")
            self.logger.info("请先运行 update_structure.py 生成候选或正式结构清单")
            return False
            
        # 检查Python版本
        python_version = sys.version_info
        if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 7):
            self.logger.warning(f"Python版本较低: {sys.version}")
            
        self.logger.info("环境验证通过")
        return True
        
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
            
        return special.get(dir_name.lower())
        
    def scan_directory(self, path: Path, max_depth: int = None, 
                      show_files: bool = True, current_depth: int = 0, 
                      parent_special_handling: Optional[Dict] = None) -> List[str]:
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
                    sub_items = self.scan_directory(
                        entry, adjusted_max_depth, sub_show_files, current_depth + 1, 
                        effective_special
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
        
    def parse_whitelist_structure(self) -> List[str]:
        """解析标准结构文档中的目录树"""
        try:
            with open(self.whitelist_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 查找目录结构部分 - 修复正则表达式以匹配完整的代码块
            # 寻找第一个```后的内容，直到最后一个```
            start_marker = content.find('```\n')
            if start_marker == -1:
                self.logger.error("无法在标准结构文档中找到目录结构开始标记")
                return []
                
            # 从开始标记后查找结束标记
            start_pos = start_marker + 4  # 跳过'```\n'
            
            # 查找最后一个```标记（在## 维护说明之前）
            maintenance_section = content.find('## 维护说明')
            if maintenance_section != -1:
                # 在维护说明之前查找最后一个```
                end_marker = content.rfind('```', start_pos, maintenance_section)
            else:
                # 如果没有维护说明，查找最后一个```
                end_marker = content.rfind('```', start_pos)
                
            if end_marker == -1 or end_marker <= start_pos:
                self.logger.error("无法在标准结构文档中找到目录结构结束标记")
                return []
                
            # 提取结构文本
            structure_text = content[start_pos:end_marker]
            lines = structure_text.strip().split('\n')
            
            # 过滤和处理行
            structure_items = []
            backup_patterns = set()  # 用于检测重复的备份模式
            
            for line in lines:
                # 跳过空行和根目录行
                if not line.strip() or line.strip() == 'YDS-Lab/':
                    continue
                    
                # 移除行首的YDS-Lab/前缀（如果存在）
                if line.startswith('YDS-Lab/'):
                    line = line[9:]  # 移除'YDS-Lab/'
                
                # 过滤掉Markdown格式标记和无效项目
                stripped_line = line.strip()
                
                # 跳过Markdown标题（以#开头）
                if stripped_line.startswith('#'):
                    continue
                    
                # 跳过Markdown代码块标记
                if stripped_line.startswith('```') or stripped_line == '```':
                    continue
                    
                # 跳过以-开头的列表项（通常是说明文字）
                if stripped_line.startswith('- '):
                    continue
                    
                # 跳过纯数字或特殊格式的行
                if stripped_line.isdigit():
                    continue
                    
                # 跳过包含中文说明的行（通常不是目录结构）
                if any(char in stripped_line for char in ['：', '。', '，', '（', '）', '！', '？']):
                    continue
                    
                # 跳过bash命令行
                if stripped_line.startswith('cd ') or stripped_line.startswith('python '):
                    continue
                
                # 🔧 新增：过滤重复的备份目录模式（暂时禁用严格过滤）
                # if self._is_redundant_backup_path(stripped_line, backup_patterns):
                #     continue
                    
                # 只保留看起来像目录/文件路径的行
                # 有效的项目应该：不为空，不是错误标记，包含有效字符
                if (stripped_line and 
                    not stripped_line.startswith('[') and  # 不是错误标记
                    not stripped_line.startswith('目录结构扫描配置文件:') and  # 不是配置说明
                    (stripped_line.endswith('/') or  # 是目录
                     '.' in stripped_line or  # 是文件（有扩展名）
                     not any(char in stripped_line for char in [':', '`']))):  # 不包含说明性字符
                    structure_items.append(line)
                
            self.logger.info(f"从标准结构文档解析出 {len(structure_items)} 个项目（已过滤重复备份）")
            return structure_items
        
        except Exception as e:
            self.logger.error(f"解析标准结构文档失败: {e}")
            return []

    # === 命名规则校验相关 ===
    def _has_number_prefix(self, name: str) -> bool:
        """检测名称是否以编号前缀开头，例如 01-、02_、03 """
        return bool(re.match(r'^\d{2,}[-_ ]', name))

    def check_naming_rules(self) -> List[Dict[str, str]]:
        """检查 Agents 与 0B-general-manager 的命名规则，返回违规清单"""
        violations: List[Dict[str, str]] = []
        rules = self.default_config.get('naming_rules', {}) or {}

        # Agents 目录规则：禁止编号前缀
        agents_rules = rules.get('agents', {}) or {}
        agents_path = agents_rules.get('path', 'Agents')
        agents_exceptions = set(agents_rules.get('exceptions', []) or [])
        agents_dir = self.project_root / agents_path
        if agents_dir.exists() and agents_dir.is_dir():
            for child in sorted(agents_dir.iterdir(), key=lambda p: p.name.lower()):
                if child.is_dir():
                    name = child.name
                    if name in agents_exceptions:
                        continue
                    if agents_rules.get('forbidden_number_prefix', True) and self._has_number_prefix(name):
                        violations.append({
                            'path': str(child.relative_to(self.project_root)).replace('\\', '/'),
                            'issue': 'Agents目录下禁止使用编号前缀',
                            'rule': 'agents.forbidden_number_prefix'
                        })

        # 总经办（0B-general-manager）目录规则：一级子目录必须编号前缀（含例外清单）
        go_rules = rules.get('general_office', {}) or {}
        go_path = go_rules.get('path', '01-struc/0B-general-manager')
        go_exceptions = set(go_rules.get('exceptions', []) or [])
        go_dir = self.project_root / Path(go_path)
        if go_dir.exists() and go_dir.is_dir():
            for child in sorted(go_dir.iterdir(), key=lambda p: p.name.lower()):
                if child.is_dir():
                    name = child.name
                    if name in go_exceptions:
                        continue
                    # 排除隐藏与排除目录规则
                    if self.should_exclude_dir(name) or name.startswith('.'):
                        continue
                    if go_rules.get('required_number_prefix', True) and not self._has_number_prefix(name):
                        violations.append({
                            'path': str(child.relative_to(self.project_root)).replace('\\', '/'),
                            'issue': '办公室目录必须使用编号前缀（例如 01-市场部）',
                            'rule': 'general_office.required_number_prefix'
                        })

        # 统计
        self.stats['naming_violations'] = len(violations)
        return violations
    
    def _is_redundant_backup_path(self, path: str, backup_patterns: set) -> bool:
        """检测是否为重复的备份路径模式"""
        # 检测备份目录的常见模式
        backup_indicators = ['Backups/', 'backup/', 'bak/', 'daily/', 'weekly/', 'monthly/']
        
        # 如果路径包含备份指示符
        for indicator in backup_indicators:
            if indicator in path:
                # 提取备份模式（去除日期/时间戳）
                import re
                # 移除常见的时间戳模式
                pattern = re.sub(r'\d{4}-\d{2}-\d{2}', 'YYYY-MM-DD', path)
                pattern = re.sub(r'\d{2}-\d{2}-\d{4}', 'MM-DD-YYYY', pattern)
                pattern = re.sub(r'\d{8}', 'YYYYMMDD', pattern)
                pattern = re.sub(r'\d{6}', 'YYMMDD', pattern)
                pattern = re.sub(r'\d{2}:\d{2}:\d{2}', 'HH:MM:SS', pattern)
                
                # 如果这个模式已经存在，则认为是重复的
                if pattern in backup_patterns:
                    return True
                else:
                    backup_patterns.add(pattern)
                    # 如果同一个备份模式出现超过3次，后续的都视为重复
                    pattern_count = sum(1 for p in backup_patterns if p.startswith(pattern.split('/')[0]))
                    if pattern_count > 3:
                        return True
        
        return False
            
    def calculate_item_depth(self, item: str) -> int:
        """计算项目的缩进深度"""
        return (len(item) - len(item.lstrip())) // 2
        
    def extract_item_name(self, item: str) -> str:
        """提取项目名称（去除缩进和特殊标记）"""
        name = item.strip().rstrip('/')
        
        # 标准化路径：去除备份目录前缀，只保留相对于项目根目录的路径
        # 这样可以正确匹配实际文件和标准清单中的项目
        name = self._normalize_path_for_comparison(name)
        
        return name
    
    def _normalize_path_for_comparison(self, path: str) -> str:
        """标准化路径用于比较，去除备份目录前缀"""
        if not path:
            return path
            
        # 备份目录前缀模式
        backup_prefixes = [
            'Backups/daily/',
            'Backups/weekly/', 
            'Backups/monthly/',
            'Backups\\daily\\',
            'Backups\\weekly\\',
            'Backups\\monthly\\',
            'bak/',
            'backup/',
            'bak\\',
            'backup\\'
        ]
        
        # 移除备份目录前缀
        normalized = path
        for prefix in backup_prefixes:
            if normalized.startswith(prefix):
                # 移除前缀
                normalized = normalized[len(prefix):]
                # 继续处理可能的嵌套备份目录
                normalized = self._normalize_path_for_comparison(normalized)
                break
        
        # 移除日期时间戳目录（如 daily_2025-11-01_20251101_223839/）
        import re
        # 匹配日期时间戳模式
        timestamp_pattern = r'daily_\d{4}-\d{2}-\d{2}_\d{8}[/\\]'
        normalized = re.sub(timestamp_pattern, '', normalized)
        
        # 移除其他时间戳模式
        timestamp_patterns = [
            r'\d{4}-\d{2}-\d{2}[/\\]',  # YYYY-MM-DD/
            r'\d{8}[/\\]',              # YYYYMMDD/
            r'\d{6}[/\\]',              # YYMMDD/
        ]
        
        for pattern in timestamp_patterns:
            normalized = re.sub(pattern, '', normalized)
        
        # 清理多余的分隔符
        normalized = re.sub(r'[/\\]+', '/', normalized)
        normalized = normalized.strip('/')
        
        return normalized
        
    def compare_structures(self, standard_items: List[str], current_items: List[str]) -> Dict:
        """比较标准结构和当前结构"""
        self.logger.info("开始结构对比分析...")
        
        # 标准化项目名称
        standard_set = set()
        current_set = set()
        
        for item in standard_items:
            name = self.extract_item_name(item)
            if name and not name.startswith('['):  # 排除错误标记
                standard_set.add(name)
                
        for item in current_items:
            name = self.extract_item_name(item)
            if name and not name.startswith('['):  # 排除错误标记
                current_set.add(name)
        
        # 🔧 修复：仅对标准集合进行轻度过滤，保留更多数据
        # standard_set = self._filter_redundant_backups(standard_set)  # 暂时禁用过度过滤
        
        # 计算差异
        missing_items = standard_set - current_set
        extra_items = current_set - standard_set
        compliant_items = standard_set & current_set
        
        # 🔧 修复：重新设计合规性评估
        total_actual_items = len(current_set)
        total_standard_items = len(standard_set)
        
        # 更新统计信息
        self.stats['total_items'] = total_standard_items
        self.stats['actual_items'] = total_actual_items
        self.stats['compliant_items'] = len(compliant_items)
        self.stats['missing_items'] = len(missing_items)
        self.stats['extra_items'] = len(extra_items)
        
        # 🔧 新的合规性计算逻辑
        if total_standard_items > 0:
            # 基础合规率：标准项目的存在率
            base_compliance = (len(compliant_items) / total_standard_items) * 100
            
            # 结构合理性评分：考虑额外项目的影响
            if total_actual_items > 0:
                extra_ratio = len(extra_items) / total_actual_items
                # 如果额外项目过多（超过50%），降低合规性评分
                if extra_ratio > 0.5:
                    structure_penalty = (extra_ratio - 0.5) * 50  # 最多扣50分
                    structure_score = max(0, 100 - structure_penalty)
                else:
                    structure_score = 100
                
                # 综合评分：基础合规率 * 结构合理性
                self.stats['compliance_rate'] = (base_compliance * structure_score) / 100
            else:
                self.stats['compliance_rate'] = base_compliance
                
            # 记录详细评分信息
            self.stats['base_compliance'] = base_compliance
            self.stats['structure_score'] = structure_score if 'structure_score' in locals() else 100
            self.stats['extra_ratio'] = extra_ratio if 'extra_ratio' in locals() else 0
        else:
            self.stats['compliance_rate'] = 0.0
            self.stats['base_compliance'] = 0.0
            self.stats['structure_score'] = 0.0
            self.stats['extra_ratio'] = 0.0
            
        return {
            'missing': sorted(missing_items),
            'extra': sorted(extra_items),
            'compliant': sorted(compliant_items)
        }
    
    def _filter_redundant_backups(self, path_set: set) -> set:
        """过滤重复的备份路径"""
        filtered_set = set()
        backup_groups = {}
        
        for path in path_set:
            # 检测是否为备份路径
            if any(indicator in path.lower() for indicator in ['backup', 'bak', 'daily', 'weekly', 'monthly']):
                # 提取备份基础模式
                import re
                base_pattern = re.sub(r'\d{4}-\d{2}-\d{2}', '', path)
                base_pattern = re.sub(r'\d{8}', '', base_pattern)
                base_pattern = re.sub(r'\d{6}', '', base_pattern)
                base_pattern = re.sub(r'\d{2}:\d{2}:\d{2}', '', base_pattern)
                base_pattern = re.sub(r'[/_-]+', '/', base_pattern).strip('/')
                
                if base_pattern not in backup_groups:
                    backup_groups[base_pattern] = []
                backup_groups[base_pattern].append(path)
            else:
                filtered_set.add(path)
        
        # 对于每个备份组，只保留最多3个代表性路径
        for group_paths in backup_groups.values():
            if len(group_paths) <= 3:
                filtered_set.update(group_paths)
            else:
                # 保留最短的3个路径作为代表
                sorted_paths = sorted(group_paths, key=len)
                filtered_set.update(sorted_paths[:3])
        
        return filtered_set
        
    def generate_compliance_report(self, comparison_result: Dict, naming_violations: List[Dict[str, str]]) -> str:
        """生成合规性报告"""
        current_time = datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')
        
        # 确定合规等级
        compliance_rate = self.stats['compliance_rate']
        thresholds = self.default_config['compliance_thresholds']
        
        if compliance_rate >= thresholds['excellent']:
            compliance_level = "优秀 ✅"
            level_color = "🟢"
        elif compliance_rate >= thresholds['minor']:
            compliance_level = "良好 ⚠️"
            level_color = "🟡"
        elif compliance_rate >= thresholds['severe']:
            compliance_level = "需要改进 ⚠️"
            level_color = "🟠"
        else:
            compliance_level = "严重问题 ❌"
            level_color = "🔴"
            
        report = f"""
# YDS-Lab 目录结构合规性检查报告

> 检查时间: {current_time}  
> 项目根目录: `{self.project_root}`  
> 合规等级: {level_color} **{compliance_level}**

## 📊 合规性统计

| 指标 | 数量 | 百分比 | 说明 |
|------|------|--------|------|
| 标准项目总数 | {self.stats['total_items']} | 100.0% | 过滤重复备份后的标准清单 |
| 实际项目总数 | {self.stats['actual_items']} | - | 当前项目中的实际文件/目录数 |
| 合规项目数 | {self.stats['compliant_items']} | {self.stats['base_compliance']:.1f}% | 符合标准清单的项目 |
| 缺失项目数 | {self.stats['missing_items']} | {(self.stats['missing_items']/max(self.stats['total_items'],1)*100):.1f}% | 标准中有但实际缺失的项目 |
| 额外项目数 | {self.stats['extra_items']} | {(self.stats['extra_items']/max(self.stats['actual_items'],1)*100):.1f}% | 实际存在但不在标准中的项目 |

### 🎯 评分详情

- **基础合规率**: {self.stats['base_compliance']:.1f}% (标准项目存在率)
- **结构合理性**: {self.stats['structure_score']:.1f}% (额外项目影响评估)
- **额外项目比例**: {self.stats['extra_ratio']*100:.1f}% (额外项目占实际项目的比例)
- **综合合规率**: {self.stats['compliance_rate']:.1f}% (最终评分)

## 📋 详细分析

### ✅ 合规项目 ({len(comparison_result['compliant'])} 个)
"""
        
        if comparison_result['compliant']:
            for item in comparison_result['compliant'][:10]:  # 只显示前10个
                report += f"- ✅ `{item}`\n"
            if len(comparison_result['compliant']) > 10:
                report += f"- ... 还有 {len(comparison_result['compliant']) - 10} 个合规项目\n"
        else:
            report += "- 暂无合规项目\n"
            
        report += f"""
### ❌ 缺失项目 ({len(comparison_result['missing'])} 个)
"""
        
        if comparison_result['missing']:
            for item in comparison_result['missing']:
                report += f"- ❌ `{item}`\n"
        else:
            report += "- 无缺失项目 ✅\n"
            
        report += f"""
### ⚠️ 额外项目 ({len(comparison_result['extra'])} 个)
"""
        
        if comparison_result['extra']:
            # 按类型分组显示额外项目
            extra_by_type = self._categorize_extra_items(comparison_result['extra'])
            
            for category, items in extra_by_type.items():
                report += f"\n#### {category} ({len(items)} 个)\n"
                for item in items[:10]:  # 每类最多显示10个
                    report += f"- ⚠️ `{item}`\n"
                if len(items) > 10:
                    report += f"- ... 还有 {len(items) - 10} 个{category}\n"
        else:
            report += "- 无额外项目 ✅\n"
            
        # 添加修复建议
        # 命名规则检查结果
        report += f"""

## 🏷️ 命名规则检查

- 规则一（Agents）：禁止使用编号前缀（如 01-、02_）
- 规则二（总经办/0B-general-manager）：一级子目录必须使用编号前缀（例外：{', '.join(sorted(set(self.default_config.get('naming_rules', {}).get('general_office', {}).get('exceptions', []) or [])) or ['无'])}）

### 违规项（{self.stats['naming_violations']} 个）
"""

        if naming_violations:
            for v in naming_violations:
                report += f"- ❌ `{v['path']}` - {v['issue']} ({v['rule']})\n"
        else:
            report += "- ✅ 未发现命名规则违规\n"

        # 添加修复建议
        report += self.generate_fix_suggestions(comparison_result)

        return report
    
    def _categorize_extra_items(self, extra_items: list) -> dict:
        """将额外项目按类型分组"""
        categories = {
            "🗂️ 备份文件": [],
            "📝 文档文件": [],
            "🔧 配置文件": [],
            "📊 日志文件": [],
            "🎯 临时文件": [],
            "📁 其他目录": [],
            "📄 其他文件": []
        }
        
        for item in extra_items:
            item_lower = item.lower()
            if any(keyword in item_lower for keyword in ['backup', 'bak', 'old', 'copy']):
                categories["🗂️ 备份文件"].append(item)
            elif any(keyword in item_lower for keyword in ['.md', '.txt', '.doc', '.pdf', 'readme', 'doc']):
                categories["📝 文档文件"].append(item)
            elif any(keyword in item_lower for keyword in ['.yaml', '.yml', '.json', '.ini', '.cfg', 'config']):
                categories["🔧 配置文件"].append(item)
            elif any(keyword in item_lower for keyword in ['.log', 'log', 'logs']):
                categories["📊 日志文件"].append(item)
            elif any(keyword in item_lower for keyword in ['temp', 'tmp', 'cache', '.cache']):
                categories["🎯 临时文件"].append(item)
            elif item.endswith('/'):
                categories["📁 其他目录"].append(item)
            else:
                categories["📄 其他文件"].append(item)
        
        # 只返回非空的分类
        return {k: v for k, v in categories.items() if v}
        
    def generate_fix_suggestions(self, comparison_result: Dict) -> str:
        """生成修复建议"""
        suggestions = "\n## 🔧 修复建议\n\n"
        
        if comparison_result['missing']:
            suggestions += "### 创建缺失项目\n"
            suggestions += "```bash\n"
            for item in comparison_result['missing'][:10]:
                if item.endswith('/') or '.' not in item:
                    # 目录
                    suggestions += f"mkdir -p \"{self.project_root}/{item}\"\n"
                else:
                    # 文件
                    suggestions += f"touch \"{self.project_root}/{item}\"\n"
            suggestions += "```\n\n"
            
        if comparison_result['extra']:
            suggestions += "### 处理额外项目\n"
            suggestions += "请检查以下额外项目是否需要：\n"
            for item in comparison_result['extra'][:10]:
                suggestions += f"- `{item}` - 考虑移动到 `bak/` 或删除\n"
            suggestions += "\n"
            
        # 根据合规率给出总体建议
        compliance_rate = self.stats['compliance_rate']
        if compliance_rate < 70:
            suggestions += "### 🚨 紧急建议\n"
            suggestions += "- 项目结构严重不符合标准，建议立即整改\n"
            suggestions += "- 运行 `python tools/update_structure.py` 更新标准结构\n"
            suggestions += "- 考虑使用项目模板重新组织结构\n\n"
        elif compliance_rate < 95:
            suggestions += "### ⚠️ 改进建议\n"
            suggestions += "- 项目结构基本符合标准，需要小幅调整\n"
            suggestions += "- 重点关注缺失的核心目录和文件\n"
            suggestions += "- 定期运行结构检查工具\n\n"
        else:
            suggestions += "### ✅ 维护建议\n"
            suggestions += "- 项目结构良好，继续保持\n"
            suggestions += "- 建议定期检查以确保持续合规\n"
            suggestions += "- 可以考虑优化额外项目的组织\n\n"
            
        return suggestions
        
    def run_compliance_check(self) -> bool:
        """运行完整的合规性检查"""
        try:
            self.logger.info("开始YDS-Lab目录结构合规性检查")
            
            # 环境验证
            if not self.validate_environment():
                return False
                
            # 解析标准结构
            self.logger.info("解析标准目录结构...")
            standard_items = self.parse_whitelist_structure()
            if not standard_items:
                self.logger.error("无法获取标准结构，检查终止")
                return False
                
            # 扫描当前结构
            self.logger.info("扫描当前目录结构...")
            current_items = self.scan_directory(self.project_root)
            self.logger.info(f"实际扫描到 {len(current_items)} 个项目")
            
            # 结构对比
            comparison_result = self.compare_structures(standard_items, current_items)

            # 命名规则检查
            naming_violations = self.check_naming_rules()

            # 生成报告
            report = self.generate_compliance_report(comparison_result, naming_violations)
            
            # 输出报告
            print(report)
            
            # 保存报告到文件
            report_file = self.project_root / "01-struc" / "0B-general-manager" / "logs" / f"compliance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            report_file.parent.mkdir(parents=True, exist_ok=True)
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            self.logger.info(f"合规性报告已保存: {report_file}")
            
            # 记录检查结果
            self.logger.info(f"合规性检查完成 - 合规率: {self.stats['compliance_rate']:.1f}%")
            if self.stats['naming_violations']:
                self.logger.info(f"命名规则违规项: {self.stats['naming_violations']} 个")

            return True
            
        except Exception as e:
            self.logger.error(f"合规性检查失败: {e}")
            return False
            
    def get_exit_code(self) -> int:
        """根据合规率返回退出码"""
        compliance_rate = self.stats['compliance_rate']
        thresholds = self.default_config['compliance_thresholds']
        
        if compliance_rate >= thresholds['excellent']:
            return 0  # 完全合规
        elif compliance_rate >= thresholds['minor']:
            return 1  # 轻微问题
        elif compliance_rate >= thresholds['severe']:
            return 2  # 需要改进
        else:
            return 3  # 严重问题

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="YDS-Lab目录结构合规性检查工具")
    parser.add_argument('--project-root', default="s:/YDS-Lab", 
                       help='项目根目录路径')
    parser.add_argument('--preview', action='store_true',
                       help='预览模式：使用候选清单进行比对演练')
    
    args = parser.parse_args()
    
    checker = YDSLabStructureChecker(args.project_root, args.preview)
    success = checker.run_compliance_check()
    
    if success:
        exit_code = checker.get_exit_code()
        sys.exit(exit_code)
    else:
        sys.exit(4)  # 检查失败

if __name__ == "__main__":
    main()