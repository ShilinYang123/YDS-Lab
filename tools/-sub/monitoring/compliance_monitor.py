#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目合规性监控系统（升级版）
自动监控项目目录和文件操作，检测违规行为并记录
支持日期一致性检查和自动修复功能
"""

import os
import sys
import json
import time
import shutil
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import re


@dataclass
class ComplianceViolation:
    """合规性违规记录"""
    violation_type: str
    file_path: str
    description: str
    severity: str = "warning"  # info, warning, error
    timestamp: datetime = None
    resolved: bool = False
    resolution_action: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data
    
    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.violation_type}: {self.description} ({self.file_path})"


class DateConsistencyChecker:
    """日期一致性检查器（升级版）"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.current_date = datetime.now().strftime('%Y-%m-%d')
        self.current_year = datetime.now().year
        
        # 日期格式模式
        self.date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{4}/\d{2}/\d{2}',  # YYYY/MM/DD
            r'\d{4}\.\d{2}\.\d{2}',  # YYYY.MM.DD
            r'\d{4}年\d{1,2}月\d{1,2}日',  # 中文日期
            r'\d{2}-\d{2}-\d{4}',  # MM-DD-YYYY
            r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
        ]
        
        # 历史日期阈值（超过这个天数的日期被认为是历史日期）
        self.history_threshold_days = 30
        
    def check_file_dates(self, file_path: Path) -> List[str]:
        """检查文件中的日期一致性"""
        issues = []
        
        if not file_path.exists() or not file_path.is_file():
            return issues
        
        # 只检查文本文件
        if not self._is_text_file(file_path):
            return issues
        
        try:
            # 尝试多种编码读取文件
            content = self._read_file_with_encoding(file_path)
            if content is None:
                return issues
            
            # 检查文件名中的日期
            filename_issues = self._check_filename_dates(file_path)
            issues.extend(filename_issues)
            
            # 检查文件内容中的日期
            content_issues = self._check_content_dates(content, file_path)
            issues.extend(content_issues)
            
        except Exception as e:
            issues.append(f"读取文件失败: {str(e)}")
        
        return issues
    
    def _is_text_file(self, file_path: Path) -> bool:
        """判断是否为文本文件"""
        text_extensions = {
            '.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.yaml', '.yml',
            '.xml', '.csv', '.log', '.conf', '.cfg', '.ini', '.sh', '.bat', '.ps1',
            '.sql', '.php', '.java', '.cpp', '.c', '.h', '.hpp', '.go', '.rs',
            '.ts', '.jsx', '.tsx', '.vue', '.svelte', '.rb', '.pl', '.r', '.m',
            '.tex', '.bib', '.rst', '.adoc', '.org', '.wiki'
        }
        return file_path.suffix.lower() in text_extensions
    
    def _read_file_with_encoding(self, file_path: Path) -> Optional[str]:
        """使用多种编码尝试读取文件"""
        encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'cp1252', 'latin-1']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except (UnicodeDecodeError, UnicodeError):
                continue
            except Exception:
                break
        
        return None
    
    def _check_filename_dates(self, file_path: Path) -> List[str]:
        """检查文件名中的日期"""
        issues = []
        filename = file_path.name
        
        # 查找文件名中的日期
        for pattern in self.date_patterns:
            matches = re.findall(pattern, filename)
            for match in matches:
                if self._is_historical_date(match):
                    issues.append(f"文件名包含历史日期: {match}")
        
        return issues
    
    def _check_content_dates(self, content: str, file_path: Path) -> List[str]:
        """检查文件内容中的日期"""
        issues = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # 跳过注释行和空行
            if self._is_comment_line(line, file_path.suffix):
                continue
            
            # 查找行中的日期
            for pattern in self.date_patterns:
                matches = re.findall(pattern, line)
                for match in matches:
                    if self._is_historical_date(match):
                        issues.append(f"第{line_num}行包含历史日期: {match}")
        
        return issues
    
    def _is_comment_line(self, line: str, file_extension: str) -> bool:
        """判断是否为注释行"""
        line = line.strip()
        if not line:
            return True
        
        # 根据文件类型判断注释
        comment_patterns = {
            '.py': ['#'],
            '.js': ['//', '/*', '*'],
            '.html': ['<!--'],
            '.css': ['/*', '*'],
            '.yaml': ['#'],
            '.yml': ['#'],
            '.sh': ['#'],
            '.bat': ['REM', 'rem', '::'],
            '.ps1': ['#'],
            '.sql': ['--', '/*'],
            '.md': ['<!--'],
        }
        
        patterns = comment_patterns.get(file_extension.lower(), [])
        for pattern in patterns:
            if line.startswith(pattern):
                return True
        
        return False
    
    def _is_historical_date(self, date_str: str) -> bool:
        """判断是否为历史日期"""
        try:
            # 解析不同格式的日期
            parsed_date = self._parse_date(date_str)
            if parsed_date is None:
                return False
            
            # 计算与当前日期的差异
            current = datetime.now().date()
            diff = (current - parsed_date).days
            
            # 超过阈值的日期被认为是历史日期
            return diff > self.history_threshold_days
            
        except Exception:
            return False
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """解析日期字符串"""
        date_formats = [
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%Y.%m.%d',
            '%m-%d-%Y',
            '%m/%d/%Y',
        ]
        
        # 处理中文日期
        if '年' in date_str and '月' in date_str and '日' in date_str:
            try:
                # 提取年月日数字
                year_match = re.search(r'(\d{4})年', date_str)
                month_match = re.search(r'(\d{1,2})月', date_str)
                day_match = re.search(r'(\d{1,2})日', date_str)
                
                if year_match and month_match and day_match:
                    year = int(year_match.group(1))
                    month = int(month_match.group(1))
                    day = int(day_match.group(1))
                    return datetime(year, month, day).date()
            except Exception:
                pass
        
        # 尝试标准格式
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        return None
    
    def suggest_date_fix(self, file_path: Path) -> List[str]:
        """建议日期修复方案"""
        suggestions = []
        
        # 基本建议
        suggestions.append(f"将历史日期更新为当前日期: {self.current_date}")
        
        # 根据文件类型提供具体建议
        if file_path.suffix.lower() == '.md':
            suggestions.append("更新文档的创建日期和修改日期")
        elif file_path.suffix.lower() in ['.py', '.js', '.java']:
            suggestions.append("更新代码文件的版权日期和修改日期")
        elif file_path.suffix.lower() in ['.yaml', '.yml', '.json']:
            suggestions.append("更新配置文件的时间戳字段")
        
        return suggestions


class ComplianceChecker:
    """合规性检查器"""
    
    def __init__(self, project_root: Path, config: Dict):
        self.project_root = project_root
        self.config = config
        
        # 加载规则配置
        self.rules = config.get("compliance", {}).get("rules", {})
        
        # 受保护的文件和目录
        self.protected_patterns = self.rules.get("protected_files", [
            "*.md",
            "docs/**",
            "*.yaml",
            "*.yml",
            "config/**"
        ])
        
        # 禁止的文件模式
        self.forbidden_patterns = self.rules.get("forbidden_files", [
            "*.tmp",
            "*.temp",
            "*.bak",
            "*.old",
            "desktop.ini",
            "Thumbs.db",
            ".DS_Store"
        ])
        
        # 命名规范
        self.naming_rules = self.rules.get("naming", {})
    
    def check_file_operation(self, file_path: str, operation: str) -> Tuple[bool, List[str]]:
        """检查文件操作是否合规"""
        messages = []
        passed = True
        
        path = Path(file_path)
        
        # 检查是否为受保护文件
        if operation in ["modify", "delete"] and self._is_protected_file(path):
            messages.append(f"操作受保护文件: {file_path}")
            passed = False
        
        # 检查是否为禁止的文件
        if operation == "create" and self._is_forbidden_file(path):
            messages.append(f"创建禁止的文件类型: {file_path}")
            passed = False
        
        # 检查文件位置
        if not self._is_valid_location(path):
            messages.append(f"文件位置不符合项目结构: {file_path}")
            passed = False
        
        return passed, messages
    
    def _is_protected_file(self, path: Path) -> bool:
        """检查是否为受保护文件"""
        for pattern in self.protected_patterns:
            if path.match(pattern):
                return True
        return False
    
    def _is_forbidden_file(self, path: Path) -> bool:
        """检查是否为禁止的文件"""
        for pattern in self.forbidden_patterns:
            if path.match(pattern):
                return True
        return False
    
    def _is_valid_location(self, path: Path) -> bool:
        """检查文件位置是否有效"""
        # 检查是否在项目根目录下
        try:
            path.relative_to(self.project_root)
        except ValueError:
            return False
        
        # 检查是否在允许的目录中
        allowed_dirs = self.rules.get("allowed_directories", [])
        if allowed_dirs:
            for allowed_dir in allowed_dirs:
                allowed_path = self.project_root / allowed_dir
                try:
                    path.relative_to(allowed_path)
                    return True
                except ValueError:
                    continue
            return False
        
        return True
    
    def _check_naming_convention(self, path: Path, messages: List[str]) -> bool:
        """检查命名规范"""
        passed = True
        filename = path.name
        
        # 检查文件名长度
        max_length = self.naming_rules.get("max_filename_length", 255)
        if len(filename) > max_length:
            messages.append(f"文件名过长 (>{max_length}字符)")
            passed = False
        
        # 检查非法字符
        illegal_chars = self.naming_rules.get("illegal_chars", ['<', '>', ':', '"', '|', '?', '*'])
        for char in illegal_chars:
            if char in filename:
                messages.append(f"文件名包含非法字符: {char}")
                passed = False
        
        # 检查文件扩展名
        if path.suffix:
            allowed_extensions = self.naming_rules.get("allowed_extensions", [])
            if allowed_extensions and path.suffix.lower() not in allowed_extensions:
                messages.append(f"不允许的文件扩展名: {path.suffix}")
                passed = False
        
        return passed


class ComplianceFileSystemHandler(FileSystemEventHandler):
    """文件系统事件处理器"""
    
    def __init__(self, monitor):
        self.monitor = monitor
        self.checker = monitor.checker
        self.date_checker = DateConsistencyChecker(monitor.project_root)
        
        # 忽略的文件模式
        self.ignore_patterns = [
            "*.log",
            "*.tmp",
            "*~",
            ".git/**",
            "__pycache__/**",
            "node_modules/**",
            ".vscode/**",
            ".idea/**"
        ]
    
    def on_created(self, event):
        """文件创建事件"""
        if event.is_directory:
            return
        
        if self._should_ignore_file(event.src_path):
            return
        
        # 检查文件创建是否合规
        passed, messages = self.checker.check_file_operation(event.src_path, "create")
        if not passed:
            violation = ComplianceViolation(
                violation_type="unauthorized_file_creation",
                file_path=event.src_path,
                description=f"未授权的文件创建: {'; '.join(messages)}",
                severity="warning"
            )
            self.monitor.record_violation(violation)
        
        # 检查日期一致性
        self._check_file_dates(event.src_path)
    
    def on_modified(self, event):
        """文件修改事件"""
        if event.is_directory:
            return
        
        if self._should_ignore_file(event.src_path):
            return
        
        # 检查文件修改是否合规
        passed, messages = self.checker.check_file_operation(event.src_path, "modify")
        if not passed:
            violation = ComplianceViolation(
                violation_type="protected_file_modification",
                file_path=event.src_path,
                description=f"受保护文件被修改: {'; '.join(messages)}",
                severity="error"
            )
            self.monitor.record_violation(violation)
        
        # 检查日期一致性
        self._check_file_dates(event.src_path)
    
    def on_deleted(self, event):
        """文件删除事件"""
        if event.is_directory:
            return
        
        if self._should_ignore_file(event.src_path):
            return
        
        # 检查文件删除是否合规
        passed, messages = self.checker.check_file_operation(event.src_path, "delete")
        if not passed:
            violation = ComplianceViolation(
                violation_type="important_file_deletion",
                file_path=event.src_path,
                description=f"重要文件被删除: {'; '.join(messages)}",
                severity="error"
            )
            self.monitor.record_violation(violation)
    
    def _should_ignore_file(self, file_path: str) -> bool:
        """检查是否应该忽略文件"""
        path = Path(file_path)
        
        for pattern in self.ignore_patterns:
            if path.match(pattern):
                return True
        
        return False
    
    def _check_file_dates(self, file_path: str):
        """检查文件日期一致性"""
        try:
            path = Path(file_path)
            date_issues = self.date_checker.check_file_dates(path)
            
            if date_issues:
                violation = ComplianceViolation(
                    violation_type="date_consistency_violation",
                    file_path=file_path,
                    description=f"日期一致性问题: {'; '.join(date_issues)}",
                    severity="warning"
                )
                violation.date_issues = date_issues
                violation.suggested_fixes = self.date_checker.suggest_date_fix(path)
                self.monitor.record_violation(violation)
        except Exception as e:
            self.monitor.logger.error(f"检查文件日期时发生错误: {e}")


class ComplianceMonitor:
    """合规性监控器（升级版）"""
    
    def __init__(self, project_root: str = None):
        # 项目根目录
        if project_root is None:
            project_root = os.environ.get("YDS_PROJECT_ROOT", "s:/YDS-Lab")
        self.project_root = Path(project_root)
        
        # 配置日志
        self.logger = self._setup_logging()
        
        # 加载配置
        self.config = self._load_config()
        
        # 初始化组件
        self.checker = ComplianceChecker(self.project_root, self.config)
        self.handler = ComplianceFileSystemHandler(self)
        self.observer = None
        
        # 违规记录
        self.violations: List[ComplianceViolation] = []
        self.violations_file = self.project_root / "logs" / "violations.json"
        
        # 统计信息
        self.stats = {
            "start_time": None,
            "total_violations": 0,
            "resolved_violations": 0
        }
        
        # PID 文件路径
        self.pid_file = self.project_root / "logs" / "compliance_monitor.pid"
        
        # 加载现有违规记录
        self._load_violations()
    
    def _setup_logging(self) -> logging.Logger:
        """设置日志"""
        logger = logging.getLogger("compliance_monitor")
        logger.setLevel(logging.INFO)
        
        # 创建日志目录
        log_dir = self.project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        
        # 文件处理器
        file_handler = logging.FileHandler(
            log_dir / "compliance_monitor.log",
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _load_config(self) -> Dict:
        """加载配置"""
        config_file = self.project_root / "Struc" / "GeneralOffice" / "config" / "compliance_config.yaml"
        
        # 默认配置
        default_config = {
            "compliance": {
                "monitoring": {
                    "enabled": True,
                    "check_interval": 300
                },
                "rules": {
                    "protected_files": [
                        "*.md",
                        "docs/**",
                        "*.yaml",
                        "*.yml",
                        "config/**"
                    ],
                    "forbidden_files": [
                        "*.tmp",
                        "*.temp",
                        "*.bak",
                        "*.old",
                        "desktop.ini",
                        "Thumbs.db",
                        ".DS_Store"
                    ],
                    "naming": {
                        "max_filename_length": 255,
                        "illegal_chars": ['<', '>', ':', '"', '|', '?', '*']
                    }
                }
            },
            "notifications": {
                "violations": {
                    "enabled": True,
                    "methods": ["log", "console"]
                }
            }
        }
        
        if config_file.exists():
            try:
                import yaml
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f)
                    # 合并配置
                    default_config.update(user_config)
            except Exception as e:
                self.logger.warning(f"加载配置文件失败，使用默认配置: {e}")
        
        return default_config
    
    def _write_pid_file(self):
        """写入 PID 文件"""
        try:
            self.pid_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.pid_file, 'w') as f:
                f.write(str(os.getpid()))
        except Exception as e:
            self.logger.error(f"写入 PID 文件失败: {e}")
    
    def _remove_pid_file(self):
        """移除 PID 文件"""
        try:
            if self.pid_file.exists():
                self.pid_file.unlink()
        except Exception as e:
            self.logger.error(f"移除 PID 文件失败: {e}")
    
    def _read_pid_file(self) -> Optional[int]:
        """读取 PID 文件"""
        try:
            if self.pid_file.exists():
                with open(self.pid_file, 'r') as f:
                    return int(f.read().strip())
        except Exception:
            pass
        return None
    
    def _is_monitor_process_active(self, pid: int) -> bool:
        """检查监控进程是否活跃"""
        try:
            import psutil  # type: ignore
            return psutil.pid_exists(pid)
        except ImportError:
            # 如果没有 psutil，使用系统调用
            try:
                os.kill(pid, 0)
                return True
            except OSError:
                return False
    
    def _write_json_atomic(self, file_path: Path, data):
        """原子写入 JSON 文件"""
        temp_file = file_path.with_suffix('.tmp')
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            temp_file.replace(file_path)
        except Exception as e:
            if temp_file.exists():
                temp_file.unlink()
            raise e
    
    def _load_violations(self):
        """加载违规记录"""
        if not self.violations_file.exists():
            return

        data = None
        last_error = None
        
        # 尝试多种编码加载
        for enc in ['utf-8', 'utf-8-sig', 'gbk', 'cp1252']:
            try:
                with open(self.violations_file, 'r', encoding=enc) as f:
                    data = json.load(f)
                    if data is not None:
                        self.logger.info(f"使用编码 {enc} 成功加载违规记录：{self.violations_file}")
                        break
            except UnicodeDecodeError as e:
                last_error = e
                self.logger.warning(f"使用编码 {enc} 读取违规记录失败（UnicodeDecodeError）: {e}")
                continue
            except json.JSONDecodeError as e:
                last_error = e
                self.logger.warning(f"使用编码 {enc} 解析违规记录JSON失败: {e}")
                continue
            except Exception as e:
                last_error = e
                self.logger.warning(f"使用编码 {enc} 加载违规记录时发生异常: {e}")
                continue

        if data is None:
            # 尝试自动修复损坏的 JSON 文件
            repaired = self._repair_violations_file(write_back=True)
            if repaired is None:
                # 修复失败才进行一次性备份，避免频繁备份
                try:
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                    backup_path = self.violations_file.with_suffix(f'.{timestamp}.bak')
                    shutil.copy2(self.violations_file, backup_path)
                    self.logger.error(
                        f"无法加载违规记录（最后错误: {last_error}），且自动修复失败。已备份原文件至: {backup_path}，将从空记录继续。"
                    )
                except Exception as be:
                    self.logger.error(f"违规记录加载失败且备份也失败: {be}；最后错误: {last_error}")
                # 保持 self.violations 为空，允许监控继续运行
                return
            else:
                data = repaired

        # 正常加载数据，构建对象
        try:
            # 支持顶层是对象且包含 violations 字段的情况
            if isinstance(data, dict) and 'violations' in data:
                data_list = data.get('violations', [])
            else:
                data_list = data if isinstance(data, list) else []

            for item in data_list:
                # 跳过非字典项
                if not isinstance(item, dict):
                    continue
                violation = ComplianceViolation(
                    violation_type=item.get("violation_type", "unknown"),
                    file_path=item.get("file_path", ""),
                    description=item.get("description", ""),
                    severity=item.get("severity", "warning")
                )
                try:
                    violation.timestamp = datetime.fromisoformat(item.get("timestamp")) if item.get("timestamp") else datetime.now()
                except Exception:
                    violation.timestamp = datetime.now()
                violation.resolved = item.get("resolved", False)
                violation.resolution_action = item.get("resolution_action")
                self.violations.append(violation)
        except Exception as e:
            self.logger.error(f"违规记录数据转换失败: {e}")
    
    def _save_violations(self):
        """保存违规记录"""
        try:
            data = [violation.to_dict() for violation in self.violations]
            # 使用原子写入，避免中途失败产生半截 JSON
            self._write_json_atomic(self.violations_file, data)
        except Exception as e:
            self.logger.error(f"保存违规记录失败: {e}")

    def _repair_violations_file(self, write_back: bool = True):
        """修复损坏的 violations.json 并返回解析后的列表。

        处理场景：
        - 非 UTF-8 编码、BOM、混合编码
        - 末尾逗号、注释、NDJSON（每行一个 JSON）
        - 连续对象无逗号连接（}{）
        """
        if not self.violations_file.exists():
            return []

        # 1. 尝试以多编码读取原始文本
        raw_text = None
        for enc in ['utf-8', 'utf-8-sig', 'gbk', 'cp1252', 'latin-1']:
            try:
                with open(self.violations_file, 'r', encoding=enc) as f:
                    raw_text = f.read()
                    break
            except Exception:
                continue

        if raw_text is None:
            self.logger.error("修复失败：无法读取 violations.json")
            return None

        # 2. 直接尝试标准 JSON 解析
        try:
            parsed = json.loads(raw_text)
            # 如果本身可解析，且需要写回为规范化 UTF-8
            if write_back:
                normalized = parsed
                # 如果顶层不是列表但包含 violations 字段，取其列表写回
                if isinstance(parsed, dict) and 'violations' in parsed:
                    normalized = parsed['violations']
                self._write_json_atomic(self.violations_file, normalized)
            return parsed if isinstance(parsed, list) else parsed
        except Exception:
            pass

        # 3. 清理文本：移除 BOM、注释、修正尾随逗号
        text = raw_text.replace('\ufeff', '')
        import re as _re
        # 移除 // 行注释
        text = _re.sub(r"(^|\n)\s*//.*?(?=\n|$)", "\n", text)
        # 移除 /* */ 注释
        text = _re.sub(r"/\*.*?\*/", "", text, flags=_re.S)
        # 修复尾随逗号：, ] 或 , } 情况
        text = _re.sub(r",\s*(\])", r"\1", text)
        text = _re.sub(r",\s*(\})", r"\1", text)

        # 再次尝试解析
        try:
            parsed = json.loads(text)
            normalized = parsed
            if isinstance(parsed, dict) and 'violations' in parsed:
                normalized = parsed['violations']
            if write_back:
                self._write_json_atomic(self.violations_file, normalized)
            return normalized if isinstance(normalized, list) else parsed
        except Exception:
            pass

        # 4. 识别 NDJSON（每行一个 JSON 对象）
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        ndjson_items = []
        ndjson_success = False
        if lines:
            try:
                for ln in lines:
                    ndjson_items.append(json.loads(ln))
                ndjson_success = True
            except Exception:
                ndjson_success = False
        if ndjson_success:
            if write_back:
                self._write_json_atomic(self.violations_file, ndjson_items)
            return ndjson_items

        # 5. 处理连续对象无逗号，尝试插入逗号并包裹为数组
        try:
            fixed = text.strip()
            # 如果看起来是一连串对象，用正则在 '}{' 之间插入逗号
            fixed = fixed.replace('}{', '},{')
            if not (fixed.startswith('[') and fixed.endswith(']')):
                fixed = '[' + fixed + ']'
            parsed = json.loads(fixed)
            if write_back:
                self._write_json_atomic(self.violations_file, parsed)
            return parsed
        except Exception as e:
            self.logger.error(f"修复 violations.json 失败: {e}")
            return None
    
    def record_violation(self, violation: ComplianceViolation):
        """记录违规行为"""
        self.violations.append(violation)
        self.stats["total_violations"] += 1
        
        # 记录日志
        self.logger.warning(str(violation))
        
        # 保存到文件
        self._save_violations()
        
        # 发送通知
        self._send_notification(violation)
    
    def _send_notification(self, violation: ComplianceViolation):
        """发送违规通知"""
        notification_config = self.config.get("notifications", {}).get("violations", {})
        
        if not notification_config.get("enabled", True):
            return
        
        methods = notification_config.get("methods", ["log", "console"])
        
        if "console" in methods:
            print(f"\n[WARNING] 合规性违规警告")
            print(f"类型: {violation.violation_type}")
            print(f"文件: {violation.file_path}")
            print(f"描述: {violation.description}")
            print(f"严重程度: {violation.severity}")
            print(f"时间: {violation.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            print("="*60)
    
    def start_monitoring(self):
        """开始监控"""
        if not self.config.get("compliance", {}).get("monitoring", {}).get("enabled", True):
            self.logger.info("监控已禁用")
            return
        
        self.logger.info(f"开始监控项目目录: {self.project_root}")
        
        # 设置文件系统监控（异常不阻断整体监控进程）
        try:
            self.observer = Observer()
            self.observer.schedule(self.handler, str(self.project_root), recursive=True)
            self.observer.start()
        except Exception as e:
            self.logger.error(f"文件系统监控器启动失败，将仅运行定时检查: {e}", exc_info=True)
            self.observer = None

        # 记录启动时间与 PID
        self.stats["start_time"] = datetime.now()
        self._write_pid_file()
        
        try:
            # 定期检查（单次异常不退出主循环）
            check_interval = self.config.get("compliance", {}).get("monitoring", {}).get("check_interval", 300)
            
            while True:
                try:
                    time.sleep(check_interval)
                    self._periodic_check()
                except Exception as e:
                    self.logger.error(f"定期检查发生异常（已忽略，继续运行）: {e}", exc_info=True)
                    continue
        except KeyboardInterrupt:
            self.logger.info("收到停止信号，正在关闭监控...")
        finally:
            self.stop_monitoring()
    
    def stop_monitoring(self):
        """停止监控"""
        if self.observer:
            self.observer.stop()
            self.observer.join()

        self.logger.info("监控已停止")
        # 清理 PID 文件
        self._remove_pid_file()
        self._generate_summary_report()
    
    def _periodic_check(self):
        """定期检查"""
        self.logger.info("执行定期合规性检查...")
        
        # 检查项目结构
        structure_violations = self._check_project_structure()
        for violation in structure_violations:
            self.record_violation(violation)
        
        # 检查文件命名
        naming_violations = self._check_naming_conventions()
        for violation in naming_violations:
            self.record_violation(violation)
        
        # 新增：检查日期一致性
        date_violations = self._check_date_consistency()
        for violation in date_violations:
            self.record_violation(violation)
        
        # 清理旧的违规记录
        self._cleanup_old_violations()
        
        self.logger.info(f"定期检查完成，发现 {len(structure_violations + naming_violations + date_violations)} 个新违规")
    
    def _check_project_structure(self) -> List[ComplianceViolation]:
        """检查项目结构"""
        violations = []
        
        # 检查根目录文件
        for item in self.project_root.iterdir():
            if item.is_file():
                passed, messages = self.checker.check_file_operation(str(item), "create")
                if not passed:
                    violation = ComplianceViolation(
                        violation_type="directory_structure_violation",
                        file_path=str(item),
                        description=f"根目录存在不当文件: {'; '.join(messages)}",
                        severity="warning"
                    )
                    violations.append(violation)
        
        return violations
    
    def _check_naming_conventions(self) -> List[ComplianceViolation]:
        """检查文件命名规范"""
        violations = []
        
        # 遍历项目文件
        for file_path in self.project_root.rglob("*"):
            if file_path.is_file() and not self.handler._should_ignore_file(str(file_path)):
                messages = []
                passed = self.checker._check_naming_convention(file_path, messages)
                if not passed:
                    violation = ComplianceViolation(
                        violation_type="naming_convention_violation",
                        file_path=str(file_path),
                        description=f"文件命名不符合规范: {'; '.join(messages)}",
                        severity="info"
                    )
                    violations.append(violation)
        
        return violations
    
    def _check_date_consistency(self) -> List[ComplianceViolation]:
        """检查日期一致性"""
        violations = []
        
        # 遍历项目文件进行日期检查
        for file_path in self.project_root.rglob("*"):
            if file_path.is_file() and not self.handler._should_ignore_file(str(file_path)):
                date_issues = self.handler.date_checker.check_file_dates(file_path)
                if date_issues:
                    violation = ComplianceViolation(
                        violation_type="date_consistency_violation",
                        file_path=str(file_path),
                        description=f"日期一致性问题: {'; '.join(date_issues)}",
                        severity="warning"
                    )
                    violation.date_issues = date_issues
                    violation.suggested_fixes = self.handler.date_checker.suggest_date_fix(file_path)
                    violations.append(violation)
        
        return violations
    
    def _cleanup_old_violations(self):
        """清理旧的违规记录"""
        cutoff_date = datetime.now() - timedelta(days=30)
        
        old_count = len(self.violations)
        self.violations = [v for v in self.violations if v.timestamp > cutoff_date or not v.resolved]
        new_count = len(self.violations)
        
        if old_count != new_count:
            self.logger.info(f"清理了 {old_count - new_count} 条旧违规记录")
            self._save_violations()
    
    def _generate_summary_report(self):
        """生成汇总报告（升级版）"""
        report_file = self.project_root / "logs" / "合规性报告" / f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        # 统计信息
        total_violations = len(self.violations)
        resolved_violations = len([v for v in self.violations if v.resolved])
        unresolved_violations = total_violations - resolved_violations
        date_violations = len([v for v in self.violations if v.violation_type == "date_consistency_violation"])
        
        # 按类型分组
        violations_by_type = {}
        for violation in self.violations:
            if violation.violation_type not in violations_by_type:
                violations_by_type[violation.violation_type] = []
            violations_by_type[violation.violation_type].append(violation)
        
        # 生成报告
        report_content = f"""# 项目合规性监控汇总报告（升级版）

**生成时间**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}
**监控开始时间**: {self.stats['start_time'].strftime('%Y年%m月%d日 %H:%M:%S')}
**监控持续时间**: {datetime.now() - self.stats['start_time']}

## 统计概览

- **总违规数**: {total_violations}
- **已解决**: {resolved_violations}
- **未解决**: {unresolved_violations}
- **日期一致性问题**: {date_violations}
- **解决率**: {(resolved_violations/total_violations*100) if total_violations > 0 else 0:.1f}%

## 违规类型分布

"""
        
        for violation_type, violations in violations_by_type.items():
            type_name = {
                "date_consistency_violation": "日期一致性违规",
                "file_naming_violation": "文件命名违规", 
                "unauthorized_file_creation": "未授权文件创建",
                "protected_file_modification": "受保护文件修改",
                "directory_structure_violation": "目录结构违规",
                "naming_convention_violation": "命名规范违规",
                "important_file_deletion": "重要文件删除"
            }.get(violation_type, violation_type)
            
            report_content += f"### {type_name} ({violation_type})\n"
            report_content += f"- 总数: {len(violations)}\n"
            report_content += f"- 已解决: {len([v for v in violations if v.resolved])}\n"
            report_content += f"- 未解决: {len([v for v in violations if not v.resolved])}\n\n"
        
        # 未解决的违规详情
        unresolved = [v for v in self.violations if not v.resolved]
        if unresolved:
            report_content += "## 未解决的违规问题\n\n"
            for violation in unresolved[-10:]:  # 最近10个
                report_content += f"- **{violation.violation_type}**: {violation.description}\n"
                report_content += f"  - 文件: `{violation.file_path}`\n"
                report_content += f"  - 时间: {violation.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
                report_content += f"  - 严重程度: {violation.severity}\n"
                if hasattr(violation, 'date_issues') and violation.date_issues:
                    report_content += f"  - 日期问题: {', '.join(violation.date_issues)}\n"
                if hasattr(violation, 'suggested_fixes') and violation.suggested_fixes:
                    report_content += f"  - 修复建议: {', '.join(violation.suggested_fixes)}\n"
                report_content += "\n"
        
        # 建议
        report_content += """## 改进建议

1. **定期运行前置检查脚本**，在创建文件前验证合规性
2. **遵循项目架构设计文档**，将文件放置在正确的目录中
3. **使用标准的文件命名规范**，避免使用非法字符
4. **及时清理临时文件**，保持项目目录整洁
5. **定期查看合规性报告**，及时发现和解决问题
6. **统一日期格式**，避免使用历史日期，确保日期一致性
7. **使用自动修复功能**，批量处理日期一致性问题

## 相关文档

- [项目架构设计](../docs/01-设计/项目架构设计.md)
- [规范与流程](../docs/03-管理/规范与流程.md)
- [项目配置文件](../docs/03-管理/project_config.yaml)
- [日期规范指南](../docs/03-管理/日期规范指南.md)
"""
        
        # 保存报告
        try:
            report_file.parent.mkdir(parents=True, exist_ok=True)
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            self.logger.info(f"汇总报告已生成: {report_file}")
        except Exception as e:
            self.logger.error(f"生成汇总报告失败: {e}")
    
    def get_status(self) -> Dict:
        """获取监控状态"""
        total_violations = len(self.violations)
        resolved_violations = len([v for v in self.violations if v.resolved])

        # 通过 PID 文件进行跨进程状态判定
        pid = self._read_pid_file()
        active_via_pid = False
        uptime_str = "unknown"
        if pid is not None:
            active_via_pid = self._is_monitor_process_active(pid)
            # 计算运行时长（如果可用）
            try:
                import psutil  # type: ignore
                if active_via_pid:
                    proc = psutil.Process(pid)
                    start_time = datetime.fromtimestamp(proc.create_time())
                    uptime_str = str(datetime.now() - start_time)
            except Exception:
                # psutil 不可用或失败时，保留 unknown
                pass

        # 同进程内的 observer 检测（用于 --start 进程内查询）
        active_via_observer = self.observer is not None and self.observer.is_alive()

        monitoring_active = active_via_pid or active_via_observer

        return {
            "monitoring_active": monitoring_active,
            "project_root": str(self.project_root),
            "total_violations": total_violations,
            "resolved_violations": resolved_violations,
            "unresolved_violations": total_violations - resolved_violations,
            "last_check": datetime.now().isoformat(),
            "uptime": uptime_str if active_via_pid and uptime_str != "unknown" else str(datetime.now() - self.stats.get("start_time", datetime.now()))
        }


def main():
    """主函数（升级版）"""
    import argparse
    
    parser = argparse.ArgumentParser(description="项目合规性监控系统（升级版）")
    parser.add_argument("--start", action="store_true", help="启动监控")
    parser.add_argument("--check", action="store_true", help="执行一次性检查")
    parser.add_argument("--status", action="store_true", help="显示监控状态")
    parser.add_argument("--stop", action="store_true", help="停止监控（跨进程，根据 PID 文件）")
    parser.add_argument("--report", action="store_true", help="生成汇总报告")
    parser.add_argument("--date-check", action="store_true", help="执行日期一致性检查")
    parser.add_argument("--file", help="指定要检查的文件（用于date-check）")
    parser.add_argument("--fix", action="store_true", help="自动修复日期问题")
    parser.add_argument("--repair-violations", action="store_true", help="修复 violations.json 并重写为有效 JSON")
    parser.add_argument("--project-root", default="s:/YDS-Lab", help="项目根目录")
    
    args = parser.parse_args()
    
    monitor = ComplianceMonitor(args.project_root)
    
    if args.start:
        print("启动项目合规性监控系统（升级版）...")
        monitor.start_monitoring()
    
    elif args.check:
        print("执行一次性合规性检查（包含日期一致性）...")
        monitor._periodic_check()
        print("检查完成")
    
    elif args.status:
        status = monitor.get_status()
        print("\n项目合规性监控状态:")
        print(f"监控状态: {'运行中' if status['monitoring_active'] else '已停止'}")
        # 可选：显示 PID 与运行时长（增强可读性，不影响 start.py 检测）
        pid = monitor._read_pid_file()
        if pid is not None:
            print(f"监控进程PID: {pid}")
            print(f"运行时长: {status.get('uptime', 'unknown')}")

    elif args.stop:
        # 基于 PID 的跨进程停止逻辑
        pid = monitor._read_pid_file()
        if pid is None:
            print("未找到 PID 文件，监控可能未运行或已停止。")
        else:
            try:
                import psutil  # type: ignore
                if psutil.pid_exists(pid):
                    proc = psutil.Process(pid)
                    # 优雅终止
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except psutil.TimeoutExpired:
                        proc.kill()
                    print(f"已停止监控进程（PID={pid}）。")
                else:
                    print(f"PID {pid} 不存在，清理 PID 文件。")
            except Exception as e:
                print(f"停止监控进程失败: {e}")
            finally:
                # 无论进程是否存在，都尝试移除 PID 文件
                monitor._remove_pid_file()

        # 显示停止后的状态
        status = monitor.get_status()
        print("\n项目合规性监控状态:")
        print(f"监控状态: {'运行中' if status['monitoring_active'] else '已停止'}")
        print(f"项目根目录: {status['project_root']}")
        print(f"总违规数: {status['total_violations']}")
        print(f"已解决: {status['resolved_violations']}")
        print(f"未解决: {status['unresolved_violations']}")
        print(f"运行时间: {status['uptime']}")
    
    elif args.report:
        print("生成汇总报告（升级版）...")
        monitor._generate_summary_report()
        print("报告生成完成")

    elif args.repair_violations:
        print("修复 violations.json 中的违规记录...")
        repaired = monitor._repair_violations_file(write_back=True)
        if repaired is None:
            print("[错误] 修复失败：无法解析或写回 violations.json。")
        else:
            count = len(repaired) if isinstance(repaired, list) else (len(repaired.get('violations', [])) if isinstance(repaired, dict) else 0)
            print(f"[成功] 已修复并写回，记录数: {count}")
        return
    
    elif args.date_check:
        print("[日期检查] 执行日期一致性检查...")
        if args.file:
            # 检查指定文件
            file_path = Path(args.file)
            if file_path.exists():
                date_issues = monitor.handler.date_checker.check_file_dates(file_path)
                if date_issues:
                    print(f"[错误] 发现日期问题: {'; '.join(date_issues)}")
                    if args.fix:
                        fixes = monitor.handler.date_checker.suggest_date_fix(file_path)
                        print(f"[修复] 修复建议: {'; '.join(fixes)}")
                else:
                    print("[成功] 未发现日期问题")
            else:
                print(f"[错误] 文件不存在: {args.file}")
        else:
            # 检查整个项目
            violations = monitor._check_date_consistency()
            if violations:
                print(f"[错误] 发现 {len(violations)} 个日期一致性问题")
                for v in violations[:5]:  # 显示前5个
                    print(f"  - {v.file_path}: {v.description}")
            else:
                print("[成功] 未发现日期一致性问题")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()