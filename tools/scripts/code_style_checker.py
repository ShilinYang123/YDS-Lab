#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YDS-Lab 代码规范检查器
用于自动化检查Python代码规范，确保代码质量
"""

import ast
import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional


class CodeStyleChecker:
    """代码规范检查器"""
    
    def __init__(self, project_root: Optional[Path] = None):
        """初始化检查器
        
        Args:
            project_root: 项目根目录，如果为None则自动检测
        """
        self.project_root = project_root or self._find_project_root()
        self.reports: List[Dict[str, Any]] = []
        
    def _find_project_root(self) -> Path:
        """自动查找项目根目录"""
        current = Path.cwd()
        for parent in [current] + list(current.parents):
            if (parent / 'ch.py').exists() or (parent / '01-struc').exists():
                return parent
        return current
        
    def find_python_files(self, path: Optional[Path] = None) -> List[Path]:
        """查找Python文件
        
        Args:
            path: 要检查的路径，如果为None则检查整个项目
            
        Returns:
            Python文件路径列表
        """
        search_path = path or self.project_root
        python_files = []
        
        for py_file in search_path.rglob('*.py'):
            # 排除虚拟环境和缓存目录
            if any(excluded in str(py_file) for excluded in ['__pycache__', '.venv', 'venv', '.git']):
                continue
            python_files.append(py_file)
            
        return sorted(python_files)
        
    def check_pep8_compliance(self, file_path: Path) -> List[Dict[str, Any]]:
        """检查PEP8规范"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            for i, line in enumerate(lines, 1):
                # 检查行长度
                if len(line.rstrip()) > 120:
                    issues.append({
                        'line': i,
                        'column': 121,
                        'type': 'style',
                        'severity': 'warning',
                        'message': f'行长度超过120字符: {len(line.rstrip())}'
                    })
                    
                # 检查制表符
                if '\t' in line:
                    issues.append({
                        'line': i,
                        'column': line.index('\t') + 1,
                        'type': 'style',
                        'severity': 'warning',
                        'message': '使用了制表符，应使用4个空格'
                    })
                    
                # 检查行尾空格
                if line.rstrip() != line.rstrip('\n').rstrip('\r'):
                    issues.append({
                        'line': i,
                        'column': len(line.rstrip()),
                        'type': 'style',
                        'severity': 'info',
                        'message': '行尾有多余空格'
                    })
                    
        except Exception as e:
            issues.append({
                'line': 0,
                'column': 0,
                'type': 'error',
                'severity': 'error',
                'message': f'读取文件失败: {e}'
            })
            
        return issues
        
    def check_naming_conventions(self, file_path: Path) -> List[Dict[str, Any]]:
        """检查命名规范"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 简单的正则表达式检查
            # 检查函数名是否使用snake_case
            function_pattern = r'def\s+([A-Z][a-zA-Z0-9_]*)\s*\('
            for match in re.finditer(function_pattern, content):
                func_name = match.group(1)
                issues.append({
                    'line': content[:match.start()].count('\n') + 1,
                    'column': match.start() - content.rfind('\n', 0, match.start()),
                    'type': 'naming',
                    'severity': 'warning',
                    'message': f'函数名应使用snake_case: {func_name}'
                })
                
            # 检查类名是否使用PascalCase
            class_pattern = r'class\s+([a-z][a-zA-Z0-9_]*)\s*[\(:]'
            for match in re.finditer(class_pattern, content):
                class_name = match.group(1)
                issues.append({
                    'line': content[:match.start()].count('\n') + 1,
                    'column': match.start() - content.rfind('\n', 0, match.start()),
                    'type': 'naming',
                    'severity': 'warning',
                    'message': f'类名应使用PascalCase: {class_name}'
                })
                
        except Exception as e:
            issues.append({
                'line': 0,
                'column': 0,
                'type': 'error',
                'severity': 'error',
                'message': f'检查命名规范失败: {e}'
            })
            
        return issues
        
    def check_docstrings(self, file_path: Path) -> List[Dict[str, Any]]:
        """检查文档字符串"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    # 检查是否有文档字符串
                    if not ast.get_docstring(node):
                        issues.append({
                            'line': node.lineno,
                            'column': 0,
                            'type': 'documentation',
                            'severity': 'info',
                            'message': f'{"函数" if isinstance(node, ast.FunctionDef) else "类"}缺少文档字符串: {node.name}'
                        })
                        
        except SyntaxError as e:
            issues.append({
                'line': e.lineno or 0,
                'column': e.offset or 0,
                'type': 'error',
                'severity': 'error',
                'message': f'语法错误: {e}'
            })
        except Exception as e:
            issues.append({
                'line': 0,
                'column': 0,
                'type': 'error',
                'severity': 'error',
                'message': f'检查文档字符串失败: {e}'
            })
            
        return issues
        
    def check_file(self, file_path: Path) -> Dict[str, Any]:
        """检查单个文件"""
        try:
            relative_path = file_path.relative_to(self.project_root)
        except ValueError:
            # 如果文件不在项目根目录下，使用绝对路径
            relative_path = file_path
        
        print(f"正在检查: {relative_path}")
        
        # 运行所有检查
        pep8_issues = self.check_pep8_compliance(file_path)
        naming_issues = self.check_naming_conventions(file_path)
        doc_issues = self.check_docstrings(file_path)
        
        all_issues = pep8_issues + naming_issues + doc_issues
        
        # 统计
        stats = {
            'total': len(all_issues),
            'error': len([i for i in all_issues if i['severity'] == 'error']),
            'warning': len([i for i in all_issues if i['severity'] == 'warning']),
            'info': len([i for i in all_issues if i['severity'] == 'info'])
        }
        
        report = {
            'file': str(relative_path),
            'issues': all_issues,
            'stats': stats,
            'status': 'error' if stats['error'] > 0 else 'warning' if stats['warning'] > 0 else 'pass'
        }
        
        return report
        
    def run_checks(self, path: Optional[Path] = None) -> Dict[str, Any]:
        """运行代码规范检查"""
        python_files = self.find_python_files(path)
        
        if not python_files:
            return {
                'summary': {
                    'total_files': 0,
                    'total_issues': 0,
                    'status': 'pass'
                },
                'files': []
            }
            
        print(f"找到 {len(python_files)} 个Python文件，开始检查...")
        
        file_reports = []
        total_issues = 0
        
        for py_file in python_files:
            try:
                report = self.check_file(py_file)
                file_reports.append(report)
                total_issues += report['stats']['total']
            except Exception as e:
                print(f"检查文件失败 {py_file}: {e}")
                file_reports.append({
                    'file': str(py_file.relative_to(self.project_root)),
                    'issues': [{
                        'line': 0,
                        'column': 0,
                        'type': 'error',
                        'severity': 'error',
                        'message': f'检查失败: {e}'
                    }],
                    'stats': {'total': 1, 'error': 1, 'warning': 0, 'info': 0},
                    'status': 'error'
                })
                total_issues += 1
                
        # 总体状态
        has_errors = any(r['status'] == 'error' for r in file_reports)
        has_warnings = any(r['status'] == 'warning' for r in file_reports)
        
        summary = {
            'total_files': len(python_files),
            'total_issues': total_issues,
            'status': 'error' if has_errors else 'warning' if has_warnings else 'pass',
            'error_files': len([r for r in file_reports if r['status'] == 'error']),
            'warning_files': len([r for r in file_reports if r['status'] == 'warning']),
            'pass_files': len([r for r in file_reports if r['status'] == 'pass'])
        }
        
        result = {
            'summary': summary,
            'files': file_reports
        }
        
        self.reports = file_reports
        return result
        
    def print_summary(self, result: Dict[str, Any]):
        """打印检查摘要"""
        summary = result['summary']
        
        print("\n" + "="*60)
        print("代码规范检查报告")
        print("="*60)
        
        status_color = {
            'pass': '\033[92m',    # 绿色
            'warning': '\033[93m',  # 黄色
            'error': '\033[91m'     # 红色
        }
        
        reset_color = '\033[0m'
        
        status_text = {
            'pass': '通过',
            'warning': '警告',
            'error': '错误'
        }
        
        # 总体状态
        color = status_color.get(summary['status'], '')
        status = status_text.get(summary['status'], summary['status'])
        
        print(f"总体状态: {color}{status}{reset_color}")
        print(f"检查文件: {summary['total_files']} 个")
        print(f"发现问题: {summary['total_issues']} 个")
        print(f"错误文件: {summary['error_files']} 个")
        print(f"警告文件: {summary['warning_files']} 个")
        print(f"通过文件: {summary['pass_files']} 个")
        
        # 显示有问题的文件
        if result['files']:
            error_files = [f for f in result['files'] if f['status'] != 'pass']
            if error_files:
                print(f"\n需要关注的文件 ({len(error_files)} 个):")
                for file_report in error_files[:10]:  # 最多显示10个
                    file_color = status_color.get(file_report['status'], '')
                    file_status = status_text.get(file_report['status'], file_report['status'])
                    print(f"  {file_color}{file_report['file']}{reset_color} ({file_report['stats']['total']} 个问题)")
                    
                    # 显示前3个问题
                    for issue in file_report['issues'][:3]:
                        severity_color = '\033[91m' if issue['severity'] == 'error' else '\033[93m'
                        print(f"    {severity_color}{issue['severity']}{reset_color}: 第{issue['line']}行 - {issue['message']}")
                        
                    if len(file_report['issues']) > 3:
                        print(f"    ... 还有 {len(file_report['issues']) - 3} 个问题")
                        
        print("\n" + "="*60)
        
    def save_report(self, result: Dict[str, Any], output_path: Path):
        """保存检查报告"""
        import json
        
        # 转换为可序列化格式
        serializable_result = {
            'summary': result['summary'],
            'files': []
        }
        
        for file_report in result['files']:
            serializable_file = {
                'file': file_report['file'],
                'status': file_report['status'],
                'stats': file_report['stats'],
                'issues': file_report['issues']
            }
            serializable_result['files'].append(serializable_file)
            
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_result, f, ensure_ascii=False, indent=2)
            
        print(f"报告已保存到: {output_path}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='YDS-Lab 代码规范检查器')
    parser.add_argument('--path', type=str, help='要检查的目录或文件')
    parser.add_argument('--output', type=str, help='输出报告文件路径')
    parser.add_argument('--verbose', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    # 创建检查器
    checker = CodeStyleChecker()
    
    # 确定检查路径
    check_path = None
    if args.path:
        check_path = Path(args.path)
        if not check_path.exists():
            print(f"错误: 路径不存在: {args.path}")
            sys.exit(1)
            
    # 运行检查
    try:
        result = checker.run_checks(check_path)
        
        # 打印摘要
        checker.print_summary(result)
        
        # 保存报告
        if args.output:
            output_path = Path(args.output)
            checker.save_report(result, output_path)
        
        # 根据检查结果退出
        if result['summary']['status'] == 'error':
            sys.exit(1)
        elif result['summary']['status'] == 'warning':
            sys.exit(2)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n检查被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"检查过程出错: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(3)


if __name__ == '__main__':
    main()