#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ch.py最终修复版本 - 应用所有修复
解决路径标准化和额外项目检测问题
"""

import os
import sys
import re
import yaml
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Set, Tuple
from difflib import SequenceMatcher
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class YDSLabStructureChecker:
    """YDS-Lab目录结构合规性检查器"""
    
    def __init__(self, project_root: str = "s:/YDS-Lab"):
        self.project_root = Path(project_root)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 配置文件路径
        self.config_file = self.project_root / "config" / "structure_config.yaml"
        self.formal_structure_file = (
            self.project_root
            / "01-struc" / "docs" / "02-组织流程"
            / "《动态目录结构清单》.md"
        )
        
        # 默认配置 - 与up.py完全一致
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
        
        # 统计信息
        self.stats = {
            'total_items': 0,
            'actual_items': 0,
            'compliant_items': 0,
            'missing_items': 0,
            'extra_items': 0,
            'compliance_rate': 0.0,
            'naming_violations': 0,
            'errors': 0
        }
        
        self.load_config()
        
    def should_exclude_dir(self, dir_name: str) -> bool:
        """检查目录是否应该排除 - 与up.py完全一致"""
        exclude_dirs = self.default_config.get('exclude_dirs', [])
        return any(
            dir_name == pattern or 
            (pattern.startswith('*') and dir_name.endswith(pattern[1:])) or
            (pattern.endswith('*') and dir_name.startswith(pattern[:-1]))
            for pattern in exclude_dirs
        )
        
    def should_exclude_file(self, file_name: str) -> bool:
        """检查文件是否应该排除 - 与up.py完全一致"""
        exclude_files = self.default_config.get('exclude_files', [])
        return any(
            file_name == pattern or
            (pattern.startswith('*') and file_name.endswith(pattern[1:])) or
            (pattern.endswith('*') and file_name.startswith(pattern[:-1]))
            for pattern in exclude_files
        )
        
    def get_special_handling(self, dir_name: str) -> Optional[Dict]:
        """获取特殊目录的处理规则 - 与up.py完全一致"""
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
        except Exception as e:
            self.logger.warning(f"配置文件加载失败，使用默认配置: {e}")
    
    def scan_directory(self, path: Path, max_depth: int = None, show_files: bool = True, 
                      current_depth: int = 0, parent_special_handling: Optional[Dict] = None) -> List[str]:
        """扫描目录结构 - 与up.py完全一致"""
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
        
    def parse_whitelist_structure(self) -> List[str]:
        """解析标准结构文档 - 修复版，与up.py生成方式完全一致"""
        try:
            if not self.formal_structure_file.exists():
                self.logger.error(f"标准结构文档不存在: {self.formal_structure_file}")
                return []

            with open(self.formal_structure_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 查找包含"YDS-Lab/"的代码块，这是up.py生成的目录结构部分
            structure_matches = re.findall(r'```\s*\n(.*?)\n```', content, re.DOTALL)
            if not structure_matches:
                self.logger.error("无法在标准结构文档中找到目录结构部分")
                return []

            # 找到包含"YDS-Lab/"的代码块
            target_content = None
            for match in structure_matches:
                if 'YDS-Lab/' in match:
                    target_content = match
                    break
            
            if not target_content:
                self.logger.error("无法在标准结构文档中找到包含YDS-Lab/的代码块")
                return []

            lines = target_content.strip().split('\n')
            items: List[str] = []

            for line in lines:
                if not line.strip():
                    continue

                s = line.strip()
                
                # 修复：保留所有项目，包括根目录标记
                # 但需要处理根目录标记，使其与scan_directory返回的格式一致
                if s == 'YDS-Lab/':
                    # 跳过根目录标记，因为scan_directory不返回它
                    continue
                
                # 移除YDS-Lab/前缀（如果存在）
                if s.startswith('YDS-Lab/'):
                    s = s[len('YDS-Lab/'):]

                # 保留所有非空项目（包括文件和目录）
                # 不再跳过任何特定类型的项目，与up.py保持一致
                if s:
                    items.append(s)

            # 去重处理 - 移除重复项
            unique_items = []
            seen = set()
            for item in items:
                if item not in seen:
                    unique_items.append(item)
                    seen.add(item)
            
            self.logger.info(f"从标准结构文档解析出 {len(items)} 个项目，去重后为 {len(unique_items)} 个项目")
            return unique_items

        except Exception as e:
            self.logger.error(f"解析标准结构文档失败: {e}")
            return []
    
    def extract_item_name(self, item: str) -> str:
        """提取项目名称（去除缩进和特殊标记）- 修复版"""
        # 移除缩进
        name = item.strip()
        
        # 移除目录标记
        if name.endswith('/'):
            name = name[:-1]
            
        # 修复：不再尝试移除备份目录前缀，保持原始路径
        # 这样可以确保与标准清单中的路径格式完全一致
        
        return name
    
    def compare_structures(self, standard_items: List[str], current_items: List[str]) -> Dict[str, Any]:
        """对比标准结构与当前结构 - 修复版，与up.py统计口径一致"""
        # 标准化路径处理（与up.py一致）
        def normalize_path(path):
            # 统一使用正斜杠
            normalized = path.replace('\\', '/')
            # 移除首尾空格
            normalized = normalized.strip()
            # 移除缩进，只保留路径部分
            normalized = normalized.lstrip()
            return normalized
        
        # 标准化所有路径
        standard_set = {normalize_path(item) for item in standard_items}
        current_set = {normalize_path(item) for item in current_items}
        
        # 计算差异
        missing_items = sorted(standard_set - current_set)
        extra_items = sorted(current_set - standard_set)
        compliant_items = standard_set & current_set
        
        # 统计信息（使用去重后的集合）
        standard_dirs = len([item for item in standard_set if item.strip().endswith('/')])
        standard_files = len(standard_set) - standard_dirs
        
        current_dirs = len([item for item in current_set if item.strip().endswith('/')])
        current_files = len(current_set) - current_dirs
        
        # 计算合规率
        if len(standard_set) > 0:
            compliance_rate = (len(compliant_items) / len(standard_set)) * 100
        else:
            compliance_rate = 100.0
        
        self.logger.info(f"对比完成 - 标准集合: {len(standard_set)}, 当前集合: {len(current_set)}, "
                        f"合规: {len(compliant_items)}, 缺失: {len(missing_items)}, 额外: {len(extra_items)}")
        
        return {
            'standard_count': len(standard_set),  # 使用去重后的标准集合大小
            'current_count': len(current_set),    # 使用去重后的当前集合大小
            'missing_count': len(missing_items),
            'extra_count': len(extra_items),
            'compliant_count': len(compliant_items),  # 添加合规项目数
            'compliance_rate': compliance_rate,
            'standard_dirs': standard_dirs,
            'standard_files': standard_files,
            'current_dirs': current_dirs,
            'current_files': current_files,
            'missing_items': missing_items,
            'extra_items': extra_items
        }
    
    def cross_validate_with_filesystem(self, comparison_result: Dict) -> Dict:
        """交叉验证：对比标准清单与实际文件系统 - 修复版"""
        self.logger.info("开始交叉验证...")
        
        validation_result = {
            'false_missing': [],  # 标准清单中缺失但实际存在的项目
            'false_extra': [],    # 标记为额外但实际应该存在的项目
            'confirmed_missing': [],  # 确实缺失的项目
            'confirmed_extra': []     # 确实额外的项目
        }
        
        # 验证缺失项目
        for missing_item in comparison_result['missing_items']:
            full_path = self.project_root / missing_item
            if full_path.exists():
                validation_result['false_missing'].append(missing_item)
                self.logger.warning(f"假缺失: {missing_item} - 实际存在但未被标准清单识别")
            else:
                validation_result['confirmed_missing'].append(missing_item)
                
        # 验证额外项目
        for extra_item in comparison_result['extra_items']:
            full_path = self.project_root / extra_item
            if full_path.exists():
                # 检查是否应该被排除
                if full_path.is_dir():
                    if self.should_exclude_dir(full_path.name):
                        validation_result['confirmed_extra'].append(extra_item)
                    else:
                        validation_result['false_extra'].append(extra_item)
                        self.logger.warning(f"假额外: {extra_item} - 实际存在且不应被排除")
                else:
                    if self.should_exclude_file(full_path.name):
                        validation_result['confirmed_extra'].append(extra_item)
                    else:
                        validation_result['false_extra'].append(extra_item)
                        self.logger.warning(f"假额外: {extra_item} - 实际存在且不应被排除")
            else:
                validation_result['confirmed_extra'].append(extra_item)
        
        self.logger.info(f"交叉验证完成 - 假缺失: {len(validation_result['false_missing'])}, "
                        f"假额外: {len(validation_result['false_extra'])}")
        
        return validation_result
    
    def run_compliance_check(self) -> bool:
        """运行完整的合规性检查 - 修复版"""
        try:
            self.logger.info("开始YDS-Lab目录结构合规性检查")
            
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
            self.logger.info("对比标准结构与当前结构...")
            comparison_result = self.compare_structures(standard_items, current_items)
            
            # 更新统计信息
            self.stats = {
                'compliance_rate': comparison_result['compliance_rate'],
                'total_items': comparison_result['standard_count'],
                'actual_items': comparison_result['current_count'],
                'compliant_items': comparison_result['compliant_count'],  # 使用实际的合规项目数
                'missing_items': comparison_result['missing_count'],
                'extra_items': comparison_result['extra_count'],
                'base_compliance': comparison_result['compliance_rate'],
                'structure_score': 100.0
            }
            
            # 交叉验证
            self.logger.info("进行交叉验证...")
            validation_result = self.cross_validate_with_filesystem(comparison_result)
            
            # 生成报告
            self.logger.info("生成检查报告...")
            report = self.generate_report(comparison_result, validation_result)
            
            # 输出报告
            print(report)
            
            # 保存详细报告
            self.save_detailed_report(report, comparison_result, validation_result)
            
            # 记录LongMemory事件
            self.emit_longmemory_event('structure_check_completed', 'yds.structure', {
                'compliance_rate': self.stats['compliance_rate'],
                'total_items': self.stats['total_items'],
                'missing_items': self.stats['missing_items'],
                'extra_items': self.stats['extra_items'],
                'false_missing': len(validation_result['false_missing']),
                'false_extra': len(validation_result['false_extra']),
                'confirmed_missing': len(validation_result['confirmed_missing']),
                'confirmed_extra': len(validation_result['confirmed_extra'])
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"合规性检查失败: {e}")
            return False
    
    def generate_report(self, comparison_result: Dict, validation_result: Dict) -> str:
        """生成检查报告 - 修复版"""
        report = f"""
# YDS-Lab目录结构合规性检查报告

> 检查时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}
> 项目根目录: {self.project_root}
> 检查标准: 《01-项目架构设计.md》

## 📊 统计概览

- **合规率**: {comparison_result['compliance_rate']:.1f}% 符合《01-项目架构设计.md》规范
- **标准项目数**: {comparison_result['standard_count']} (基于《动态目录结构清单》标准)
- **实际项目数**: {comparison_result['current_count']} (当前扫描结果)
- **合规项目数**: {comparison_result['compliant_count']}
- **缺失项目数**: {comparison_result['missing_count']}
- **额外项目数**: {comparison_result['extra_count']}

## 📁 项目类型统计

### 标准结构
- **目录数量**: {comparison_result['standard_dirs']}
- **文件数量**: {comparison_result['standard_files']}

### 当前结构
- **目录数量**: {comparison_result['current_dirs']}
- **文件数量**: {comparison_result['current_files']}

## 🔍 与《动态目录结构清单》对比分析

- **清单总项目数**: {comparison_result['standard_count']} (来自up.py生成的正式清单)
- **当前扫描项目数**: {comparison_result['current_count']}
- **差距**: {comparison_result['standard_count'] - comparison_result['current_count']} 个项目
- **差距分析**: {"处理逻辑一致" if comparison_result['standard_count'] == comparison_result['current_count'] else "处理逻辑不一致，需要修正脚本"}

## 🔍 交叉验证结果

- **假缺失项目**: {len(validation_result['false_missing'])} (实际存在但未被识别)
- **假额外项目**: {len(validation_result['false_extra'])} (实际存在但被误标为额外)
- **确实缺失项目**: {len(validation_result['confirmed_missing'])}
- **确实额外项目**: {len(validation_result['confirmed_extra'])}

"""
        
        # 如果有假缺失或假额外，重点报告
        if validation_result['false_missing'] or validation_result['false_extra']:
            report += "## ⚠️ 检测算法问题\n\n"
            
            if validation_result['false_missing']:
                report += "### 假缺失项目 (检测算法需要修复)\n"
                for item in validation_result['false_missing'][:10]:
                    report += f"- ❌ `{item}` - 实际存在但未被标准清单识别\n"
                if len(validation_result['false_missing']) > 10:
                    report += f"- ... 还有 {len(validation_result['false_missing']) - 10} 个\n"
                report += "\n"
                
            if validation_result['false_extra']:
                report += "### 假额外项目 (检测算法需要修复)\n"
                for item in validation_result['false_extra'][:10]:
                    report += f"- ❌ `{item}` - 实际存在且不应被排除\n"
                if len(validation_result['false_extra']) > 10:
                    report += f"- ... 还有 {len(validation_result['false_extra']) - 10} 个\n"
                report += "\n"
        
        # 正常的缺失和额外项目
        if comparison_result['missing_items']:
            report += "### 缺失项目\n"
            for item in comparison_result['missing_items'][:10]:
                report += f"- 📋 `{item}`\n"
            if len(comparison_result['missing_items']) > 10:
                report += f"- ... 还有 {len(comparison_result['missing_items']) - 10} 个\n"
            report += "\n"
            
        if comparison_result['extra_items']:
            report += "### 额外项目\n"
            for item in comparison_result['extra_items'][:10]:
                report += f"- 📄 `{item}`\n"
            if len(comparison_result['extra_items']) > 10:
                report += f"- ... 还有 {len(comparison_result['extra_items']) - 10} 个\n"
            report += "\n"
            
        # 合规状态评估
        if comparison_result['compliance_rate'] >= 95:
            status = "✅ 优秀"
        elif comparison_result['compliance_rate'] >= 85:
            status = "⚠️ 良好"
        elif comparison_result['compliance_rate'] >= 70:
            status = "⚠️ 需要改进"
        else:
            status = "🚨 紧急需要整改"
            
        report += f"## 📈 合规状态: {status}\n\n"
        
        return report
    
    def save_detailed_report(self, report: str, comparison_result: Dict, validation_result: Dict):
        """保存详细报告"""
        try:
            # 修复：按照三级存储规范，报告应保存在rep/compliance目录
            report_dir = self.project_root / "rep" / "compliance"
            report_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_file = report_dir / f"结构合规检查报告_{timestamp}.md"
            
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
                
            # 保存详细数据
            data_file = report_dir / f"结构合规检查数据_{timestamp}.json"
            detailed_data = {
                'timestamp': datetime.now().isoformat(),
                'stats': self.stats,
                'comparison_result': comparison_result,
                'validation_result': validation_result,
                'config': self.default_config
            }
            
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(detailed_data, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"详细报告已保存: {report_file}")
            self.logger.info(f"详细数据已保存: {data_file}")
            
        except Exception as e:
            self.logger.error(f"保存详细报告失败: {e}")
    
    def emit_longmemory_event(self, event_type: str, topic: str, payload: Dict[str, Any]) -> None:
        """调用 LongMemory 事件记录工具"""
        try:
            script = self.project_root / 'tools' / 'LongMemory' / 'record_event.py'
            if not script.exists():
                self.logger.warning(f"未找到LongMemory事件记录脚本: {script}")
                return
                
            cmd = [sys.executable, str(script), '--type', event_type, '--topic', topic,
                   '--source', 'tools/ch.py', '--payload', json.dumps(payload, ensure_ascii=False)]
            subprocess.run(cmd, check=False, capture_output=True)
            self.logger.info(f"LongMemory事件已记录: {event_type}")
        except Exception as e:
            self.logger.warning(f"LongMemory事件记录失败: {e}")

def main():
    """主函数"""
    import argparse
    parser = argparse.ArgumentParser(description="YDS-Lab目录结构合规性检查工具（修复版）")
    parser.add_argument("--project-root", default="s:/YDS-Lab", help="项目根目录路径")
    parser.add_argument("--verbose", action="store_true", help="详细输出")
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    checker = YDSLabStructureChecker(args.project_root)
    success = checker.run_compliance_check()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()