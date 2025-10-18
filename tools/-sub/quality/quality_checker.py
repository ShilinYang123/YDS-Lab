#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YDS-Lab 项目质量检查工具
检查生成的文档、代码和流程图文件是否符合命名规范、目录结构要求，验证内容准确性和可读性
适配YDS-Lab项目结构和AI Agent协作需求
"""

import os
import re
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET
import json
import yaml

class ProjectQualityChecker:
    """项目质量检查器"""
    
    def __init__(self, project_root: str = None):
        """初始化检查器"""
        if project_root is None:
            self.project_root = Path(__file__).parent.parent.parent
        else:
            self.project_root = Path(project_root)
        
        # 日志目录
        self.log_dir = self.project_root / "logs"
        self.log_dir.mkdir(exist_ok=True)
        
        # 初始化报告数据
        self.report_data = {
            'check_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'project_root': str(self.project_root),
            'total_files': 0,
            'valid_files': 0,
            'invalid_files': 0,
            'naming_issues': [],
            'content_issues': [],
            'structure_issues': [],
            'file_details': [],
            'categories': {
                'documents': {'total': 0, 'valid': 0, 'issues': []},
                'code': {'total': 0, 'valid': 0, 'issues': []},
                'configs': {'total': 0, 'valid': 0, 'issues': []},
                'flowcharts': {'total': 0, 'valid': 0, 'issues': []}
            }
        }
    
    def check_file_naming(self, file_path: Path, file_type: str) -> list:
        """检查文件命名规范"""
        filename = file_path.name
        issues = []
        
        # 通用命名检查
        if ' ' in filename:
            issues.append(f"文件名包含空格: {filename}")
        
        # 检查特殊字符
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
        for char in invalid_chars:
            if char in filename:
                issues.append(f"文件名包含非法字符'{char}': {filename}")
        
        # 根据文件类型检查特定规范
        if file_type == 'flowchart':
            if not filename.endswith('.drawio'):
                issues.append(f"流程图文件扩展名不正确: {filename}")
            if "流程图" not in filename:
                issues.append(f"流程图文件名缺少'流程图'标识: {filename}")
        
        elif file_type == 'document':
            valid_extensions = ['.md', '.docx', '.pdf', '.txt']
            if not any(filename.endswith(ext) for ext in valid_extensions):
                issues.append(f"文档文件扩展名不支持: {filename}")
        
        elif file_type == 'code':
            valid_extensions = ['.py', '.js', '.json', '.yaml', '.yml', '.bat', '.ps1']
            if not any(filename.endswith(ext) for ext in valid_extensions):
                issues.append(f"代码文件扩展名不支持: {filename}")
        
        return issues
    
    def check_drawio_content(self, file_path: Path) -> list:
        """检查Draw.io文件内容"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否为有效的XML
            try:
                root = ET.fromstring(content)
            except ET.ParseError as e:
                issues.append(f"XML格式错误: {str(e)}")
                return issues
            
            # 检查是否包含mxGraphModel
            if 'mxGraphModel' not in content:
                issues.append("缺少mxGraphModel元素")
            
            # 检查是否包含基本的流程图元素
            if 'mxCell' not in content:
                issues.append("缺少mxCell元素")
            
            # 检查是否包含流程图节点
            node_count = content.count('mxCell')
            if node_count < 3:  # 至少应该有开始、处理、结束节点
                issues.append(f"流程图节点数量过少: {node_count}")
            
            # 检查是否包含连接线
            edge_count = content.count('edge="1"')
            if edge_count < 1:
                issues.append("缺少连接线")
            
        except Exception as e:
            issues.append(f"文件读取错误: {str(e)}")
        
        return issues
    
    def check_markdown_content(self, file_path: Path) -> list:
        """检查Markdown文件内容"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否有标题
            if not content.strip().startswith('#'):
                issues.append("Markdown文件缺少主标题")
            
            # 检查是否为空文件
            if len(content.strip()) < 50:
                issues.append("Markdown文件内容过少")
            
            # 检查是否有基本结构
            if '##' not in content:
                issues.append("Markdown文件缺少二级标题结构")
            
        except Exception as e:
            issues.append(f"Markdown文件读取错误: {str(e)}")
        
        return issues
    
    def check_python_content(self, file_path: Path) -> list:
        """检查Python文件内容"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查编码声明
            lines = content.split('\n')
            if len(lines) > 1:
                if 'utf-8' not in lines[0] and 'utf-8' not in lines[1]:
                    issues.append("Python文件缺少UTF-8编码声明")
            
            # 检查是否有文档字符串
            if '"""' not in content and "'''" not in content:
                issues.append("Python文件缺少文档字符串")
            
            # 检查基本语法（简单检查）
            try:
                compile(content, file_path.name, 'exec')
            except SyntaxError as e:
                issues.append(f"Python语法错误: {str(e)}")
            
        except Exception as e:
            issues.append(f"Python文件读取错误: {str(e)}")
        
        return issues
    
    def check_json_content(self, file_path: Path) -> list:
        """检查JSON文件内容"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            try:
                json.loads(content)
            except json.JSONDecodeError as e:
                issues.append(f"JSON格式错误: {str(e)}")
            
        except Exception as e:
            issues.append(f"JSON文件读取错误: {str(e)}")
        
        return issues
    
    def check_yaml_content(self, file_path: Path) -> list:
        """检查YAML文件内容"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            try:
                yaml.safe_load(content)
            except yaml.YAMLError as e:
                issues.append(f"YAML格式错误: {str(e)}")
            
        except Exception as e:
            issues.append(f"YAML文件读取错误: {str(e)}")
        
        return issues
    
    def determine_file_type(self, file_path: Path) -> str:
        """确定文件类型"""
        suffix = file_path.suffix.lower()
        
        if suffix == '.drawio':
            return 'flowchart'
        elif suffix in ['.md', '.docx', '.pdf', '.txt']:
            return 'document'
        elif suffix in ['.py', '.js', '.bat', '.ps1']:
            return 'code'
        elif suffix in ['.json', '.yaml', '.yml']:
            return 'config'
        else:
            return 'other'
    
    def check_single_file(self, file_path: Path) -> dict:
        """检查单个文件"""
        file_type = self.determine_file_type(file_path)
        
        file_info = {
            'filename': file_path.name,
            'path': str(file_path.relative_to(self.project_root)),
            'type': file_type,
            'size': file_path.stat().st_size if file_path.exists() else 0,
            'naming_issues': [],
            'content_issues': [],
            'is_valid': True
        }
        
        # 检查文件是否存在
        if not file_path.exists():
            file_info['content_issues'].append("文件不存在")
            file_info['is_valid'] = False
            return file_info
        
        # 检查文件大小
        if file_info['size'] == 0:
            file_info['content_issues'].append("文件为空")
            file_info['is_valid'] = False
        
        # 检查命名规范
        naming_issues = self.check_file_naming(file_path, file_type)
        file_info['naming_issues'] = naming_issues
        if naming_issues:
            file_info['is_valid'] = False
        
        # 根据文件类型检查内容
        content_issues = []
        if file_type == 'flowchart':
            content_issues = self.check_drawio_content(file_path)
        elif file_type == 'document' and file_path.suffix == '.md':
            content_issues = self.check_markdown_content(file_path)
        elif file_type == 'code' and file_path.suffix == '.py':
            content_issues = self.check_python_content(file_path)
        elif file_type == 'config' and file_path.suffix == '.json':
            content_issues = self.check_json_content(file_path)
        elif file_type == 'config' and file_path.suffix in ['.yaml', '.yml']:
            content_issues = self.check_yaml_content(file_path)
        
        file_info['content_issues'].extend(content_issues)
        if content_issues:
            file_info['is_valid'] = False
        
        return file_info
    
    def scan_project_files(self) -> list:
        """扫描项目文件"""
        files_to_check = []
        
        # 扫描主要目录
        scan_dirs = [
            self.project_root / "Docs",
            self.project_root / "tools",
            self.project_root / "ai",
            self.project_root / "projects"
        ]
        
        # 扫描文件类型
        file_patterns = [
            "**/*.md", "**/*.py", "**/*.js", "**/*.json", 
            "**/*.yaml", "**/*.yml", "**/*.drawio", "**/*.bat", "**/*.ps1"
        ]
        
        for scan_dir in scan_dirs:
            if scan_dir.exists():
                for pattern in file_patterns:
                    files_to_check.extend(scan_dir.glob(pattern))
        
        # 去重并排序
        return sorted(list(set(files_to_check)))
    
    def run_quality_check(self) -> dict:
        """运行质量检查"""
        print(f"开始项目质量检查: {self.project_root}")
        
        # 扫描文件
        files_to_check = self.scan_project_files()
        self.report_data['total_files'] = len(files_to_check)
        
        print(f"找到 {len(files_to_check)} 个文件需要检查")
        
        # 检查每个文件
        for i, file_path in enumerate(files_to_check, 1):
            print(f"[{i}/{len(files_to_check)}] 检查: {file_path.relative_to(self.project_root)}")
            
            file_info = self.check_single_file(file_path)
            self.report_data['file_details'].append(file_info)
            
            # 更新分类统计
            file_type = file_info['type']
            if file_type in self.report_data['categories']:
                self.report_data['categories'][file_type]['total'] += 1
                if file_info['is_valid']:
                    self.report_data['categories'][file_type]['valid'] += 1
                else:
                    self.report_data['categories'][file_type]['issues'].extend(
                        file_info['naming_issues'] + file_info['content_issues']
                    )
            
            # 更新总体统计
            if file_info['is_valid']:
                self.report_data['valid_files'] += 1
                print(f"  ✅ 通过")
            else:
                self.report_data['invalid_files'] += 1
                print(f"  ❌ 发现问题:")
                for issue in file_info['naming_issues'] + file_info['content_issues']:
                    print(f"    - {issue}")
                    if '命名' in issue or '文件名' in issue:
                        if issue not in self.report_data['naming_issues']:
                            self.report_data['naming_issues'].append(issue)
                    else:
                        if issue not in self.report_data['content_issues']:
                            self.report_data['content_issues'].append(issue)
        
        return self.report_data
    
    def generate_quality_report(self) -> Path:
        """生成质量检查报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.log_dir / f"quality_check_report_{timestamp}.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# YDS-Lab 项目质量检查报告\n\n")
            f.write(f"检查时间: {self.report_data['check_time']}\n")
            f.write(f"项目根目录: {self.report_data['project_root']}\n\n")
            
            # 总体统计
            f.write("## 检查统计\n\n")
            f.write(f"- **总文件数**: {self.report_data['total_files']}\n")
            f.write(f"- **通过检查**: {self.report_data['valid_files']}\n")
            f.write(f"- **存在问题**: {self.report_data['invalid_files']}\n")
            if self.report_data['total_files'] > 0:
                pass_rate = (self.report_data['valid_files']/self.report_data['total_files']*100)
                f.write(f"- **通过率**: {pass_rate:.1f}%\n\n")
            
            # 分类统计
            f.write("## 分类统计\n\n")
            for category, stats in self.report_data['categories'].items():
                if stats['total'] > 0:
                    category_names = {
                        'documents': '文档文件',
                        'code': '代码文件', 
                        'configs': '配置文件',
                        'flowcharts': '流程图文件'
                    }
                    f.write(f"### {category_names.get(category, category)}\n")
                    f.write(f"- 总数: {stats['total']}\n")
                    f.write(f"- 通过: {stats['valid']}\n")
                    f.write(f"- 问题: {stats['total'] - stats['valid']}\n\n")
            
            # 问题汇总
            if self.report_data['naming_issues'] or self.report_data['content_issues']:
                f.write("## 问题汇总\n\n")
                
                if self.report_data['naming_issues']:
                    f.write("### 命名规范问题\n\n")
                    for issue in set(self.report_data['naming_issues']):
                        f.write(f"- {issue}\n")
                    f.write("\n")
                
                if self.report_data['content_issues']:
                    f.write("### 内容质量问题\n\n")
                    for issue in set(self.report_data['content_issues']):
                        f.write(f"- {issue}\n")
                    f.write("\n")
            
            # 详细检查结果
            f.write("## 详细检查结果\n\n")
            f.write("| 序号 | 文件路径 | 类型 | 状态 | 文件大小 | 问题描述 |\n")
            f.write("|------|----------|------|------|----------|----------|\n")
            
            for i, file_info in enumerate(self.report_data['file_details'], 1):
                status = "✅ 通过" if file_info['is_valid'] else "❌ 问题"
                size_kb = f"{file_info['size']/1024:.1f}KB" if file_info['size'] > 0 else "0KB"
                issues = file_info['naming_issues'] + file_info['content_issues']
                issue_text = "; ".join(issues) if issues else "无"
                
                f.write(f"| {i} | {file_info['path']} | {file_info['type']} | {status} | {size_kb} | {issue_text} |\n")
            
            f.write("\n## 建议\n\n")
            if self.report_data['invalid_files'] == 0:
                f.write("🎉 所有文件均通过质量检查，符合规范要求。\n")
            else:
                f.write("请根据上述问题描述修复相关文件，确保所有文件符合质量标准。\n")
                f.write("\n### 修复建议\n\n")
                f.write("1. **命名规范**: 确保文件名不包含空格和特殊字符\n")
                f.write("2. **内容完整**: 检查文件内容是否完整和有效\n")
                f.write("3. **格式正确**: 确保JSON、YAML等配置文件格式正确\n")
                f.write("4. **编码规范**: Python文件应包含UTF-8编码声明\n")
        
        print(f"\n📊 质量检查报告已生成: {report_path}")
        return report_path

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='YDS-Lab 项目质量检查工具')
    parser.add_argument('--project-root', help='指定项目根目录路径')
    args = parser.parse_args()
    
    checker = ProjectQualityChecker(args.project_root)
    report_data = checker.run_quality_check()
    report_path = checker.generate_quality_report()
    
    print(f"\n=== 质量检查完成 ===")
    print(f"🔍 项目目录: {checker.project_root}")
    print(f"📊 总文件数: {report_data['total_files']}")
    print(f"✅ 通过检查: {report_data['valid_files']}")
    print(f"❌ 存在问题: {report_data['invalid_files']}")
    if report_data['total_files'] > 0:
        pass_rate = (report_data['valid_files']/report_data['total_files']*100)
        print(f"📈 通过率: {pass_rate:.1f}%")
    print(f"📋 详细报告: {report_path}")
    
    return report_data

if __name__ == "__main__":
    main()