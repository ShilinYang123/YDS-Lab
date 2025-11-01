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
    
    def __init__(self, project_root: str = "s:/YDS-Lab"):
        self.project_root = Path(project_root)
        self.config_file = self.project_root / "tools" / "structure_config.yaml"
        # 正式与候选结构清单
        self.formal_file = self.project_root / "Struc" / "GeneralOffice" / "Docs" / "YDS-AI-组织与流程" / "《动态目录结构清单》.md"
        self.candidate_file = self.project_root / "Struc" / "GeneralOffice" / "Docs" / "YDS-AI-组织与流程" / "《动态目录结构清单（候选）》.md"
        use_candidate = ('--preview' in sys.argv) or os.environ.get('YDS_USE_CANDIDATE_STRUCTURE') in ("1", "true", "True")
        self.whitelist_file = self.candidate_file if use_candidate else self.formal_file
        self.log_file = self.project_root / "Struc" / "GeneralOffice" / "logs" / "structure_check.log"
        
        # 设置日志
        self.setup_logging()
        
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
            },
            'compliance_thresholds': {
                'severe': 70,    # 低于70%为严重问题
                'minor': 95,     # 低于95%为轻微问题
                'excellent': 100 # 100%为完全合规
            }
        }
        
        self.load_config()
        
        # 统计信息
        self.stats = {
            'total_items': 0,
            'compliant_items': 0,
            'missing_items': 0,
            'extra_items': 0,
            'compliance_rate': 0.0
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
        
    def parse_whitelist_structure(self) -> List[str]:
        """解析标准结构文档中的目录树"""
        try:
            with open(self.whitelist_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 查找目录结构部分
            structure_match = re.search(r'```\s*\n(.*?)\n```', content, re.DOTALL)
            if not structure_match:
                self.logger.error("无法在标准结构文档中找到目录结构")
                return []
                
            structure_text = structure_match.group(1)
            lines = structure_text.strip().split('\n')
            
            # 过滤和处理行
            structure_items = []
            for line in lines:
                # 跳过空行和根目录行
                if not line.strip() or line.strip() == 'YDS-Lab/':
                    continue
                    
                # 移除行首的YDS-Lab/前缀（如果存在）
                if line.startswith('YDS-Lab/'):
                    line = line[9:]  # 移除'YDS-Lab/'
                    
                structure_items.append(line)
                
            self.logger.info(f"从标准结构文档解析出 {len(structure_items)} 个项目")
            return structure_items
            
        except Exception as e:
            self.logger.error(f"解析标准结构文档失败: {e}")
            return []
            
    def calculate_item_depth(self, item: str) -> int:
        """计算项目的缩进深度"""
        return (len(item) - len(item.lstrip())) // 2
        
    def extract_item_name(self, item: str) -> str:
        """提取项目名称（去除缩进和特殊标记）"""
        return item.strip().rstrip('/')
        
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
                
        # 计算差异
        missing_items = standard_set - current_set
        extra_items = current_set - standard_set
        compliant_items = standard_set & current_set
        
        # 更新统计信息
        self.stats['total_items'] = len(standard_set)
        self.stats['compliant_items'] = len(compliant_items)
        self.stats['missing_items'] = len(missing_items)
        self.stats['extra_items'] = len(extra_items)
        
        if self.stats['total_items'] > 0:
            self.stats['compliance_rate'] = (self.stats['compliant_items'] / self.stats['total_items']) * 100
        else:
            self.stats['compliance_rate'] = 0.0
            
        return {
            'missing': sorted(missing_items),
            'extra': sorted(extra_items),
            'compliant': sorted(compliant_items)
        }
        
    def generate_compliance_report(self, comparison_result: Dict) -> str:
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

| 指标 | 数量 | 百分比 |
|------|------|--------|
| 标准项目总数 | {self.stats['total_items']} | 100.0% |
| 合规项目数 | {self.stats['compliant_items']} | {self.stats['compliance_rate']:.1f}% |
| 缺失项目数 | {self.stats['missing_items']} | {(self.stats['missing_items']/max(self.stats['total_items'],1)*100):.1f}% |
| 额外项目数 | {self.stats['extra_items']} | - |

**总体合规率: {self.stats['compliance_rate']:.1f}%**

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
            for item in comparison_result['extra'][:20]:  # 只显示前20个
                report += f"- ⚠️ `{item}`\n"
            if len(comparison_result['extra']) > 20:
                report += f"- ... 还有 {len(comparison_result['extra']) - 20} 个额外项目\n"
        else:
            report += "- 无额外项目 ✅\n"
            
        # 添加修复建议
        report += self.generate_fix_suggestions(comparison_result)
        
        return report
        
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
            
            # 结构对比
            comparison_result = self.compare_structures(standard_items, current_items)
            
            # 生成报告
            report = self.generate_compliance_report(comparison_result)
            
            # 输出报告
            print(report)
            
            # 保存报告到文件
            report_file = self.project_root / "Struc" / "GeneralOffice" / "logs" / f"compliance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            report_file.parent.mkdir(parents=True, exist_ok=True)
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            self.logger.info(f"合规性报告已保存: {report_file}")
            
            # 记录检查结果
            self.logger.info(f"合规性检查完成 - 合规率: {self.stats['compliance_rate']:.1f}%")
            
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
    # 支持命令行参数指定项目根目录
    project_root = sys.argv[1] if len(sys.argv) > 1 else "s:/YDS-Lab"
    
    checker = YDSLabStructureChecker(project_root)
    success = checker.run_compliance_check()
    
    if success:
        exit_code = checker.get_exit_code()
        sys.exit(exit_code)
    else:
        sys.exit(4)  # 检查失败

if __name__ == "__main__":
    main()