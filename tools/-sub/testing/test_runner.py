#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YDS-Lab 测试运行工具
提供自动化测试执行、结果收集和报告生成
适配YDS-Lab项目结构和AI Agent协作需求
"""

import os
import sys
import json
import yaml
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import xml.etree.ElementTree as ET
import coverage
import pytest

@dataclass
class TestResult:
    """测试结果数据类"""
    test_name: str
    test_file: str
    status: str  # passed, failed, skipped, error
    duration: float
    message: str = ""
    traceback: str = ""
    output: str = ""

@dataclass
class TestSuite:
    """测试套件数据类"""
    name: str
    tests: List[TestResult]
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    error_tests: int = 0
    total_duration: float = 0.0

class TestRunner:
    """测试运行器"""
    
    def __init__(self, project_root: str = None):
        """初始化测试运行器"""
        if project_root is None:
            self.project_root = Path(__file__).parent.parent.parent
        else:
            self.project_root = Path(project_root)
        
        self.config_dir = self.project_root / "Struc" / "GeneralOffice" / "config"
        self.reports_dir = self.project_root / "reports" / "testing"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # 测试配置
        self.test_config = self._load_test_config()
        
        # 测试结果
        self.test_suites: List[TestSuite] = []
        self.coverage_data = None
        
        # 支持的测试框架
        self.test_frameworks = {
            'pytest': self._run_pytest,
            'unittest': self._run_unittest,
            'nose2': self._run_nose2,
            'doctest': self._run_doctest
        }
    
    def _load_test_config(self) -> Dict[str, Any]:
        """加载测试配置"""
        config_file = self.config_dir / "test_config.yaml"
        
        default_config = {
            'test_framework': 'pytest',
            'test_directories': ['tests', 'test'],
            'test_patterns': ['test_*.py', '*_test.py'],
            'coverage_enabled': True,
            'coverage_threshold': 80.0,
            'coverage_exclude': [
                '*/tests/*',
                '*/test/*',
                '*/__pycache__/*',
                '*/venv/*',
                '*/.venv/*'
            ],
            'pytest_options': [
                '-v',
                '--tb=short',
                '--strict-markers',
                '--disable-warnings'
            ],
            'unittest_options': [
                '-v'
            ],
            'parallel_execution': False,
            'max_workers': 4,
            'timeout': 300,  # 5分钟
            'retry_failed': False,
            'retry_count': 3,
            'generate_html_report': True,
            'generate_xml_report': True,
            'generate_json_report': True
        }
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f)
                    default_config.update(user_config)
            except Exception as e:
                print(f"⚠️ 加载测试配置失败: {e}")
        
        return default_config
    
    def discover_tests(self) -> List[Path]:
        """发现测试文件"""
        test_files = []
        
        for test_dir in self.test_config['test_directories']:
            test_path = self.project_root / test_dir
            
            if not test_path.exists():
                continue
            
            for pattern in self.test_config['test_patterns']:
                test_files.extend(test_path.rglob(pattern))
        
        # 去重并排序
        test_files = sorted(list(set(test_files)))
        
        print(f"🔍 发现 {len(test_files)} 个测试文件")
        for test_file in test_files:
            print(f"  - {test_file.relative_to(self.project_root)}")
        
        return test_files
    
    def run_tests(self, test_files: List[Path] = None, framework: str = None) -> Dict[str, Any]:
        """运行测试"""
        if framework is None:
            framework = self.test_config['test_framework']
        
        if framework not in self.test_frameworks:
            raise ValueError(f"不支持的测试框架: {framework}")
        
        if test_files is None:
            test_files = self.discover_tests()
        
        if not test_files:
            print("⚠️ 未找到测试文件")
            return {'status': 'no_tests', 'message': '未找到测试文件'}
        
        print(f"🧪 使用 {framework} 运行测试...")
        
        # 启动覆盖率收集
        if self.test_config['coverage_enabled']:
            self._start_coverage()
        
        # 运行测试
        start_time = time.time()
        
        try:
            runner_func = self.test_frameworks[framework]
            result = runner_func(test_files)
            
            result['duration'] = time.time() - start_time
            result['framework'] = framework
            result['test_files_count'] = len(test_files)
            
        except Exception as e:
            result = {
                'status': 'error',
                'message': f'测试运行失败: {str(e)}',
                'duration': time.time() - start_time,
                'framework': framework
            }
        
        # 停止覆盖率收集
        if self.test_config['coverage_enabled']:
            self._stop_coverage()
        
        return result
    
    def _start_coverage(self):
        """启动覆盖率收集"""
        try:
            self.coverage_data = coverage.Coverage(
                source=[str(self.project_root)],
                omit=self.test_config['coverage_exclude']
            )
            self.coverage_data.start()
            print("📊 启动代码覆盖率收集")
        except Exception as e:
            print(f"⚠️ 启动覆盖率收集失败: {e}")
            self.coverage_data = None
    
    def _stop_coverage(self):
        """停止覆盖率收集"""
        if self.coverage_data:
            try:
                self.coverage_data.stop()
                self.coverage_data.save()
                print("📊 停止代码覆盖率收集")
            except Exception as e:
                print(f"⚠️ 停止覆盖率收集失败: {e}")
    
    def _run_pytest(self, test_files: List[Path]) -> Dict[str, Any]:
        """运行pytest测试"""
        cmd = ['python', '-m', 'pytest']
        cmd.extend(self.test_config['pytest_options'])
        
        # 添加测试文件
        cmd.extend([str(f) for f in test_files])
        
        # 添加输出格式
        junit_file = self.reports_dir / 'pytest_results.xml'
        cmd.extend(['--junitxml', str(junit_file)])
        
        if self.test_config['coverage_enabled']:
            cmd.extend(['--cov', str(self.project_root)])
            cmd.extend(['--cov-report', 'html:' + str(self.reports_dir / 'coverage_html')])
            cmd.extend(['--cov-report', 'xml:' + str(self.reports_dir / 'coverage.xml')])
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=self.test_config['timeout']
            )
            
            # 解析结果
            test_results = self._parse_pytest_results(junit_file, result.stdout)
            
            return {
                'status': 'completed',
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'test_results': test_results
            }
            
        except subprocess.TimeoutExpired:
            return {
                'status': 'timeout',
                'message': f'测试超时 ({self.test_config["timeout"]}秒)'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'运行pytest失败: {str(e)}'
            }
    
    def _run_unittest(self, test_files: List[Path]) -> Dict[str, Any]:
        """运行unittest测试"""
        cmd = ['python', '-m', 'unittest']
        cmd.extend(self.test_config['unittest_options'])
        
        # 转换文件路径为模块名
        modules = []
        for test_file in test_files:
            try:
                # 将文件路径转换为模块路径
                rel_path = test_file.relative_to(self.project_root)
                module_path = str(rel_path.with_suffix('')).replace(os.sep, '.')
                modules.append(module_path)
            except ValueError:
                # 文件不在项目根目录下
                continue
        
        cmd.extend(modules)
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=self.test_config['timeout']
            )
            
            # 解析结果
            test_results = self._parse_unittest_results(result.stdout, result.stderr)
            
            return {
                'status': 'completed',
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'test_results': test_results
            }
            
        except subprocess.TimeoutExpired:
            return {
                'status': 'timeout',
                'message': f'测试超时 ({self.test_config["timeout"]}秒)'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'运行unittest失败: {str(e)}'
            }
    
    def _run_nose2(self, test_files: List[Path]) -> Dict[str, Any]:
        """运行nose2测试"""
        cmd = ['python', '-m', 'nose2', '-v']
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=self.test_config['timeout']
            )
            
            # 解析结果
            test_results = self._parse_nose2_results(result.stdout, result.stderr)
            
            return {
                'status': 'completed',
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'test_results': test_results
            }
            
        except subprocess.TimeoutExpired:
            return {
                'status': 'timeout',
                'message': f'测试超时 ({self.test_config["timeout"]}秒)'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'运行nose2失败: {str(e)}'
            }
    
    def _run_doctest(self, test_files: List[Path]) -> Dict[str, Any]:
        """运行doctest测试"""
        results = []
        
        for test_file in test_files:
            if test_file.suffix == '.py':
                cmd = ['python', '-m', 'doctest', '-v', str(test_file)]
                
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    results.append({
                        'file': str(test_file),
                        'return_code': result.returncode,
                        'stdout': result.stdout,
                        'stderr': result.stderr
                    })
                    
                except Exception as e:
                    results.append({
                        'file': str(test_file),
                        'error': str(e)
                    })
        
        return {
            'status': 'completed',
            'results': results
        }
    
    def _parse_pytest_results(self, junit_file: Path, stdout: str) -> List[TestSuite]:
        """解析pytest结果"""
        test_suites = []
        
        if junit_file.exists():
            try:
                tree = ET.parse(junit_file)
                root = tree.getroot()
                
                for testsuite in root.findall('testsuite'):
                    suite_name = testsuite.get('name', 'Unknown')
                    tests = []
                    
                    for testcase in testsuite.findall('testcase'):
                        test_name = testcase.get('name')
                        test_file = testcase.get('classname', '')
                        duration = float(testcase.get('time', 0))
                        
                        # 确定测试状态
                        status = 'passed'
                        message = ''
                        traceback = ''
                        
                        failure = testcase.find('failure')
                        error = testcase.find('error')
                        skipped = testcase.find('skipped')
                        
                        if failure is not None:
                            status = 'failed'
                            message = failure.get('message', '')
                            traceback = failure.text or ''
                        elif error is not None:
                            status = 'error'
                            message = error.get('message', '')
                            traceback = error.text or ''
                        elif skipped is not None:
                            status = 'skipped'
                            message = skipped.get('message', '')
                        
                        test_result = TestResult(
                            test_name=test_name,
                            test_file=test_file,
                            status=status,
                            duration=duration,
                            message=message,
                            traceback=traceback
                        )
                        
                        tests.append(test_result)
                    
                    # 计算统计信息
                    suite = TestSuite(name=suite_name, tests=tests)
                    suite.total_tests = len(tests)
                    suite.passed_tests = len([t for t in tests if t.status == 'passed'])
                    suite.failed_tests = len([t for t in tests if t.status == 'failed'])
                    suite.error_tests = len([t for t in tests if t.status == 'error'])
                    suite.skipped_tests = len([t for t in tests if t.status == 'skipped'])
                    suite.total_duration = sum(t.duration for t in tests)
                    
                    test_suites.append(suite)
                    
            except Exception as e:
                print(f"⚠️ 解析pytest结果失败: {e}")
        
        return test_suites
    
    def _parse_unittest_results(self, stdout: str, stderr: str) -> List[TestSuite]:
        """解析unittest结果"""
        # 简化的unittest结果解析
        test_suites = []
        
        # 从输出中提取测试信息
        lines = stdout.split('\n') + stderr.split('\n')
        
        tests = []
        for line in lines:
            if ' ... ' in line:
                parts = line.split(' ... ')
                if len(parts) == 2:
                    test_name = parts[0].strip()
                    status_text = parts[1].strip().lower()
                    
                    if status_text == 'ok':
                        status = 'passed'
                    elif status_text == 'fail':
                        status = 'failed'
                    elif status_text == 'error':
                        status = 'error'
                    elif status_text == 'skip':
                        status = 'skipped'
                    else:
                        status = 'unknown'
                    
                    test_result = TestResult(
                        test_name=test_name,
                        test_file='',
                        status=status,
                        duration=0.0
                    )
                    
                    tests.append(test_result)
        
        if tests:
            suite = TestSuite(name='unittest', tests=tests)
            suite.total_tests = len(tests)
            suite.passed_tests = len([t for t in tests if t.status == 'passed'])
            suite.failed_tests = len([t for t in tests if t.status == 'failed'])
            suite.error_tests = len([t for t in tests if t.status == 'error'])
            suite.skipped_tests = len([t for t in tests if t.status == 'skipped'])
            
            test_suites.append(suite)
        
        return test_suites
    
    def _parse_nose2_results(self, stdout: str, stderr: str) -> List[TestSuite]:
        """解析nose2结果"""
        # 简化的nose2结果解析
        return self._parse_unittest_results(stdout, stderr)
    
    def get_coverage_report(self) -> Optional[Dict[str, Any]]:
        """获取覆盖率报告"""
        if not self.coverage_data:
            return None
        
        try:
            # 生成覆盖率报告
            coverage_report = {}
            
            # 总体覆盖率
            total_coverage = self.coverage_data.report()
            coverage_report['total_coverage'] = total_coverage
            
            # 文件级覆盖率
            file_coverage = {}
            for filename in self.coverage_data.get_data().measured_files():
                try:
                    rel_path = Path(filename).relative_to(self.project_root)
                    analysis = self.coverage_data.analysis2(filename)
                    
                    total_lines = len(analysis.statements)
                    covered_lines = len(analysis.statements) - len(analysis.missing)
                    coverage_percent = (covered_lines / total_lines * 100) if total_lines > 0 else 0
                    
                    file_coverage[str(rel_path)] = {
                        'total_lines': total_lines,
                        'covered_lines': covered_lines,
                        'missing_lines': list(analysis.missing),
                        'coverage_percent': coverage_percent
                    }
                except Exception:
                    continue
            
            coverage_report['file_coverage'] = file_coverage
            
            # 检查覆盖率阈值
            threshold = self.test_config['coverage_threshold']
            coverage_report['meets_threshold'] = total_coverage >= threshold
            coverage_report['threshold'] = threshold
            
            return coverage_report
            
        except Exception as e:
            print(f"⚠️ 生成覆盖率报告失败: {e}")
            return None
    
    def generate_report(self, test_result: Dict[str, Any], output_format: str = 'markdown') -> str:
        """生成测试报告"""
        if output_format == 'markdown':
            return self._generate_markdown_report(test_result)
        elif output_format == 'json':
            return self._generate_json_report(test_result)
        elif output_format == 'html':
            return self._generate_html_report(test_result)
        else:
            raise ValueError(f"不支持的输出格式: {output_format}")
    
    def _generate_markdown_report(self, test_result: Dict[str, Any]) -> str:
        """生成Markdown格式报告"""
        report = []
        
        # 报告头部
        report.append("# 🧪 测试报告")
        report.append("")
        report.append(f"**测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"**项目路径**: {self.project_root}")
        report.append(f"**测试框架**: {test_result.get('framework', 'Unknown')}")
        report.append(f"**测试文件数**: {test_result.get('test_files_count', 0)}")
        report.append(f"**执行时间**: {test_result.get('duration', 0):.2f}秒")
        report.append("")
        
        # 测试状态
        status = test_result.get('status', 'unknown')
        if status == 'completed':
            return_code = test_result.get('return_code', 0)
            if return_code == 0:
                report.append("## ✅ 测试状态: 通过")
            else:
                report.append("## ❌ 测试状态: 失败")
        elif status == 'timeout':
            report.append("## ⏰ 测试状态: 超时")
        elif status == 'error':
            report.append("## 💥 测试状态: 错误")
        else:
            report.append(f"## ❓ 测试状态: {status}")
        
        report.append("")
        
        # 测试统计
        test_suites = test_result.get('test_results', [])
        if test_suites:
            total_tests = sum(suite.total_tests for suite in test_suites)
            total_passed = sum(suite.passed_tests for suite in test_suites)
            total_failed = sum(suite.failed_tests for suite in test_suites)
            total_errors = sum(suite.error_tests for suite in test_suites)
            total_skipped = sum(suite.skipped_tests for suite in test_suites)
            total_duration = sum(suite.total_duration for suite in test_suites)
            
            report.append("## 📊 测试统计")
            report.append("")
            report.append(f"- **总测试数**: {total_tests}")
            report.append(f"- **通过**: {total_passed}")
            report.append(f"- **失败**: {total_failed}")
            report.append(f"- **错误**: {total_errors}")
            report.append(f"- **跳过**: {total_skipped}")
            report.append(f"- **总耗时**: {total_duration:.2f}秒")
            
            if total_tests > 0:
                success_rate = (total_passed / total_tests) * 100
                report.append(f"- **成功率**: {success_rate:.1f}%")
            
            report.append("")
            
            # 测试套件详情
            report.append("## 📋 测试套件详情")
            report.append("")
            
            for suite in test_suites:
                report.append(f"### {suite.name}")
                report.append("")
                report.append(f"- 总测试数: {suite.total_tests}")
                report.append(f"- 通过: {suite.passed_tests}")
                report.append(f"- 失败: {suite.failed_tests}")
                report.append(f"- 错误: {suite.error_tests}")
                report.append(f"- 跳过: {suite.skipped_tests}")
                report.append(f"- 耗时: {suite.total_duration:.2f}秒")
                report.append("")
                
                # 失败的测试
                failed_tests = [t for t in suite.tests if t.status in ['failed', 'error']]
                if failed_tests:
                    report.append("#### ❌ 失败的测试")
                    report.append("")
                    
                    for test in failed_tests:
                        report.append(f"**{test.test_name}**")
                        report.append(f"- 文件: `{test.test_file}`")
                        report.append(f"- 状态: {test.status}")
                        report.append(f"- 耗时: {test.duration:.3f}秒")
                        
                        if test.message:
                            report.append(f"- 错误信息: {test.message}")
                        
                        if test.traceback:
                            report.append("- 错误堆栈:")
                            report.append("```")
                            report.append(test.traceback)
                            report.append("```")
                        
                        report.append("")
        
        # 覆盖率报告
        coverage_report = self.get_coverage_report()
        if coverage_report:
            report.append("## 📈 代码覆盖率")
            report.append("")
            
            total_coverage = coverage_report['total_coverage']
            threshold = coverage_report['threshold']
            meets_threshold = coverage_report['meets_threshold']
            
            report.append(f"- **总覆盖率**: {total_coverage:.1f}%")
            report.append(f"- **覆盖率阈值**: {threshold}%")
            
            if meets_threshold:
                report.append("- **阈值检查**: ✅ 通过")
            else:
                report.append("- **阈值检查**: ❌ 未达标")
            
            report.append("")
            
            # 文件覆盖率详情
            file_coverage = coverage_report.get('file_coverage', {})
            if file_coverage:
                report.append("### 文件覆盖率详情")
                report.append("")
                
                # 按覆盖率排序
                sorted_files = sorted(
                    file_coverage.items(),
                    key=lambda x: x[1]['coverage_percent']
                )
                
                for file_path, coverage_info in sorted_files:
                    coverage_percent = coverage_info['coverage_percent']
                    total_lines = coverage_info['total_lines']
                    covered_lines = coverage_info['covered_lines']
                    
                    status_icon = "✅" if coverage_percent >= threshold else "❌"
                    
                    report.append(f"{status_icon} **{file_path}**: {coverage_percent:.1f}% ({covered_lines}/{total_lines})")
                
                report.append("")
        
        # 输出信息
        if test_result.get('stdout'):
            report.append("## 📤 标准输出")
            report.append("")
            report.append("```")
            report.append(test_result['stdout'])
            report.append("```")
            report.append("")
        
        if test_result.get('stderr'):
            report.append("## 📥 错误输出")
            report.append("")
            report.append("```")
            report.append(test_result['stderr'])
            report.append("```")
            report.append("")
        
        return '\n'.join(report)
    
    def _generate_json_report(self, test_result: Dict[str, Any]) -> str:
        """生成JSON格式报告"""
        report_data = {
            'test_info': {
                'test_time': datetime.now().isoformat(),
                'project_path': str(self.project_root),
                'framework': test_result.get('framework', 'Unknown'),
                'test_files_count': test_result.get('test_files_count', 0),
                'duration': test_result.get('duration', 0)
            },
            'test_result': test_result,
            'coverage_report': self.get_coverage_report()
        }
        
        return json.dumps(report_data, ensure_ascii=False, indent=2)
    
    def _generate_html_report(self, test_result: Dict[str, Any]) -> str:
        """生成HTML格式报告"""
        # 简化的HTML报告
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>测试报告</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
        .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
        .stat-card {{ background: #fff; border: 1px solid #ddd; padding: 15px; border-radius: 5px; }}
        .passed {{ color: #28a745; }}
        .failed {{ color: #dc3545; }}
        .error {{ color: #fd7e14; }}
        .skipped {{ color: #6c757d; }}
        .test-case {{ border-left: 4px solid #ccc; padding: 15px; margin: 10px 0; }}
        .test-case.passed {{ border-left-color: #28a745; }}
        .test-case.failed {{ border-left-color: #dc3545; }}
        .test-case.error {{ border-left-color: #fd7e14; }}
        .test-case.skipped {{ border-left-color: #6c757d; }}
        .code {{ background: #f8f9fa; padding: 10px; border-radius: 3px; font-family: monospace; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🧪 测试报告</h1>
        <p><strong>测试时间</strong>: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>项目路径</strong>: {self.project_root}</p>
        <p><strong>测试框架</strong>: {test_result.get('framework', 'Unknown')}</p>
    </div>
"""
        
        # 添加统计信息
        test_suites = test_result.get('test_results', [])
        if test_suites:
            total_tests = sum(suite.total_tests for suite in test_suites)
            total_passed = sum(suite.passed_tests for suite in test_suites)
            total_failed = sum(suite.failed_tests for suite in test_suites)
            total_errors = sum(suite.error_tests for suite in test_suites)
            total_skipped = sum(suite.skipped_tests for suite in test_suites)
            
            html += f"""
    <h2>📊 测试统计</h2>
    <div class="stats">
        <div class="stat-card">
            <h3>总测试数</h3>
            <p>{total_tests}</p>
        </div>
        <div class="stat-card">
            <h3 class="passed">通过</h3>
            <p>{total_passed}</p>
        </div>
        <div class="stat-card">
            <h3 class="failed">失败</h3>
            <p>{total_failed}</p>
        </div>
        <div class="stat-card">
            <h3 class="error">错误</h3>
            <p>{total_errors}</p>
        </div>
        <div class="stat-card">
            <h3 class="skipped">跳过</h3>
            <p>{total_skipped}</p>
        </div>
    </div>
"""
            
            # 添加失败的测试
            for suite in test_suites:
                failed_tests = [t for t in suite.tests if t.status in ['failed', 'error']]
                if failed_tests:
                    html += f"<h2>❌ {suite.name} - 失败的测试</h2>"
                    
                    for test in failed_tests:
                        html += f"""
    <div class="test-case {test.status}">
        <h3>{test.test_name}</h3>
        <p><strong>文件</strong>: {test.test_file}</p>
        <p><strong>状态</strong>: {test.status}</p>
        <p><strong>耗时</strong>: {test.duration:.3f}秒</p>
"""
                        
                        if test.message:
                            html += f"<p><strong>错误信息</strong>: {test.message}</p>"
                        
                        if test.traceback:
                            html += f'<div class="code">{test.traceback}</div>'
                        
                        html += "</div>"
        
        html += """
</body>
</html>
"""
        
        return html
    
    def save_report(self, test_result: Dict[str, Any], output_format: str = 'markdown', filename: str = None) -> str:
        """保存测试报告"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"test_report_{timestamp}.{output_format}"
        
        report_content = self.generate_report(test_result, output_format)
        report_path = self.reports_dir / filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"📄 测试报告已保存: {report_path}")
        return str(report_path)
    
    def run_continuous_tests(self, watch_directories: List[str] = None):
        """运行持续测试（监控文件变化）"""
        if watch_directories is None:
            watch_directories = ['src', 'tests', 'test']
        
        print("👀 启动持续测试模式...")
        print("按 Ctrl+C 停止监控")
        
        try:
            import watchdog
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
            
            class TestHandler(FileSystemEventHandler):
                def __init__(self, test_runner):
                    self.test_runner = test_runner
                    self.last_run = 0
                
                def on_modified(self, event):
                    if event.is_directory:
                        return
                    
                    # 避免频繁触发
                    current_time = time.time()
                    if current_time - self.last_run < 2:
                        return
                    
                    if event.src_path.endswith('.py'):
                        print(f"\n📝 检测到文件变化: {event.src_path}")
                        print("🧪 重新运行测试...")
                        
                        result = self.test_runner.run_tests()
                        self.test_runner.save_report(result)
                        
                        self.last_run = current_time
            
            observer = Observer()
            handler = TestHandler(self)
            
            for watch_dir in watch_directories:
                watch_path = self.project_root / watch_dir
                if watch_path.exists():
                    observer.schedule(handler, str(watch_path), recursive=True)
                    print(f"📁 监控目录: {watch_path}")
            
            observer.start()
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                observer.stop()
                print("\n⏹️ 停止持续测试")
            
            observer.join()
            
        except ImportError:
            print("⚠️ 需要安装 watchdog 库来支持持续测试")
            print("运行: pip install watchdog")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='YDS-Lab 测试运行工具')
    parser.add_argument('--project-root', help='指定项目根目录路径')
    parser.add_argument('--framework', choices=['pytest', 'unittest', 'nose2', 'doctest'],
                       help='指定测试框架')
    parser.add_argument('--output-format', choices=['markdown', 'json', 'html'],
                       default='markdown', help='输出格式')
    parser.add_argument('--output-file', help='输出文件名')
    parser.add_argument('--no-coverage', action='store_true', help='禁用覆盖率收集')
    parser.add_argument('--continuous', action='store_true', help='启用持续测试模式')
    parser.add_argument('--discover', action='store_true', help='仅发现测试文件')
    parser.add_argument('test_files', nargs='*', help='指定测试文件')
    
    args = parser.parse_args()
    
    runner = TestRunner(args.project_root)
    
    # 更新配置
    if args.no_coverage:
        runner.test_config['coverage_enabled'] = False
    
    # 仅发现测试文件
    if args.discover:
        test_files = runner.discover_tests()
        print(f"\n发现 {len(test_files)} 个测试文件:")
        for test_file in test_files:
            print(f"  {test_file.relative_to(runner.project_root)}")
        return
    
    # 持续测试模式
    if args.continuous:
        runner.run_continuous_tests()
        return
    
    # 指定测试文件
    test_files = None
    if args.test_files:
        test_files = [Path(f) for f in args.test_files]
    
    # 运行测试
    result = runner.run_tests(test_files, args.framework)
    
    # 保存报告
    report_path = runner.save_report(result, args.output_format, args.output_file)
    
    # 输出摘要
    print("\n" + "="*50)
    print("📋 测试摘要")
    print("="*50)
    
    if result['status'] == 'completed':
        test_suites = result.get('test_results', [])
        if test_suites:
            total_tests = sum(suite.total_tests for suite in test_suites)
            total_passed = sum(suite.passed_tests for suite in test_suites)
            total_failed = sum(suite.failed_tests for suite in test_suites)
            total_errors = sum(suite.error_tests for suite in test_suites)
            
            print(f"总测试数: {total_tests}")
            print(f"通过: {total_passed}")
            print(f"失败: {total_failed}")
            print(f"错误: {total_errors}")
            
            if total_tests > 0:
                success_rate = (total_passed / total_tests) * 100
                print(f"成功率: {success_rate:.1f}%")
            
            # 覆盖率信息
            coverage_report = runner.get_coverage_report()
            if coverage_report:
                total_coverage = coverage_report['total_coverage']
                print(f"代码覆盖率: {total_coverage:.1f}%")
        
        # 根据测试结果设置退出码
        return_code = result.get('return_code', 0)
        if return_code != 0:
            print("\n❌ 测试失败")
            sys.exit(return_code)
        else:
            print("\n✅ 所有测试通过")
    
    elif result['status'] == 'timeout':
        print(f"⏰ 测试超时: {result.get('message', '')}")
        sys.exit(1)
    
    elif result['status'] == 'error':
        print(f"💥 测试错误: {result.get('message', '')}")
        sys.exit(1)
    
    else:
        print(f"❓ 未知状态: {result['status']}")
        sys.exit(1)

if __name__ == "__main__":
    main()