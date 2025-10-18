#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YDS-Lab 性能分析工具
提供代码性能分析、性能测试和优化建议
适配YDS-Lab项目结构和AI Agent协作需求
"""

import os
import sys
import json
import yaml
import time
import cProfile
import pstats
import tracemalloc
import threading
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import logging
import ast
import re

@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    timestamp: str
    function_name: str
    filename: str
    line_number: int
    call_count: int
    total_time: float
    cumulative_time: float
    per_call_time: float
    memory_usage: int = 0
    memory_peak: int = 0

@dataclass
class MemorySnapshot:
    """内存快照数据类"""
    timestamp: str
    current_memory: int
    peak_memory: int
    memory_blocks: int
    top_allocations: List[Dict[str, Any]]

@dataclass
class PerformanceIssue:
    """性能问题数据类"""
    severity: str  # low, medium, high, critical
    category: str  # time, memory, io, cpu
    function_name: str
    filename: str
    line_number: int
    description: str
    suggestion: str
    metrics: Dict[str, Any]

class PerformanceAnalyzer:
    """性能分析器"""
    
    def __init__(self, project_root: str = None):
        """初始化性能分析器"""
        if project_root is None:
            self.project_root = Path(__file__).parent.parent.parent
        else:
            self.project_root = Path(project_root)
        
        self.config_dir = self.project_root / "Struc" / "GeneralOffice" / "config"
        self.logs_dir = self.project_root / "logs" / "performance"
        self.reports_dir = self.project_root / "reports" / "performance"
        self.profiles_dir = self.project_root / "profiles"
        
        # 创建目录
        for directory in [self.logs_dir, self.reports_dir, self.profiles_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # 分析配置
        self.config = self._load_config()
        
        # 性能数据
        self.metrics_history = deque(maxlen=self.config['history_size'])
        self.memory_snapshots = deque(maxlen=self.config['memory_history_size'])
        self.performance_issues = []
        
        # 分析状态
        self.profiling = False
        self.memory_tracing = False
        self.profiler = None
        
        # 设置日志
        self._setup_logging()
        
        # 性能阈值
        self.thresholds = self.config['performance_thresholds']
    
    def _load_config(self) -> Dict[str, Any]:
        """加载性能分析配置"""
        config_file = self.config_dir / "performance_config.yaml"
        
        default_config = {
            'history_size': 1000,
            'memory_history_size': 100,
            'profile_output_dir': 'profiles',
            'enable_memory_tracing': True,
            'enable_line_profiling': False,
            'performance_thresholds': {
                'slow_function_time': 1.0,  # 秒
                'high_memory_usage': 100 * 1024 * 1024,  # 100MB
                'excessive_calls': 1000,
                'memory_leak_threshold': 10 * 1024 * 1024,  # 10MB增长
                'cpu_intensive_threshold': 5.0  # 秒
            },
            'analysis_patterns': {
                'inefficient_loops': [
                    r'for\s+\w+\s+in\s+range\(len\(',
                    r'while\s+.*len\(',
                ],
                'memory_leaks': [
                    r'global\s+\w+\s*=\s*\[\]',
                    r'\.append\(',
                    r'\.extend\(',
                ],
                'io_bottlenecks': [
                    r'open\(',
                    r'\.read\(',
                    r'\.write\(',
                    r'requests\.',
                ],
                'database_issues': [
                    r'SELECT\s+\*',
                    r'\.execute\(',
                    r'cursor\.',
                ]
            },
            'optimization_suggestions': {
                'slow_function': [
                    "考虑使用缓存机制",
                    "优化算法复杂度",
                    "使用并行处理",
                    "减少不必要的计算"
                ],
                'high_memory': [
                    "使用生成器代替列表",
                    "及时释放不需要的对象",
                    "考虑使用内存映射",
                    "优化数据结构"
                ],
                'excessive_calls': [
                    "减少函数调用次数",
                    "合并相似操作",
                    "使用批处理",
                    "缓存计算结果"
                ]
            },
            'log_level': 'INFO',
            'auto_cleanup': True,
            'retention_days': 30
        }
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f)
                    default_config.update(user_config)
            except Exception as e:
                print(f"⚠️ 加载性能分析配置失败: {e}")
        
        return default_config
    
    def _setup_logging(self):
        """设置日志"""
        log_file = self.logs_dir / f"performance_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=getattr(logging, self.config['log_level']),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def start_profiling(self, sort_by: str = 'cumulative') -> str:
        """启动性能分析"""
        if self.profiling:
            self.logger.warning("性能分析已在运行中")
            return None
        
        # 启动cProfile
        self.profiler = cProfile.Profile()
        self.profiler.enable()
        
        # 启动内存跟踪
        if self.config['enable_memory_tracing']:
            tracemalloc.start()
            self.memory_tracing = True
        
        self.profiling = True
        self.sort_by = sort_by
        
        self.logger.info("性能分析已启动")
        return "性能分析已启动"
    
    def stop_profiling(self) -> str:
        """停止性能分析并生成报告"""
        if not self.profiling:
            self.logger.warning("性能分析未在运行")
            return None
        
        # 停止cProfile
        self.profiler.disable()
        
        # 生成性能报告
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        profile_file = self.profiles_dir / f"profile_{timestamp}.prof"
        
        # 保存profile文件
        self.profiler.dump_stats(str(profile_file))
        
        # 分析profile数据
        stats = pstats.Stats(self.profiler)
        stats.sort_stats(self.sort_by)
        
        # 提取性能指标
        self._extract_performance_metrics(stats)
        
        # 停止内存跟踪
        if self.memory_tracing:
            self._capture_memory_snapshot()
            tracemalloc.stop()
            self.memory_tracing = False
        
        self.profiling = False
        self.profiler = None
        
        self.logger.info(f"性能分析已停止，报告保存至: {profile_file}")
        return str(profile_file)
    
    def _extract_performance_metrics(self, stats: pstats.Stats):
        """提取性能指标"""
        timestamp = datetime.now().isoformat()
        
        # 获取统计信息
        for func_info, (call_count, total_time, cumulative_time, callers) in stats.stats.items():
            filename, line_number, function_name = func_info
            
            # 过滤系统函数
            if not self._should_analyze_function(filename, function_name):
                continue
            
            per_call_time = total_time / call_count if call_count > 0 else 0
            
            metrics = PerformanceMetrics(
                timestamp=timestamp,
                function_name=function_name,
                filename=filename,
                line_number=line_number,
                call_count=call_count,
                total_time=total_time,
                cumulative_time=cumulative_time,
                per_call_time=per_call_time
            )
            
            self.metrics_history.append(metrics)
            
            # 检查性能问题
            self._check_performance_issues(metrics)
    
    def _should_analyze_function(self, filename: str, function_name: str) -> bool:
        """判断是否应该分析该函数"""
        # 过滤系统库和第三方库
        if any(path in filename for path in [
            'site-packages', 'lib/python', '<built-in>', '<string>',
            'importlib', 'pkgutil', 'threading', 'queue'
        ]):
            return False
        
        # 过滤特殊函数
        if function_name.startswith('_') and not function_name.startswith('__'):
            return False
        
        # 只分析项目相关文件
        try:
            file_path = Path(filename)
            return str(self.project_root) in str(file_path.resolve())
        except Exception:
            return False
    
    def _capture_memory_snapshot(self):
        """捕获内存快照"""
        if not tracemalloc.is_tracing():
            return
        
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')
        
        current_memory = sum(stat.size for stat in top_stats)
        peak_memory = tracemalloc.get_traced_memory()[1]
        
        # 获取前10个内存分配
        top_allocations = []
        for stat in top_stats[:10]:
            top_allocations.append({
                'filename': stat.traceback.format()[0] if stat.traceback.format() else 'unknown',
                'size': stat.size,
                'count': stat.count
            })
        
        memory_snapshot = MemorySnapshot(
            timestamp=datetime.now().isoformat(),
            current_memory=current_memory,
            peak_memory=peak_memory,
            memory_blocks=len(top_stats),
            top_allocations=top_allocations
        )
        
        self.memory_snapshots.append(memory_snapshot)
    
    def _check_performance_issues(self, metrics: PerformanceMetrics):
        """检查性能问题"""
        issues = []
        
        # 检查慢函数
        if metrics.total_time > self.thresholds['slow_function_time']:
            issue = PerformanceIssue(
                severity='high' if metrics.total_time > 5.0 else 'medium',
                category='time',
                function_name=metrics.function_name,
                filename=metrics.filename,
                line_number=metrics.line_number,
                description=f"函数执行时间过长: {metrics.total_time:.2f}秒",
                suggestion=self._get_optimization_suggestion('slow_function'),
                metrics={'total_time': metrics.total_time, 'call_count': metrics.call_count}
            )
            issues.append(issue)
        
        # 检查频繁调用
        if metrics.call_count > self.thresholds['excessive_calls']:
            issue = PerformanceIssue(
                severity='medium',
                category='cpu',
                function_name=metrics.function_name,
                filename=metrics.filename,
                line_number=metrics.line_number,
                description=f"函数调用次数过多: {metrics.call_count}次",
                suggestion=self._get_optimization_suggestion('excessive_calls'),
                metrics={'call_count': metrics.call_count, 'per_call_time': metrics.per_call_time}
            )
            issues.append(issue)
        
        # 检查高内存使用
        if metrics.memory_usage > self.thresholds['high_memory_usage']:
            issue = PerformanceIssue(
                severity='high',
                category='memory',
                function_name=metrics.function_name,
                filename=metrics.filename,
                line_number=metrics.line_number,
                description=f"内存使用过高: {metrics.memory_usage / (1024*1024):.1f}MB",
                suggestion=self._get_optimization_suggestion('high_memory'),
                metrics={'memory_usage': metrics.memory_usage}
            )
            issues.append(issue)
        
        self.performance_issues.extend(issues)
    
    def _get_optimization_suggestion(self, issue_type: str) -> str:
        """获取优化建议"""
        suggestions = self.config['optimization_suggestions'].get(issue_type, [])
        return "; ".join(suggestions) if suggestions else "需要进一步分析"
    
    def analyze_code_patterns(self, file_path: str) -> List[PerformanceIssue]:
        """分析代码模式"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 分析低效模式
            for pattern_type, patterns in self.config['analysis_patterns'].items():
                for pattern in patterns:
                    matches = re.finditer(pattern, content, re.MULTILINE)
                    
                    for match in matches:
                        line_number = content[:match.start()].count('\n') + 1
                        
                        issue = PerformanceIssue(
                            severity='medium',
                            category=self._get_pattern_category(pattern_type),
                            function_name='unknown',
                            filename=file_path,
                            line_number=line_number,
                            description=f"发现{pattern_type}模式: {match.group()}",
                            suggestion=self._get_pattern_suggestion(pattern_type),
                            metrics={'pattern': pattern, 'line': line_number}
                        )
                        
                        issues.append(issue)
        
        except Exception as e:
            self.logger.error(f"分析代码模式失败 {file_path}: {e}")
        
        return issues
    
    def _get_pattern_category(self, pattern_type: str) -> str:
        """获取模式类别"""
        category_map = {
            'inefficient_loops': 'cpu',
            'memory_leaks': 'memory',
            'io_bottlenecks': 'io',
            'database_issues': 'io'
        }
        return category_map.get(pattern_type, 'other')
    
    def _get_pattern_suggestion(self, pattern_type: str) -> str:
        """获取模式优化建议"""
        suggestions = {
            'inefficient_loops': "使用enumerate()或直接迭代，避免range(len())",
            'memory_leaks': "注意全局变量和循环引用，及时清理不需要的对象",
            'io_bottlenecks': "考虑异步IO、批处理或缓存机制",
            'database_issues': "优化SQL查询，使用索引，避免SELECT *"
        }
        return suggestions.get(pattern_type, "需要进一步优化")
    
    def analyze_project(self, include_patterns: List[str] = None) -> Dict[str, Any]:
        """分析整个项目"""
        if include_patterns is None:
            include_patterns = ['*.py']
        
        analysis_results = {
            'timestamp': datetime.now().isoformat(),
            'project_root': str(self.project_root),
            'files_analyzed': 0,
            'total_issues': 0,
            'issues_by_severity': defaultdict(int),
            'issues_by_category': defaultdict(int),
            'files_with_issues': [],
            'top_issues': []
        }
        
        # 扫描项目文件
        all_issues = []
        
        for pattern in include_patterns:
            for file_path in self.project_root.rglob(pattern):
                if self._should_analyze_file(file_path):
                    file_issues = self.analyze_code_patterns(str(file_path))
                    
                    if file_issues:
                        analysis_results['files_with_issues'].append({
                            'file': str(file_path.relative_to(self.project_root)),
                            'issues_count': len(file_issues),
                            'issues': [asdict(issue) for issue in file_issues]
                        })
                        
                        all_issues.extend(file_issues)
                    
                    analysis_results['files_analyzed'] += 1
        
        # 统计结果
        analysis_results['total_issues'] = len(all_issues)
        
        for issue in all_issues:
            analysis_results['issues_by_severity'][issue.severity] += 1
            analysis_results['issues_by_category'][issue.category] += 1
        
        # 获取最严重的问题
        severity_order = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
        sorted_issues = sorted(all_issues, 
                             key=lambda x: severity_order.get(x.severity, 0), 
                             reverse=True)
        
        analysis_results['top_issues'] = [asdict(issue) for issue in sorted_issues[:10]]
        
        return analysis_results
    
    def _should_analyze_file(self, file_path: Path) -> bool:
        """判断是否应该分析该文件"""
        # 跳过特定目录
        skip_dirs = {'.git', '__pycache__', '.pytest_cache', 'node_modules', 
                    '.venv', 'venv', 'env', 'build', 'dist'}
        
        if any(part in skip_dirs for part in file_path.parts):
            return False
        
        # 跳过测试文件（可选）
        if 'test' in file_path.name.lower():
            return False
        
        return True
    
    def benchmark_function(self, func: Callable, *args, iterations: int = 100, **kwargs) -> Dict[str, Any]:
        """基准测试函数"""
        results = {
            'function_name': func.__name__,
            'iterations': iterations,
            'times': [],
            'memory_usage': [],
            'total_time': 0,
            'avg_time': 0,
            'min_time': float('inf'),
            'max_time': 0,
            'std_dev': 0
        }
        
        # 预热
        for _ in range(min(10, iterations // 10)):
            func(*args, **kwargs)
        
        # 基准测试
        for i in range(iterations):
            # 内存跟踪
            if self.config['enable_memory_tracing']:
                tracemalloc.start()
            
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            
            execution_time = end_time - start_time
            results['times'].append(execution_time)
            
            if self.config['enable_memory_tracing']:
                current, peak = tracemalloc.get_traced_memory()
                results['memory_usage'].append(peak)
                tracemalloc.stop()
        
        # 计算统计信息
        times = results['times']
        results['total_time'] = sum(times)
        results['avg_time'] = results['total_time'] / iterations
        results['min_time'] = min(times)
        results['max_time'] = max(times)
        
        # 计算标准差
        if len(times) > 1:
            mean = results['avg_time']
            variance = sum((t - mean) ** 2 for t in times) / (len(times) - 1)
            results['std_dev'] = variance ** 0.5
        
        # 内存统计
        if results['memory_usage']:
            results['avg_memory'] = sum(results['memory_usage']) / len(results['memory_usage'])
            results['max_memory'] = max(results['memory_usage'])
        
        return results
    
    def compare_functions(self, functions: List[Tuple[str, Callable]], *args, iterations: int = 100, **kwargs) -> Dict[str, Any]:
        """比较多个函数的性能"""
        comparison_results = {
            'timestamp': datetime.now().isoformat(),
            'iterations': iterations,
            'functions': {},
            'ranking': []
        }
        
        # 测试每个函数
        for name, func in functions:
            self.logger.info(f"基准测试函数: {name}")
            
            try:
                results = self.benchmark_function(func, *args, iterations=iterations, **kwargs)
                results['name'] = name
                comparison_results['functions'][name] = results
            except Exception as e:
                self.logger.error(f"基准测试失败 {name}: {e}")
                comparison_results['functions'][name] = {
                    'name': name,
                    'error': str(e)
                }
        
        # 排序（按平均时间）
        valid_results = [(name, data) for name, data in comparison_results['functions'].items() 
                        if 'avg_time' in data]
        
        valid_results.sort(key=lambda x: x[1]['avg_time'])
        
        for i, (name, data) in enumerate(valid_results):
            comparison_results['ranking'].append({
                'rank': i + 1,
                'name': name,
                'avg_time': data['avg_time'],
                'relative_speed': data['avg_time'] / valid_results[0][1]['avg_time'] if valid_results else 1.0
            })
        
        return comparison_results
    
    def profile_memory_usage(self, duration: int = 60) -> Dict[str, Any]:
        """监控内存使用情况"""
        if not tracemalloc.is_tracing():
            tracemalloc.start()
        
        start_time = time.time()
        snapshots = []
        
        self.logger.info(f"开始监控内存使用，持续{duration}秒")
        
        while time.time() - start_time < duration:
            snapshot = tracemalloc.take_snapshot()
            top_stats = snapshot.statistics('lineno')
            
            current_memory = sum(stat.size for stat in top_stats)
            peak_memory = tracemalloc.get_traced_memory()[1]
            
            snapshots.append({
                'timestamp': time.time(),
                'current_memory': current_memory,
                'peak_memory': peak_memory,
                'blocks_count': len(top_stats)
            })
            
            time.sleep(1)  # 每秒采样一次
        
        tracemalloc.stop()
        
        # 分析内存趋势
        if len(snapshots) > 1:
            memory_growth = snapshots[-1]['current_memory'] - snapshots[0]['current_memory']
            avg_memory = sum(s['current_memory'] for s in snapshots) / len(snapshots)
            max_memory = max(s['current_memory'] for s in snapshots)
            
            return {
                'duration': duration,
                'snapshots_count': len(snapshots),
                'memory_growth': memory_growth,
                'avg_memory': avg_memory,
                'max_memory': max_memory,
                'peak_memory': max(s['peak_memory'] for s in snapshots),
                'snapshots': snapshots,
                'potential_leak': memory_growth > self.thresholds['memory_leak_threshold']
            }
        
        return {'error': '内存监控数据不足'}
    
    def generate_performance_report(self, output_format: str = 'markdown') -> str:
        """生成性能分析报告"""
        if output_format == 'markdown':
            return self._generate_markdown_report()
        elif output_format == 'html':
            return self._generate_html_report()
        elif output_format == 'json':
            return self._generate_json_report()
        else:
            raise ValueError(f"不支持的输出格式: {output_format}")
    
    def _generate_markdown_report(self) -> str:
        """生成Markdown格式报告"""
        report = []
        
        # 报告头部
        report.append("# 🚀 性能分析报告")
        report.append("")
        report.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"**项目路径**: {self.project_root}")
        report.append(f"**分析状态**: {'运行中' if self.profiling else '已停止'}")
        report.append("")
        
        # 性能指标摘要
        if self.metrics_history:
            report.append("## 📊 性能指标摘要")
            report.append("")
            
            # 最慢的函数
            slow_functions = sorted(self.metrics_history, 
                                  key=lambda x: x.total_time, reverse=True)[:10]
            
            if slow_functions:
                report.append("### 🐌 最慢函数 (Top 10)")
                report.append("")
                report.append("| 函数名 | 文件 | 总时间(s) | 调用次数 | 平均时间(s) |")
                report.append("|--------|------|-----------|----------|-------------|")
                
                for metrics in slow_functions:
                    filename = Path(metrics.filename).name
                    report.append(f"| {metrics.function_name} | {filename} | {metrics.total_time:.3f} | {metrics.call_count} | {metrics.per_call_time:.6f} |")
                
                report.append("")
            
            # 调用最频繁的函数
            frequent_functions = sorted(self.metrics_history, 
                                      key=lambda x: x.call_count, reverse=True)[:10]
            
            if frequent_functions:
                report.append("### 🔄 调用最频繁函数 (Top 10)")
                report.append("")
                report.append("| 函数名 | 文件 | 调用次数 | 总时间(s) | 平均时间(s) |")
                report.append("|--------|------|----------|-----------|-------------|")
                
                for metrics in frequent_functions:
                    filename = Path(metrics.filename).name
                    report.append(f"| {metrics.function_name} | {filename} | {metrics.call_count} | {metrics.total_time:.3f} | {metrics.per_call_time:.6f} |")
                
                report.append("")
        
        # 内存使用情况
        if self.memory_snapshots:
            report.append("## 💾 内存使用情况")
            report.append("")
            
            latest_snapshot = self.memory_snapshots[-1]
            
            report.append(f"- **当前内存使用**: {latest_snapshot.current_memory / (1024*1024):.1f} MB")
            report.append(f"- **峰值内存使用**: {latest_snapshot.peak_memory / (1024*1024):.1f} MB")
            report.append(f"- **内存块数量**: {latest_snapshot.memory_blocks}")
            report.append("")
            
            if latest_snapshot.top_allocations:
                report.append("### 🔝 主要内存分配")
                report.append("")
                
                for i, alloc in enumerate(latest_snapshot.top_allocations[:5], 1):
                    size_mb = alloc['size'] / (1024*1024)
                    report.append(f"{i}. **{alloc['filename']}**: {size_mb:.2f} MB ({alloc['count']} 个对象)")
                
                report.append("")
        
        # 性能问题
        if self.performance_issues:
            report.append("## ⚠️ 性能问题")
            report.append("")
            
            # 按严重程度分组
            issues_by_severity = defaultdict(list)
            for issue in self.performance_issues:
                issues_by_severity[issue.severity].append(issue)
            
            severity_order = ['critical', 'high', 'medium', 'low']
            severity_icons = {
                'critical': '🔥',
                'high': '❌',
                'medium': '⚠️',
                'low': 'ℹ️'
            }
            
            for severity in severity_order:
                if severity in issues_by_severity:
                    issues = issues_by_severity[severity]
                    icon = severity_icons.get(severity, '❓')
                    
                    report.append(f"### {icon} {severity.upper()} 级别问题 ({len(issues)}个)")
                    report.append("")
                    
                    for issue in issues[:10]:  # 显示前10个
                        filename = Path(issue.filename).name if issue.filename else 'unknown'
                        
                        report.append(f"**{issue.function_name}** ({filename}:{issue.line_number})")
                        report.append(f"- 类别: {issue.category}")
                        report.append(f"- 问题: {issue.description}")
                        report.append(f"- 建议: {issue.suggestion}")
                        report.append("")
        
        # 优化建议
        report.append("## 💡 优化建议")
        report.append("")
        
        if self.performance_issues:
            # 统计问题类别
            category_counts = defaultdict(int)
            for issue in self.performance_issues:
                category_counts[issue.category] += 1
            
            if category_counts:
                report.append("### 问题分布")
                report.append("")
                
                for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
                    report.append(f"- **{category}**: {count} 个问题")
                
                report.append("")
            
            # 通用优化建议
            report.append("### 通用优化策略")
            report.append("")
            report.append("1. **代码优化**")
            report.append("   - 使用更高效的算法和数据结构")
            report.append("   - 避免不必要的循环和计算")
            report.append("   - 使用内置函数和库函数")
            report.append("")
            report.append("2. **内存优化**")
            report.append("   - 使用生成器代替大列表")
            report.append("   - 及时释放不需要的对象")
            report.append("   - 考虑使用__slots__减少内存占用")
            report.append("")
            report.append("3. **并发优化**")
            report.append("   - 使用多线程处理I/O密集型任务")
            report.append("   - 使用多进程处理CPU密集型任务")
            report.append("   - 考虑异步编程模式")
            report.append("")
        else:
            report.append("暂未发现明显的性能问题，继续保持良好的编码习惯！")
            report.append("")
        
        return '\n'.join(report)
    
    def _generate_json_report(self) -> str:
        """生成JSON格式报告"""
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'project_root': str(self.project_root),
            'profiling_status': self.profiling,
            'metrics_count': len(self.metrics_history),
            'memory_snapshots_count': len(self.memory_snapshots),
            'performance_issues_count': len(self.performance_issues),
            'metrics': [asdict(m) for m in self.metrics_history],
            'memory_snapshots': [asdict(s) for s in self.memory_snapshots],
            'performance_issues': [asdict(i) for i in self.performance_issues]
        }
        
        return json.dumps(report_data, ensure_ascii=False, indent=2)
    
    def _generate_html_report(self) -> str:
        """生成HTML格式报告"""
        # 简化的HTML报告
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>性能分析报告</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
        .metrics {{ display: flex; gap: 20px; margin: 20px 0; }}
        .metric-card {{ background: #fff; border: 1px solid #ddd; padding: 15px; border-radius: 5px; flex: 1; }}
        .issue {{ padding: 10px; margin: 10px 0; border-radius: 5px; }}
        .issue.critical {{ background: #f8d7da; border: 1px solid #f5c6cb; }}
        .issue.high {{ background: #fff3cd; border: 1px solid #ffeaa7; }}
        .issue.medium {{ background: #d1ecf1; border: 1px solid #bee5eb; }}
        .issue.low {{ background: #d4edda; border: 1px solid #c3e6cb; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 性能分析报告</h1>
        <p><strong>生成时间</strong>: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>分析状态</strong>: {'运行中' if self.profiling else '已停止'}</p>
    </div>
"""
        
        # 性能指标
        if self.metrics_history:
            html += """
    <h2>📊 性能指标摘要</h2>
    <div class="metrics">
        <div class="metric-card">
            <h3>函数数量</h3>
            <p>{}</p>
        </div>
        <div class="metric-card">
            <h3>性能问题</h3>
            <p>{}</p>
        </div>
        <div class="metric-card">
            <h3>内存快照</h3>
            <p>{}</p>
        </div>
    </div>
""".format(len(self.metrics_history), len(self.performance_issues), len(self.memory_snapshots))
        
        # 性能问题
        if self.performance_issues:
            html += "<h2>⚠️ 性能问题</h2>"
            
            for issue in self.performance_issues[:10]:
                html += f"""
    <div class="issue {issue.severity}">
        <strong>{issue.function_name}</strong> ({issue.category.upper()})
        <p>{issue.description}</p>
        <p><em>建议: {issue.suggestion}</em></p>
    </div>
"""
        
        html += """
</body>
</html>
"""
        
        return html
    
    def save_report(self, output_format: str = 'markdown', filename: str = None) -> str:
        """保存性能分析报告"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"performance_report_{timestamp}.{output_format}"
        
        report_content = self.generate_performance_report(output_format)
        report_path = self.reports_dir / filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"📄 性能分析报告已保存: {report_path}")
        return str(report_path)

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='YDS-Lab 性能分析工具')
    parser.add_argument('--project-root', help='指定项目根目录路径')
    parser.add_argument('--profile', action='store_true', help='启动性能分析')
    parser.add_argument('--analyze', help='分析指定文件或目录')
    parser.add_argument('--report', action='store_true', help='生成性能报告')
    parser.add_argument('--format', choices=['markdown', 'html', 'json'], default='markdown', help='报告格式')
    parser.add_argument('--output', help='输出文件名')
    parser.add_argument('--benchmark', help='基准测试指定函数')
    parser.add_argument('--memory', type=int, help='监控内存使用（秒）')
    parser.add_argument('--duration', type=int, default=60, help='分析持续时间')
    
    args = parser.parse_args()
    
    analyzer = PerformanceAnalyzer(args.project_root)
    
    # 启动性能分析
    if args.profile:
        print("🚀 启动性能分析...")
        analyzer.start_profiling()
        
        try:
            print(f"⏱️ 分析运行中，持续 {args.duration} 秒...")
            time.sleep(args.duration)
        except KeyboardInterrupt:
            print("\n⏹️ 用户中断分析")
        finally:
            profile_file = analyzer.stop_profiling()
            print(f"✅ 性能分析完成: {profile_file}")
        
        return
    
    # 分析代码
    if args.analyze:
        analyze_path = Path(args.analyze)
        
        if analyze_path.is_file():
            print(f"🔍 分析文件: {analyze_path}")
            issues = analyzer.analyze_code_patterns(str(analyze_path))
            
            if issues:
                print(f"发现 {len(issues)} 个性能问题:")
                for issue in issues:
                    print(f"  {issue.severity.upper()}: {issue.description}")
            else:
                print("✅ 未发现性能问题")
        
        elif analyze_path.is_dir():
            print(f"🔍 分析目录: {analyze_path}")
            results = analyzer.analyze_project(['*.py'])
            
            print(f"分析完成:")
            print(f"  文件数量: {results['files_analyzed']}")
            print(f"  问题总数: {results['total_issues']}")
            
            for severity, count in results['issues_by_severity'].items():
                print(f"  {severity.upper()}: {count}")
        
        else:
            print(f"❌ 路径不存在: {analyze_path}")
        
        return
    
    # 生成报告
    if args.report:
        report_path = analyzer.save_report(args.format, args.output)
        print(f"✅ 报告已生成: {report_path}")
        return
    
    # 内存监控
    if args.memory:
        print(f"💾 开始监控内存使用，持续 {args.memory} 秒...")
        results = analyzer.profile_memory_usage(args.memory)
        
        if 'error' not in results:
            print(f"内存监控完成:")
            print(f"  平均内存: {results['avg_memory'] / (1024*1024):.1f} MB")
            print(f"  最大内存: {results['max_memory'] / (1024*1024):.1f} MB")
            print(f"  内存增长: {results['memory_growth'] / (1024*1024):.1f} MB")
            
            if results['potential_leak']:
                print("⚠️ 检测到潜在内存泄漏")
        else:
            print(f"❌ 内存监控失败: {results['error']}")
        
        return
    
    # 默认显示状态
    print("📊 性能分析器状态")
    print("="*40)
    print(f"项目路径: {analyzer.project_root}")
    print(f"分析状态: {'运行中' if analyzer.profiling else '已停止'}")
    print(f"性能指标: {len(analyzer.metrics_history)} 条")
    print(f"内存快照: {len(analyzer.memory_snapshots)} 个")
    print(f"性能问题: {len(analyzer.performance_issues)} 个")

if __name__ == "__main__":
    main()