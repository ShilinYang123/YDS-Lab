#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YDS-Lab 日志管理工具
提供统一的日志管理、分析、清理和监控功能
适配YDS-Lab项目结构和AI Agent协作需求
"""

import os
import sys
import json
import yaml
import logging
from logging import handlers as logging_handlers
import re
import gzip
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import threading
import time
from collections import defaultdict, Counter
import subprocess

try:
    import colorlog
    COLORLOG_AVAILABLE = True
except ImportError:
    COLORLOG_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

@dataclass
class LogEntry:
    """日志条目"""
    timestamp: datetime
    level: str
    logger: str
    message: str
    file_path: str = ''
    line_number: int = 0
    function: str = ''
    thread_id: str = ''
    process_id: int = 0
    extra_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.extra_data is None:
            self.extra_data = {}

@dataclass
class LogStats:
    """日志统计"""
    total_entries: int = 0
    level_counts: Dict[str, int] = None
    logger_counts: Dict[str, int] = None
    error_patterns: Dict[str, int] = None
    time_range: Tuple[datetime, datetime] = None
    file_sizes: Dict[str, int] = None
    
    def __post_init__(self):
        if self.level_counts is None:
            self.level_counts = {}
        if self.logger_counts is None:
            self.logger_counts = {}
        if self.error_patterns is None:
            self.error_patterns = {}
        if self.file_sizes is None:
            self.file_sizes = {}

@dataclass
class LogAlert:
    """日志告警"""
    id: str
    level: str
    pattern: str
    threshold: int
    time_window: int  # 分钟
    count: int = 0
    last_triggered: Optional[datetime] = None
    enabled: bool = True
    description: str = ''

class LogManager:
    """日志管理器"""
    
    def __init__(self, project_root: str = None):
        """初始化日志管理器"""
        if project_root is None:
            self.project_root = Path(__file__).parent.parent.parent
        else:
            self.project_root = Path(project_root)
        
        self.config_dir = self.project_root / "Struc" / "GeneralOffice" / "config"
        self.logs_dir = self.project_root / "logs"
        self.archive_dir = self.logs_dir / "archive"
        
        # 创建目录
        for directory in [self.logs_dir, self.archive_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # 加载配置
        self.config = self._load_config()
        
        # 初始化状态
        self.loggers = {}
        self.handlers = {}
        self.alerts = {}
        self.monitoring_thread = None
        self.monitoring_active = False
        
        # 设置主日志记录器
        self._setup_main_logger()
        
        # 加载告警规则
        self._load_alerts()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载日志配置"""
        config_file = self.config_dir / "logging_config.yaml"
        
        default_config = {
            'logging': {
                'version': 1,
                'disable_existing_loggers': False,
                'formatters': {
                    'standard': {
                        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        'datefmt': '%Y-%m-%d %H:%M:%S'
                    },
                    'detailed': {
                        'format': '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s',
                        'datefmt': '%Y-%m-%d %H:%M:%S'
                    },
                    'json': {
                        'format': '{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "message": "%(message)s", "file": "%(filename)s", "line": %(lineno)d, "function": "%(funcName)s"}',
                        'datefmt': '%Y-%m-%d %H:%M:%S'
                    },
                    'colored': {
                        'format': '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s%(reset)s',
                        'datefmt': '%Y-%m-%d %H:%M:%S'
                    }
                },
                'handlers': {
                    'console': {
                        'class': 'logging.StreamHandler',
                        'level': 'INFO',
                        'formatter': 'colored' if COLORLOG_AVAILABLE else 'standard',
                        'stream': 'ext://sys.stdout'
                    },
                    'file': {
                        'class': 'logging.handlers.RotatingFileHandler',
                        'level': 'DEBUG',
                        'formatter': 'detailed',
                        'filename': str(self.logs_dir / 'yds_lab.log'),
                        'maxBytes': 10485760,  # 10MB
                        'backupCount': 5,
                        'encoding': 'utf-8'
                    },
                    'error_file': {
                        'class': 'logging.handlers.RotatingFileHandler',
                        'level': 'ERROR',
                        'formatter': 'detailed',
                        'filename': str(self.logs_dir / 'error.log'),
                        'maxBytes': 10485760,  # 10MB
                        'backupCount': 10,
                        'encoding': 'utf-8'
                    },
                    'json_file': {
                        'class': 'logging.handlers.TimedRotatingFileHandler',
                        'level': 'INFO',
                        'formatter': 'json',
                        'filename': str(self.logs_dir / 'yds_lab.json'),
                        'when': 'midnight',
                        'interval': 1,
                        'backupCount': 30,
                        'encoding': 'utf-8'
                    }
                },
                'loggers': {
                    'yds_lab': {
                        'level': 'DEBUG',
                        'handlers': ['console', 'file', 'error_file', 'json_file'],
                        'propagate': False
                    }
                },
                'root': {
                    'level': 'WARNING',
                    'handlers': ['console']
                }
            },
            'management': {
                'max_log_age_days': 30,
                'max_archive_age_days': 90,
                'max_total_size_mb': 1000,
                'compression_enabled': True,
                'auto_cleanup_enabled': True,
                'cleanup_interval_hours': 24
            },
            'analysis': {
                'error_patterns': [
                    r'ERROR',
                    r'CRITICAL',
                    r'Exception',
                    r'Traceback',
                    r'Failed',
                    r'Error:',
                    r'timeout',
                    r'connection.*failed',
                    r'permission.*denied'
                ],
                'warning_patterns': [
                    r'WARNING',
                    r'WARN',
                    r'deprecated',
                    r'slow.*query',
                    r'memory.*usage',
                    r'disk.*space'
                ],
                'performance_patterns': [
                    r'slow.*response',
                    r'high.*cpu',
                    r'memory.*leak',
                    r'database.*slow',
                    r'timeout.*exceeded'
                ]
            },
            'alerts': {
                'enabled': True,
                'check_interval_minutes': 5,
                'email_notifications': False,
                'webhook_notifications': False,
                'default_rules': [
                    {
                        'id': 'high_error_rate',
                        'level': 'ERROR',
                        'pattern': r'ERROR|CRITICAL',
                        'threshold': 10,
                        'time_window': 60,
                        'description': '错误率过高'
                    },
                    {
                        'id': 'memory_warning',
                        'level': 'WARNING',
                        'pattern': r'memory.*usage|memory.*leak',
                        'threshold': 5,
                        'time_window': 30,
                        'description': '内存使用警告'
                    },
                    {
                        'id': 'database_errors',
                        'level': 'ERROR',
                        'pattern': r'database.*error|connection.*failed',
                        'threshold': 3,
                        'time_window': 15,
                        'description': '数据库连接错误'
                    }
                ]
            },
            'monitoring': {
                'enabled': True,
                'watch_directories': [
                    str(self.logs_dir)
                ],
                'file_patterns': ['*.log', '*.json'],
                'real_time_analysis': True,
                'performance_tracking': True
            }
        }
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f)
                    # 深度合并配置
                    self._deep_merge_config(default_config, user_config)
            except Exception as e:
                print(f"⚠️ 加载日志配置失败: {e}")
        
        return default_config
    
    def _deep_merge_config(self, base: Dict, update: Dict):
        """深度合并配置"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge_config(base[key], value)
            else:
                base[key] = value
    
    def _setup_main_logger(self):
        """设置主日志记录器"""
        # 配置日志系统
        logging.config.dictConfig(self.config['logging'])
        
        # 获取主记录器
        self.main_logger = logging.getLogger('yds_lab.log_manager')
        
        # 如果启用了彩色日志
        if COLORLOG_AVAILABLE:
            console_handler = None
            for handler in self.main_logger.handlers:
                if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
                    console_handler = handler
                    break
            
            if console_handler:
                colored_formatter = colorlog.ColoredFormatter(
                    '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s%(reset)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    log_colors={
                        'DEBUG': 'cyan',
                        'INFO': 'green',
                        'WARNING': 'yellow',
                        'ERROR': 'red',
                        'CRITICAL': 'red,bg_white',
                    }
                )
                console_handler.setFormatter(colored_formatter)
    
    def _load_alerts(self):
        """加载告警规则"""
        if not self.config['alerts']['enabled']:
            return
        
        for rule_config in self.config['alerts']['default_rules']:
            alert = LogAlert(
                id=rule_config['id'],
                level=rule_config['level'],
                pattern=rule_config['pattern'],
                threshold=rule_config['threshold'],
                time_window=rule_config['time_window'],
                description=rule_config.get('description', '')
            )
            self.alerts[alert.id] = alert
    
    def get_logger(self, name: str, level: str = 'INFO', 
                   handlers: List[str] = None) -> logging.Logger:
        """获取或创建日志记录器"""
        if name in self.loggers:
            return self.loggers[name]
        
        logger = logging.getLogger(f'yds_lab.{name}')
        logger.setLevel(getattr(logging, level.upper()))
        
        # 添加处理器
        if handlers is None:
            handlers = ['console', 'file']
        
        for handler_name in handlers:
            if handler_name in self.config['logging']['handlers']:
                handler_config = self.config['logging']['handlers'][handler_name]
                handler = self._create_handler(handler_config, name)
                if handler:
                    logger.addHandler(handler)
        
        self.loggers[name] = logger
        return logger
    
    def _create_handler(self, config: Dict[str, Any], logger_name: str) -> Optional[logging.Handler]:
        """创建日志处理器"""
        try:
            handler_class = config['class']
            
            if handler_class == 'logging.StreamHandler':
                handler = logging.StreamHandler()
            elif handler_class == 'logging.handlers.RotatingFileHandler':
                # 为不同的记录器创建不同的文件
                filename = config['filename']
                if logger_name != 'yds_lab':
                    base_path = Path(filename)
                    filename = str(base_path.parent / f"{logger_name}_{base_path.name}")
                
                handler = logging_handlers.RotatingFileHandler(
                    filename=filename,
                    maxBytes=config.get('maxBytes', 10485760),
                    backupCount=config.get('backupCount', 5),
                    encoding=config.get('encoding', 'utf-8')
                )
            elif handler_class == 'logging.handlers.TimedRotatingFileHandler':
                # 为不同的记录器创建不同的文件
                filename = config['filename']
                if logger_name != 'yds_lab':
                    base_path = Path(filename)
                    filename = str(base_path.parent / f"{logger_name}_{base_path.name}")
                
                handler = logging_handlers.TimedRotatingFileHandler(
                    filename=filename,
                    when=config.get('when', 'midnight'),
                    interval=config.get('interval', 1),
                    backupCount=config.get('backupCount', 30),
                    encoding=config.get('encoding', 'utf-8')
                )
            else:
                self.main_logger.warning(f"不支持的处理器类型: {handler_class}")
                return None
            
            # 设置级别
            handler.setLevel(getattr(logging, config.get('level', 'INFO')))
            
            # 设置格式器
            formatter_name = config.get('formatter', 'standard')
            if formatter_name in self.config['logging']['formatters']:
                formatter_config = self.config['logging']['formatters'][formatter_name]
                
                if formatter_name == 'colored' and COLORLOG_AVAILABLE:
                    formatter = colorlog.ColoredFormatter(
                        formatter_config['format'],
                        datefmt=formatter_config.get('datefmt'),
                        log_colors={
                            'DEBUG': 'cyan',
                            'INFO': 'green',
                            'WARNING': 'yellow',
                            'ERROR': 'red',
                            'CRITICAL': 'red,bg_white',
                        }
                    )
                else:
                    formatter = logging.Formatter(
                        formatter_config['format'],
                        datefmt=formatter_config.get('datefmt')
                    )
                
                handler.setFormatter(formatter)
            
            return handler
        
        except Exception as e:
            self.main_logger.error(f"创建处理器失败: {e}")
            return None
    
    def analyze_logs(self, log_files: List[str] = None, 
                    start_time: datetime = None, 
                    end_time: datetime = None) -> LogStats:
        """分析日志文件"""
        if log_files is None:
            log_files = list(self.logs_dir.glob('*.log'))
        else:
            log_files = [Path(f) for f in log_files]
        
        stats = LogStats()
        entries = []
        
        self.main_logger.info(f"开始分析 {len(log_files)} 个日志文件")
        
        for log_file in log_files:
            if not log_file.exists():
                continue
            
            try:
                file_entries = self._parse_log_file(log_file, start_time, end_time)
                entries.extend(file_entries)
                stats.file_sizes[str(log_file)] = log_file.stat().st_size
            except Exception as e:
                self.main_logger.error(f"分析日志文件失败 {log_file}: {e}")
        
        # 统计分析
        stats.total_entries = len(entries)
        
        if entries:
            # 级别统计
            stats.level_counts = Counter(entry.level for entry in entries)
            
            # 记录器统计
            stats.logger_counts = Counter(entry.logger for entry in entries)
            
            # 时间范围
            timestamps = [entry.timestamp for entry in entries]
            stats.time_range = (min(timestamps), max(timestamps))
            
            # 错误模式分析
            stats.error_patterns = self._analyze_error_patterns(entries)
        
        self.main_logger.info(f"日志分析完成，共处理 {stats.total_entries} 条记录")
        return stats
    
    def _parse_log_file(self, log_file: Path, start_time: datetime = None, 
                       end_time: datetime = None) -> List[LogEntry]:
        """解析日志文件"""
        entries = []
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        # 尝试解析JSON格式
                        if line.startswith('{') and line.endswith('}'):
                            entry = self._parse_json_log_line(line)
                        else:
                            # 解析标准格式
                            entry = self._parse_standard_log_line(line)
                        
                        if entry:
                            # 时间过滤
                            if start_time and entry.timestamp < start_time:
                                continue
                            if end_time and entry.timestamp > end_time:
                                continue
                            
                            entries.append(entry)
                    
                    except Exception as e:
                        self.main_logger.debug(f"解析日志行失败 {log_file}:{line_num}: {e}")
        
        except Exception as e:
            self.main_logger.error(f"读取日志文件失败 {log_file}: {e}")
        
        return entries
    
    def _parse_json_log_line(self, line: str) -> Optional[LogEntry]:
        """解析JSON格式日志行"""
        try:
            data = json.loads(line)
            
            timestamp = datetime.strptime(data['timestamp'], '%Y-%m-%d %H:%M:%S')
            
            entry = LogEntry(
                timestamp=timestamp,
                level=data.get('level', 'INFO'),
                logger=data.get('logger', ''),
                message=data.get('message', ''),
                file_path=data.get('file', ''),
                line_number=data.get('line', 0),
                function=data.get('function', ''),
                extra_data=data
            )
            
            return entry
        
        except Exception:
            return None
    
    def _parse_standard_log_line(self, line: str) -> Optional[LogEntry]:
        """解析标准格式日志行"""
        # 标准格式: 2024-01-01 12:00:00 - logger - LEVEL - message
        pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - ([^-]+) - ([^-]+) - (.+)'
        
        match = re.match(pattern, line)
        if not match:
            return None
        
        try:
            timestamp_str, logger, level, message = match.groups()
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            
            entry = LogEntry(
                timestamp=timestamp,
                level=level.strip(),
                logger=logger.strip(),
                message=message.strip()
            )
            
            return entry
        
        except Exception:
            return None
    
    def _analyze_error_patterns(self, entries: List[LogEntry]) -> Dict[str, int]:
        """分析错误模式"""
        error_patterns = {}
        
        all_patterns = (
            self.config['analysis']['error_patterns'] +
            self.config['analysis']['warning_patterns'] +
            self.config['analysis']['performance_patterns']
        )
        
        for pattern_str in all_patterns:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            count = 0
            
            for entry in entries:
                if pattern.search(entry.message):
                    count += 1
            
            if count > 0:
                error_patterns[pattern_str] = count
        
        return error_patterns
    
    def search_logs(self, query: str, log_files: List[str] = None,
                   start_time: datetime = None, end_time: datetime = None,
                   level: str = None, logger: str = None) -> List[LogEntry]:
        """搜索日志"""
        if log_files is None:
            log_files = list(self.logs_dir.glob('*.log'))
        else:
            log_files = [Path(f) for f in log_files]
        
        results = []
        query_pattern = re.compile(query, re.IGNORECASE)
        
        for log_file in log_files:
            if not log_file.exists():
                continue
            
            try:
                entries = self._parse_log_file(log_file, start_time, end_time)
                
                for entry in entries:
                    # 级别过滤
                    if level and entry.level != level:
                        continue
                    
                    # 记录器过滤
                    if logger and entry.logger != logger:
                        continue
                    
                    # 查询匹配
                    if query_pattern.search(entry.message):
                        results.append(entry)
            
            except Exception as e:
                self.main_logger.error(f"搜索日志文件失败 {log_file}: {e}")
        
        return results
    
    def cleanup_logs(self, dry_run: bool = False) -> Dict[str, Any]:
        """清理日志文件"""
        cleanup_result = {
            'deleted_files': [],
            'archived_files': [],
            'compressed_files': [],
            'total_space_freed': 0,
            'errors': []
        }
        
        max_age = timedelta(days=self.config['management']['max_log_age_days'])
        max_archive_age = timedelta(days=self.config['management']['max_archive_age_days'])
        max_total_size = self.config['management']['max_total_size_mb'] * 1024 * 1024
        compression_enabled = self.config['management']['compression_enabled']
        
        current_time = datetime.now()
        
        # 获取所有日志文件
        log_files = []
        for pattern in ['*.log', '*.log.*', '*.json', '*.json.*']:
            log_files.extend(self.logs_dir.glob(pattern))
        
        # 按修改时间排序
        log_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        
        total_size = 0
        
        for log_file in log_files:
            try:
                file_stat = log_file.stat()
                file_age = current_time - datetime.fromtimestamp(file_stat.st_mtime)
                file_size = file_stat.st_size
                
                # 检查是否需要删除
                if file_age > max_age:
                    if not dry_run:
                        log_file.unlink()
                    cleanup_result['deleted_files'].append(str(log_file))
                    cleanup_result['total_space_freed'] += file_size
                    continue
                
                # 检查是否需要压缩
                if (compression_enabled and 
                    not log_file.name.endswith('.gz') and 
                    file_age > timedelta(days=1) and
                    file_size > 1024 * 1024):  # 1MB
                    
                    if not dry_run:
                        compressed_file = self._compress_log_file(log_file)
                        if compressed_file:
                            cleanup_result['compressed_files'].append(str(compressed_file))
                            cleanup_result['total_space_freed'] += file_size - compressed_file.stat().st_size
                    else:
                        cleanup_result['compressed_files'].append(str(log_file) + '.gz')
                
                # 检查总大小限制
                total_size += file_size
                if total_size > max_total_size:
                    # 删除最旧的文件
                    if not dry_run:
                        log_file.unlink()
                    cleanup_result['deleted_files'].append(str(log_file))
                    cleanup_result['total_space_freed'] += file_size
            
            except Exception as e:
                error_msg = f"处理文件失败 {log_file}: {e}"
                cleanup_result['errors'].append(error_msg)
                self.main_logger.error(error_msg)
        
        # 清理归档目录
        if self.archive_dir.exists():
            for archive_file in self.archive_dir.glob('*'):
                try:
                    file_stat = archive_file.stat()
                    file_age = current_time - datetime.fromtimestamp(file_stat.st_mtime)
                    
                    if file_age > max_archive_age:
                        if not dry_run:
                            archive_file.unlink()
                        cleanup_result['deleted_files'].append(str(archive_file))
                        cleanup_result['total_space_freed'] += file_stat.st_size
                
                except Exception as e:
                    error_msg = f"处理归档文件失败 {archive_file}: {e}"
                    cleanup_result['errors'].append(error_msg)
                    self.main_logger.error(error_msg)
        
        self.main_logger.info(f"日志清理完成，释放空间: {cleanup_result['total_space_freed'] / 1024 / 1024:.2f} MB")
        return cleanup_result
    
    def _compress_log_file(self, log_file: Path) -> Optional[Path]:
        """压缩日志文件"""
        try:
            compressed_file = log_file.with_suffix(log_file.suffix + '.gz')
            
            with open(log_file, 'rb') as f_in:
                with gzip.open(compressed_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # 删除原文件
            log_file.unlink()
            
            return compressed_file
        
        except Exception as e:
            self.main_logger.error(f"压缩日志文件失败 {log_file}: {e}")
            return None
    
    def start_monitoring(self):
        """启动日志监控"""
        if not self.config['monitoring']['enabled']:
            self.main_logger.info("日志监控已禁用")
            return
        
        if self.monitoring_active:
            self.main_logger.warning("日志监控已在运行")
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        self.main_logger.info("日志监控已启动")
    
    def stop_monitoring(self):
        """停止日志监控"""
        if not self.monitoring_active:
            return
        
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        self.main_logger.info("日志监控已停止")
    
    def _monitoring_loop(self):
        """监控循环"""
        check_interval = self.config['alerts']['check_interval_minutes'] * 60
        
        while self.monitoring_active:
            try:
                # 检查告警
                self._check_alerts()
                
                # 自动清理
                if self.config['management']['auto_cleanup_enabled']:
                    cleanup_interval = self.config['management']['cleanup_interval_hours'] * 3600
                    if hasattr(self, '_last_cleanup'):
                        if time.time() - self._last_cleanup > cleanup_interval:
                            self.cleanup_logs()
                            self._last_cleanup = time.time()
                    else:
                        self._last_cleanup = time.time()
                
                time.sleep(check_interval)
            
            except Exception as e:
                self.main_logger.error(f"监控循环异常: {e}")
                time.sleep(60)  # 出错时等待1分钟
    
    def _check_alerts(self):
        """检查告警条件"""
        if not self.config['alerts']['enabled']:
            return
        
        current_time = datetime.now()
        
        for alert_id, alert in self.alerts.items():
            if not alert.enabled:
                continue
            
            try:
                # 获取时间窗口内的日志
                start_time = current_time - timedelta(minutes=alert.time_window)
                
                # 搜索匹配的日志条目
                matching_entries = self.search_logs(
                    query=alert.pattern,
                    start_time=start_time,
                    end_time=current_time,
                    level=alert.level if alert.level != 'ALL' else None
                )
                
                count = len(matching_entries)
                
                # 检查是否触发告警
                if count >= alert.threshold:
                    # 检查冷却时间
                    if (alert.last_triggered is None or 
                        current_time - alert.last_triggered > timedelta(minutes=alert.time_window)):
                        
                        self._trigger_alert(alert, count, matching_entries)
                        alert.last_triggered = current_time
            
            except Exception as e:
                self.main_logger.error(f"检查告警失败 {alert_id}: {e}")
    
    def _trigger_alert(self, alert: LogAlert, count: int, entries: List[LogEntry]):
        """触发告警"""
        message = f"告警触发: {alert.description} (ID: {alert.id})"
        message += f"\n匹配条目数: {count} (阈值: {alert.threshold})"
        message += f"\n时间窗口: {alert.time_window} 分钟"
        message += f"\n模式: {alert.pattern}"
        
        if entries:
            message += "\n最近的匹配条目:"
            for entry in entries[-3:]:  # 显示最近3条
                message += f"\n  {entry.timestamp} - {entry.level} - {entry.message[:100]}"
        
        self.main_logger.warning(message)
        
        # 发送通知
        self._send_alert_notification(alert, message)
    
    def _send_alert_notification(self, alert: LogAlert, message: str):
        """发送告警通知"""
        # 这里可以实现邮件、Webhook等通知方式
        # 目前只记录到日志
        self.main_logger.critical(f"ALERT: {message}")
    
    def export_logs(self, output_file: str, format_type: str = 'json',
                   start_time: datetime = None, end_time: datetime = None,
                   level: str = None, logger: str = None) -> bool:
        """导出日志"""
        try:
            # 获取日志条目
            entries = []
            for log_file in self.logs_dir.glob('*.log'):
                file_entries = self._parse_log_file(log_file, start_time, end_time)
                entries.extend(file_entries)
            
            # 过滤
            if level:
                entries = [e for e in entries if e.level == level]
            if logger:
                entries = [e for e in entries if e.logger == logger]
            
            # 排序
            entries.sort(key=lambda e: e.timestamp)
            
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if format_type == 'json':
                data = [asdict(entry) for entry in entries]
                # 转换datetime为字符串
                for item in data:
                    item['timestamp'] = item['timestamp'].isoformat()
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            
            elif format_type == 'csv' and PANDAS_AVAILABLE:
                data = [asdict(entry) for entry in entries]
                df = pd.DataFrame(data)
                df.to_csv(output_path, index=False, encoding='utf-8')
            
            elif format_type == 'txt':
                with open(output_path, 'w', encoding='utf-8') as f:
                    for entry in entries:
                        f.write(f"{entry.timestamp} - {entry.logger} - {entry.level} - {entry.message}\n")
            
            else:
                raise ValueError(f"不支持的导出格式: {format_type}")
            
            self.main_logger.info(f"日志导出完成: {output_path}")
            return True
        
        except Exception as e:
            self.main_logger.error(f"导出日志失败: {e}")
            return False
    
    def get_log_stats(self) -> Dict[str, Any]:
        """获取日志统计信息"""
        stats = self.analyze_logs()
        
        # 文件信息
        log_files = list(self.logs_dir.glob('*.log'))
        total_size = sum(f.stat().st_size for f in log_files if f.exists())
        
        return {
            'total_entries': stats.total_entries,
            'level_counts': stats.level_counts,
            'logger_counts': stats.logger_counts,
            'error_patterns': stats.error_patterns,
            'time_range': stats.time_range,
            'file_count': len(log_files),
            'total_size_mb': total_size / 1024 / 1024,
            'file_sizes': {k: v / 1024 / 1024 for k, v in stats.file_sizes.items()},
            'alerts_count': len(self.alerts),
            'monitoring_active': self.monitoring_active
        }

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='YDS-Lab 日志管理工具')
    parser.add_argument('--project-root', help='指定项目根目录路径')
    parser.add_argument('--analyze', action='store_true', help='分析日志文件')
    parser.add_argument('--search', help='搜索日志内容')
    parser.add_argument('--cleanup', action='store_true', help='清理日志文件')
    parser.add_argument('--dry-run', action='store_true', help='模拟运行（不实际删除文件）')
    parser.add_argument('--export', help='导出日志到文件')
    parser.add_argument('--format', choices=['json', 'csv', 'txt'], default='json', help='导出格式')
    parser.add_argument('--level', help='过滤日志级别')
    parser.add_argument('--logger', help='过滤记录器名称')
    parser.add_argument('--start-time', help='开始时间 (YYYY-MM-DD HH:MM:SS)')
    parser.add_argument('--end-time', help='结束时间 (YYYY-MM-DD HH:MM:SS)')
    parser.add_argument('--monitor', action='store_true', help='启动监控模式')
    parser.add_argument('--stats', action='store_true', help='显示日志统计')
    
    args = parser.parse_args()
    
    manager = LogManager(args.project_root)
    
    # 解析时间参数
    start_time = None
    end_time = None
    
    if args.start_time:
        try:
            start_time = datetime.strptime(args.start_time, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            print("❌ 开始时间格式错误，请使用 YYYY-MM-DD HH:MM:SS")
            return
    
    if args.end_time:
        try:
            end_time = datetime.strptime(args.end_time, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            print("❌ 结束时间格式错误，请使用 YYYY-MM-DD HH:MM:SS")
            return
    
    # 分析日志
    if args.analyze:
        print("📊 分析日志文件")
        stats = manager.analyze_logs(start_time=start_time, end_time=end_time)
        
        print("="*50)
        print(f"总条目数: {stats.total_entries}")
        print(f"时间范围: {stats.time_range[0]} - {stats.time_range[1]}" if stats.time_range else "无数据")
        
        print("\n级别统计:")
        for level, count in stats.level_counts.items():
            print(f"  {level}: {count}")
        
        print("\n记录器统计:")
        for logger, count in sorted(stats.logger_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {logger}: {count}")
        
        print("\n错误模式:")
        for pattern, count in sorted(stats.error_patterns.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {pattern}: {count}")
        
        return
    
    # 搜索日志
    if args.search:
        print(f"🔍 搜索日志: {args.search}")
        results = manager.search_logs(
            query=args.search,
            start_time=start_time,
            end_time=end_time,
            level=args.level,
            logger=args.logger
        )
        
        print(f"找到 {len(results)} 条匹配记录:")
        for entry in results[-20:]:  # 显示最近20条
            print(f"{entry.timestamp} - {entry.logger} - {entry.level} - {entry.message}")
        
        return
    
    # 清理日志
    if args.cleanup:
        print("🧹 清理日志文件")
        result = manager.cleanup_logs(dry_run=args.dry_run)
        
        print("="*50)
        print(f"删除文件: {len(result['deleted_files'])}")
        print(f"压缩文件: {len(result['compressed_files'])}")
        print(f"释放空间: {result['total_space_freed'] / 1024 / 1024:.2f} MB")
        
        if result['errors']:
            print(f"错误: {len(result['errors'])}")
            for error in result['errors'][:5]:
                print(f"  {error}")
        
        return
    
    # 导出日志
    if args.export:
        print(f"📤 导出日志到: {args.export}")
        success = manager.export_logs(
            output_file=args.export,
            format_type=args.format,
            start_time=start_time,
            end_time=end_time,
            level=args.level,
            logger=args.logger
        )
        
        if success:
            print("✅ 导出成功")
        else:
            print("❌ 导出失败")
        
        return
    
    # 显示统计
    if args.stats:
        print("📈 日志统计信息")
        stats = manager.get_log_stats()
        
        print("="*50)
        print(f"总条目数: {stats['total_entries']}")
        print(f"文件数量: {stats['file_count']}")
        print(f"总大小: {stats['total_size_mb']:.2f} MB")
        print(f"告警规则: {stats['alerts_count']}")
        print(f"监控状态: {'运行中' if stats['monitoring_active'] else '已停止'}")
        
        print("\n级别分布:")
        for level, count in stats['level_counts'].items():
            print(f"  {level}: {count}")
        
        return
    
    # 监控模式
    if args.monitor:
        print("👁️ 启动日志监控")
        manager.start_monitoring()
        
        try:
            print("监控运行中，按 Ctrl+C 停止...")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n停止监控...")
            manager.stop_monitoring()
        
        return
    
    # 默认显示状态
    print("📋 日志管理器状态")
    print("="*40)
    print(f"项目路径: {manager.project_root}")
    print(f"日志目录: {manager.logs_dir}")
    print(f"归档目录: {manager.archive_dir}")
    
    stats = manager.get_log_stats()
    print(f"日志文件: {stats['file_count']} 个")
    print(f"总大小: {stats['total_size_mb']:.2f} MB")
    print(f"监控状态: {'运行中' if stats['monitoring_active'] else '已停止'}")

if __name__ == "__main__":
    main()