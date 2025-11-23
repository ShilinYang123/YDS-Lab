#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YDS-Lab 通用工具模块
替代原有的utils目录功能
"""

import os
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any


class Logger:
    """统一日志记录器"""
    
    def __init__(self, name: str = "YDS-Lab"):
        self.name = name
        self.log_dir = Path("S:/YDS-Lab/logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def log_meeting(self, meeting_id: str, content: str) -> str:
        """记录会议日志"""
        log_file = self.log_dir / "meeting" / f"{meeting_id}.md"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return str(log_file)
    
    def log_info(self, message: str, module: str = ""):
        """记录信息日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] INFO {module}: {message}"
        print(log_message)
        
        # 保存到文件
        log_file = self.log_dir / "app" / f"{datetime.now().strftime('%Y%m%d')}.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + "\n")
    
    def log_error(self, message: str, module: str = ""):
        """记录错误日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] ERROR {module}: {message}"
        print(log_message)
        
        # 保存到文件
        log_file = self.log_dir / "app" / f"{datetime.now().strftime('%Y%m%d')}.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + "\n")


def get_project_root() -> Path:
    """获取项目根目录"""
    return Path("S:/YDS-Lab")


def load_config(config_name: str) -> Dict[str, Any]:
    """加载配置文件"""
    config_path = get_project_root() / "config" / config_name
    
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    if config_path.suffix.lower() in ['.yaml', '.yml']:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    elif config_path.suffix.lower() == '.json':
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        raise ValueError(f"不支持的配置文件格式: {config_path.suffix}")


def save_config(config_name: str, data: Dict[str, Any]) -> str:
    """保存配置文件"""
    config_path = get_project_root() / "config" / config_name
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    if config_path.suffix.lower() in ['.yaml', '.yml']:
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, indent=2)
    elif config_path.suffix.lower() == '.json':
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    else:
        raise ValueError(f"不支持的配置文件格式: {config_path.suffix}")
    
    return str(config_path)


def ensure_directory(path: str) -> Path:
    """确保目录存在，如果不存在则创建"""
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def get_current_timestamp() -> str:
    """获取当前时间戳"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def read_file(file_path: str) -> str:
    """读取文件内容"""
    path_obj = Path(file_path)
    if not path_obj.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    with open(path_obj, 'r', encoding='utf-8') as f:
        return f.read()


def write_file(file_path: str, content: str) -> str:
    """写入文件内容"""
    path_obj = Path(file_path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path_obj, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return str(path_obj)


def append_file(file_path: str, content: str) -> str:
    """追加文件内容"""
    path_obj = Path(file_path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path_obj, 'a', encoding='utf-8') as f:
        f.write(content)
    
    return str(path_obj)


def list_files(directory: str, pattern: str = "*") -> list:
    """列出目录中的文件"""
    path_obj = Path(directory)
    if not path_obj.exists():
        return []
    
    return [str(f) for f in path_obj.glob(pattern) if f.is_file()]


def list_directories(directory: str) -> list:
    """列出目录中的子目录"""
    path_obj = Path(directory)
    if not path_obj.exists():
        return []
    
    return [str(d) for d in path_obj.iterdir() if d.is_dir()]


def copy_file(src: str, dst: str) -> str:
    """复制文件"""
    import shutil
    dst_path = Path(dst)
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return str(dst_path)


def move_file(src: str, dst: str) -> str:
    """移动文件"""
    import shutil
    dst_path = Path(dst)
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(src, dst)
    return str(dst_path)


def delete_file(file_path: str) -> bool:
    """删除文件"""
    path_obj = Path(file_path)
    if path_obj.exists() and path_obj.is_file():
        path_obj.unlink()
        return True
    return False


def get_file_size(file_path: str) -> int:
    """获取文件大小（字节）"""
    path_obj = Path(file_path)
    if path_obj.exists() and path_obj.is_file():
        return path_obj.stat().st_size
    return 0


def get_file_modified_time(file_path: str) -> datetime:
    """获取文件修改时间"""
    path_obj = Path(file_path)
    if path_obj.exists():
        return datetime.fromtimestamp(path_obj.stat().st_mtime)
    return datetime.min


# 全局日志器实例
logger = Logger()


# 向后兼容的函数
def log_meeting(meeting_id: str, content: str) -> str:
    """记录会议（兼容旧代码）"""
    return logger.log_meeting(meeting_id, content)