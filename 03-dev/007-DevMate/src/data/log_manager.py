"""
日志管理模块
负责结构化日志记录和管理
"""
import os
import datetime
import threading
from enum import Enum
from typing import Optional


class LogLevel(Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogManager:
    """日志管理器，负责结构化日志记录和管理"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, log_file_path: Optional[str] = None, force_new: bool = False):
        """
        创建日志管理器实例
        
        Args:
            log_file_path: 日志文件路径，如果为None则使用默认路径
            force_new: 是否强制创建新实例（主要用于测试）
        """
        if force_new or cls._instance is None:
            with cls._lock:
                if force_new or cls._instance is None:
                    cls._instance = super(LogManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, log_file_path: Optional[str] = None, force_new: bool = False):
        """
        初始化日志管理器
        
        Args:
            log_file_path: 日志文件路径，如果为None则使用默认路径
            force_new: 是否强制创建新实例（主要用于测试）
        """
        if hasattr(self, '_initialized') and not force_new:
            return
            
        self._initialized = True
        self.log_file_path = log_file_path or self._get_default_log_path()
        self._ensure_log_dir()
        self._lock = threading.Lock()
    
    def _get_default_log_path(self) -> str:
        """获取默认日志文件路径"""
        return os.path.join(os.path.dirname(__file__), '..', '..', 'trae_mate_log.txt')
    
    def _ensure_log_dir(self) -> None:
        """确保日志目录存在"""
        log_dir = os.path.dirname(self.log_file_path)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
    
    def write_log(self, level: LogLevel, message: str) -> None:
        """
        写入日志
        
        Args:
            level: 日志级别
            message: 日志消息
        """
        with self._lock:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] [{level.value}] {message}\n"
            
            try:
                with open(self.log_file_path, 'a', encoding='utf-8') as f:
                    f.write(log_entry)
            except Exception as e:
                # 如果写入日志失败，输出到控制台
                print(f"日志写入失败: {e}")
                print(log_entry)
    
    def read_logs(self) -> str:
        """读取所有日志内容"""
        if not os.path.exists(self.log_file_path):
            return ""
        
        try:
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return ""
    
    def debug(self, message: str) -> None:
        """写入调试级别日志"""
        self.write_log(LogLevel.DEBUG, message)
    
    def info(self, message: str) -> None:
        """写入信息级别日志"""
        self.write_log(LogLevel.INFO, message)
    
    def warning(self, message: str) -> None:
        """写入警告级别日志"""
        self.write_log(LogLevel.WARNING, message)
    
    def error(self, message: str) -> None:
        """写入错误级别日志"""
        self.write_log(LogLevel.ERROR, message)
    
    def critical(self, message: str) -> None:
        """写入严重错误级别日志"""
        self.write_log(LogLevel.CRITICAL, message)
    
    def get_recent_logs(self, lines: int = 100) -> list:
        """
        获取最近的日志
        
        Args:
            lines: 要获取的行数
            
        Returns:
            日志行列表
        """
        try:
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                return all_lines[-lines:] if len(all_lines) > lines else all_lines
        except Exception as e:
            return [f"读取日志失败: {e}"]
    
    def clear_logs(self) -> bool:
        """
        清空日志文件
        
        Returns:
            是否成功清空
        """
        try:
            with open(self.log_file_path, 'w', encoding='utf-8') as f:
                f.write("")
            return True
        except Exception as e:
            self.error(f"清空日志失败: {e}")
            return False
    
    def get_log_size(self) -> int:
        """
        获取日志文件大小（字节）
        
        Returns:
            日志文件大小
        """
        try:
            return os.path.getsize(self.log_file_path)
        except Exception:
            return 0