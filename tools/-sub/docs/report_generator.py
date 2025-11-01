#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YDS-Lab 报告生成器模块
提供统一的报告生成功能，支持多种格式输出
适配YDS-Lab项目结构和AI Agent协作需求
"""

import sys
from pathlib import Path
from typing import Set, List, Optional, Dict, Any
from datetime import datetime
import json
import yaml

class YDSReportGenerator:
    """YDS-Lab 报告生成器类"""

    def __init__(self, project_root: str = None):
        """初始化报告生成器"""
        if project_root is None:
            self.project_root = Path(__file__).parent.parent.parent
        else:
            self.project_root = Path(project_root)
        
        # 配置默认值
        self.config = {
            'timestamp_format': '%Y-%m-%d %H:%M:%S',
            'tree_root_name': 'YDS-Lab/',
            'max_tree_depth': 3,
            'output_dir': self.project_root / "logs" / "reports"
        }
        
        # 确保输出目录存在
        self.config['output_dir'].mkdir(parents=True, exist_ok=True)

    def load_project_config(self) -> Dict[str, Any]:
        """加载项目配置"""
        config_file = self.project_root / "project_config.yaml"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                print(f"⚠️ 配置文件加载失败: {e}")
        return {}

    def generate_directory_tree(self, paths: Set[str], max_depth: int = None) -> str:
        """生成目录树结构"""
        if not paths:
            return "(空目录)"

        if max_depth is None:
            max_depth = self.config['max_tree_depth']

        # 将路径转换为Path对象并排序
        path_objects = [Path(p) for p in paths]
        path_objects.sort()

        # 构建树结构
        tree_lines = []
        processed_dirs = set()

        for path_obj in path_objects:
            # 获取相对于项目根目录的路径
            try:
                rel_path = path_obj.relative_to(self.project_root)
            except ValueError:
                rel_path = path_obj

            parts = rel_path.parts
            if len(parts) > max_depth:
                continue

            # 构建每一级的缩进
            for i, part in enumerate(parts):
                current_path = Path(*parts[:i + 1])
                if current_path not in processed_dirs:
                    indent = "│   " * i
                    if i == len(parts) - 1:
                        # 最后一级，判断是文件还是目录
                        if path_obj.is_dir():
                            tree_lines.append(f"{indent}├── {part}/")
                        else:
                            tree_lines.append(f"{indent}├── {part}")
                    else:
                        tree_lines.append(f"{indent}├── {part}/")
                    processed_dirs.add(current_path)

        return "\n".join(tree_lines)

    def format_file_list(self, files: List[Path], title: str = "文件列表", 
                        show_size: bool = False, show_modified: bool = False) -> str:
        """格式化文件列表"""
        if not files:
            return f"## {title}\n\n(无文件)\n\n"

        content = f"## {title}\n\n"
        
        if show_size or show_modified:
            content += "| 文件路径 |"
            if show_size:
                content += " 大小 |"
            if show_modified:
                content += " 修改时间 |"
            content += "\n|----------|"
            if show_size:
                content += "------|"
            if show_modified:
                content += "------------|"
            content += "\n"
            
            for file_path in sorted(files):
                try:
                    rel_path = file_path.relative_to(self.project_root)
                    content += f"| {rel_path} |"
                    
                    if show_size and file_path.exists():
                        size = file_path.stat().st_size
                        if size > 1024 * 1024:
                            size_str = f"{size / (1024 * 1024):.1f}MB"
                        elif size > 1024:
                            size_str = f"{size / 1024:.1f}KB"
                        else:
                            size_str = f"{size}B"
                        content += f" {size_str} |"
                    elif show_size:
                        content += " - |"
                    
                    if show_modified and file_path.exists():
                        mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        content += f" {mtime.strftime('%Y-%m-%d %H:%M')} |"
                    elif show_modified:
                        content += " - |"
                    
                    content += "\n"
                except ValueError:
                    content += f"| {file_path} |"
                    if show_size:
                        content += " - |"
                    if show_modified:
                        content += " - |"
                    content += "\n"
        else:
            for file_path in sorted(files):
                try:
                    rel_path = file_path.relative_to(self.project_root)
                    content += f"- {rel_path}\n"
                except ValueError:
                    content += f"- {file_path}\n"

        return content + "\n"

    def format_directory_list(self, directories: List[Path], title: str = "目录列表") -> str:
        """格式化目录列表"""
        if not directories:
            return f"## {title}\n\n(无目录)\n\n"

        content = f"## {title}\n\n"
        for dir_path in sorted(directories):
            try:
                rel_path = dir_path.relative_to(self.project_root)
                content += f"- {rel_path}/\n"
            except ValueError:
                content += f"- {dir_path}/\n"

        return content + "\n"

    def generate_statistics_section(self, stats: Dict[str, Any]) -> str:
        """生成统计信息部分"""
        content = "## 统计信息\n\n"
        
        for key, value in stats.items():
            if isinstance(value, dict):
                content += f"### {key}\n\n"
                for sub_key, sub_value in value.items():
                    content += f"- **{sub_key}**: {sub_value}\n"
                content += "\n"
            else:
                content += f"- **{key}**: {value}\n"
        
        return content + "\n"

    def generate_issues_section(self, issues: List[Dict[str, Any]], title: str = "问题列表") -> str:
        """生成问题列表部分"""
        if not issues:
            return f"## {title}\n\n✅ 未发现问题\n\n"

        content = f"## {title}\n\n"
        
        for i, issue in enumerate(issues, 1):
            severity = issue.get('severity', 'info')
            severity_icon = {
                'error': '🔴',
                'warning': '🟡', 
                'info': '🔵'
            }.get(severity, '🔵')
            
            content += f"{i}. {severity_icon} **{issue.get('title', '未知问题')}**\n"
            if 'description' in issue:
                content += f"   - 描述: {issue['description']}\n"
            if 'file' in issue:
                content += f"   - 文件: {issue['file']}\n"
            if 'line' in issue:
                content += f"   - 行号: {issue['line']}\n"
            if 'suggestion' in issue:
                content += f"   - 建议: {issue['suggestion']}\n"
            content += "\n"
        
        return content

    def save_report(self, content: str, filename: str, 
                   output_dir: Path = None, message: str = "报告已保存") -> Path:
        """保存报告到文件"""
        if output_dir is None:
            output_dir = self.config['output_dir']
        
        output_file = output_dir / filename
        
        try:
            # 确保输出目录存在
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # 写入文件
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)

            self.print_file_link(message, output_file)
            return output_file

        except Exception as e:
            print(f"❌ 保存报告失败: {e}")
            raise

    def save_json_report(self, data: Dict[str, Any], filename: str,
                        output_dir: Path = None) -> Path:
        """保存JSON格式报告"""
        if output_dir is None:
            output_dir = self.config['output_dir']
        
        output_file = output_dir / filename
        
        try:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.print_file_link("JSON报告已保存", output_file)
            return output_file
            
        except Exception as e:
            print(f"❌ 保存JSON报告失败: {e}")
            raise

    def print_file_link(self, message: str, file_path: Path) -> None:
        """打印可点击的文件链接"""
        # 将Windows路径转换为URL格式
        file_url = f"file:///{str(file_path).replace(chr(92), '/')}"
        print(f"{message}:")
        print(f"  📄 {file_url}")

    def generate_standard_report_header(self, tool_name: str,
                                      directories_count: int = 0,
                                      files_count: int = 0,
                                      template_files_count: int = 0,
                                      additional_info: Dict[str, Any] = None) -> str:
        """生成标准报告头部"""
        timestamp = datetime.now().strftime(self.config['timestamp_format'])

        header = (
            f"# YDS-Lab 项目报告\n\n"
            f"> 生成时间: {timestamp}\n"
            f"> 生成工具: {tool_name}\n"
            f"> 项目根目录: {self.project_root}\n"
        )

        if directories_count > 0:
            header += f"> 目录数量: {directories_count}\n"
        if files_count > 0:
            header += f"> 文件数量: {files_count}\n"
        if template_files_count > 0:
            header += f"> 模板文件: {template_files_count}\n"

        if additional_info:
            for key, value in additional_info.items():
                header += f"> {key}: {value}\n"

        header += "\n---\n\n"
        return header

    def generate_directory_section(self, paths: Set[str], title: str = "目录结构") -> str:
        """生成目录结构部分"""
        tree_content = self.generate_directory_tree(paths)

        return (
            f"## {title}\n\n"
            f"```\n"
            f"{self.config['tree_root_name']}\n"
            f"{tree_content}\n"
            f"```\n\n"
        )

    def generate_summary_section(self, summary_data: Dict[str, Any]) -> str:
        """生成摘要部分"""
        content = "## 摘要\n\n"
        
        # 总体状态
        if 'status' in summary_data:
            status_icon = {
                'success': '✅',
                'warning': '⚠️',
                'error': '❌',
                'info': 'ℹ️'
            }.get(summary_data['status'], 'ℹ️')
            content += f"{status_icon} **状态**: {summary_data.get('status_text', '未知')}\n\n"
        
        # 关键指标
        if 'metrics' in summary_data:
            content += "### 关键指标\n\n"
            for metric, value in summary_data['metrics'].items():
                content += f"- **{metric}**: {value}\n"
            content += "\n"
        
        # 主要发现
        if 'findings' in summary_data:
            content += "### 主要发现\n\n"
            for finding in summary_data['findings']:
                content += f"- {finding}\n"
            content += "\n"
        
        # 建议
        if 'recommendations' in summary_data:
            content += "### 建议\n\n"
            for i, recommendation in enumerate(summary_data['recommendations'], 1):
                content += f"{i}. {recommendation}\n"
            content += "\n"
        
        return content

    def create_comprehensive_report(self, report_data: Dict[str, Any], 
                                  report_name: str = "comprehensive_report") -> Path:
        """创建综合报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{report_name}_{timestamp}.md"
        
        # 构建报告内容
        content = self.generate_standard_report_header(
            tool_name=report_data.get('tool_name', 'YDS-Lab Report Generator'),
            directories_count=report_data.get('directories_count', 0),
            files_count=report_data.get('files_count', 0),
            additional_info=report_data.get('additional_info', {})
        )
        
        # 添加摘要
        if 'summary' in report_data:
            content += self.generate_summary_section(report_data['summary'])
        
        # 添加统计信息
        if 'statistics' in report_data:
            content += self.generate_statistics_section(report_data['statistics'])
        
        # 添加目录结构
        if 'directory_paths' in report_data:
            content += self.generate_directory_section(report_data['directory_paths'])
        
        # 添加文件列表
        if 'files' in report_data:
            content += self.format_file_list(
                report_data['files'], 
                title=report_data.get('files_title', '文件列表'),
                show_size=report_data.get('show_file_size', False),
                show_modified=report_data.get('show_file_modified', False)
            )
        
        # 添加问题列表
        if 'issues' in report_data:
            content += self.generate_issues_section(
                report_data['issues'],
                title=report_data.get('issues_title', '问题列表')
            )
        
        # 添加自定义部分
        if 'custom_sections' in report_data:
            for section in report_data['custom_sections']:
                content += f"## {section['title']}\n\n{section['content']}\n\n"
        
        # 保存报告
        return self.save_report(content, filename)

def main():
    """主函数 - 演示用法"""
    generator = YDSReportGenerator()
    
    # 示例报告数据
    sample_data = {
        'tool_name': 'YDS-Lab Report Generator Demo',
        'files_count': 10,
        'directories_count': 5,
        'summary': {
            'status': 'success',
            'status_text': '报告生成成功',
            'metrics': {
                '总文件数': 10,
                '总目录数': 5,
                '检查通过率': '95%'
            },
            'findings': [
                '项目结构符合规范',
                '代码质量良好',
                '文档完整性较高'
            ],
            'recommendations': [
                '建议定期更新文档',
                '建议增加单元测试覆盖率'
            ]
        },
        'statistics': {
            '文件类型分布': {
                'Python文件': 6,
                'Markdown文件': 3,
                '配置文件': 1
            }
        }
    }
    
    # 生成示例报告
    report_path = generator.create_comprehensive_report(sample_data, "demo_report")
    print(f"✅ 示例报告已生成: {report_path}")

if __name__ == "__main__":
    main()