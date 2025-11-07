#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YDS-Lab 工作完成处理工具

功能：
- 工作会话结束检查
- 生成工作报告
- 项目备份管理
- Git提交记录整理
- AI Agent工作总结

适配YDS-Lab项目和CrewAI多智能体协作需求
"""

import os
import sys
import json
import time
import logging
import subprocess
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import yaml
import argparse

# 添加 tools 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))
"""
GitHelper 兼容导入与回退实现

优先使用 -sub/git_tools/git_helper.py 中的 GitHelper；若不存在，则尝试
使用 tools/git/auto_push.py 中的 YDSLabAutoPush 并封装为同名接口；再不行，
使用系统 git 命令作为最终回退以保证 fi.py 的推送流程正常。
"""

# 修复导入路径，使用相对导入，并提供健壮的回退实现
try:
    from pathlib import Path
    import importlib.util

    git_helper_path = Path(__file__).parent / "-sub" / "git_tools" / "git_helper.py"
    if git_helper_path.exists():
        spec = importlib.util.spec_from_file_location("git_helper", git_helper_path)
        git_helper_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(git_helper_module)
        GitHelper = git_helper_module.GitHelper
    else:
        # 尝试使用 tools/git/auto_push.py
        auto_push_path = Path(__file__).parent / "tools" / "git" / "auto_push.py"
        if auto_push_path.exists():
            spec = importlib.util.spec_from_file_location("auto_push", auto_push_path)
            auto_push_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(auto_push_module)
            YDSLabAutoPush = auto_push_module.YDSLabAutoPush

            class GitHelper:
                """封装 YDSLabAutoPush 为 fi.py 期望的接口"""
                def __init__(self, repo_path: str):
                    self.repo_path = str(repo_path)
                    self.auto = YDSLabAutoPush(project_root=self.repo_path)

                def get_status(self):
                    return self.auto.get_status()

                def commit(self, message: str, auto_add: bool = False):
                    if auto_add:
                        self.auto.add_all_changes()
                    return self.auto.commit_changes(message)

                def push(self, remote: str = 'origin', branch: str = None):
                    if not branch:
                        branch = self.auto.get_current_branch()
                    return self.auto.push_to_remote(remote, branch)

                def get_commits(self, since: str = None, until: str = None):
                    # 使用底层 run_git_command 以支持时间范围过滤
                    from datetime import datetime
                    args = [
                        'log',
                        f"--after={since}" if since else '--all',
                        f"--before={until}" if until else '',
                        '--pretty=format:%h|%s|%an|%ad',
                        '--date=format:%H:%M',
                        '--no-merges'
                    ]
                    # 去除空字符串参数
                    args = [a for a in args if a]
                    ok, out, err = self.auto.run_git_command(args)
                    commits = []
                    if ok and out.strip():
                        for line in out.strip().split('\n'):
                            parts = line.split('|')
                            if len(parts) >= 4:
                                commits.append({
                                    'hash': parts[0],
                                    'message': parts[1],
                                    'author': parts[2],
                                    'time': parts[3]
                                })
                        return {'success': True, 'commits': commits}
                    else:
                        return {'success': False, 'error': err or 'git log 执行失败', 'commits': []}
        else:
            # 最终回退：直接使用系统 git 命令实现必要接口
            class GitHelper:
                def __init__(self, repo_path: str):
                    self.repo_path = str(repo_path)

                def _run(self, args):
                    try:
                        r = subprocess.run(['git'] + args, cwd=self.repo_path,
                                           capture_output=True, text=True, encoding='utf-8')
                        return r.returncode == 0, r.stdout.strip(), r.stderr.strip()
                    except Exception as e:
                        return False, '', str(e)

                def get_status(self):
                    ok, out, err = self._run(['status', '--porcelain'])
                    if not ok:
                        return {'clean': True, 'error': err}
                    status = {'modified': [], 'added': [], 'deleted': [], 'untracked': [], 'clean': True}
                    for line in out.split('\n'):
                        if not line.strip():
                            continue
                        code = line[:2]
                        path = line[3:].strip()
                        status['clean'] = False
                        if code.startswith('M'):
                            status['modified'].append(path)
                        elif code.startswith('A'):
                            status['added'].append(path)
                        elif code.startswith('D'):
                            status['deleted'].append(path)
                        elif code.startswith('??'):
                            status['untracked'].append(path)
                    return status

                def commit(self, message: str, auto_add: bool = False):
                    if auto_add:
                        self._run(['add', '-A'])
                    ok, _, err = self._run(['commit', '-m', message])
                    return ok

                def push(self, remote: str = 'origin', branch: str = None):
                    if not branch:
                        okb, outb, _ = self._run(['branch', '--show-current'])
                        branch = outb.strip() if okb and outb.strip() else 'main'
                    ok, _, _err = self._run(['push', remote, branch])
                    return ok

                def get_commits(self, since: str = None, until: str = None):
                    args = [
                        'log',
                        f"--after={since}" if since else '--all',
                        f"--before={until}" if until else '',
                        '--pretty=format:%h|%s|%an|%ad',
                        '--date=format:%H:%M',
                        '--no-merges'
                    ]
                    args = [a for a in args if a]
                    ok, out, err = self._run(args)
                    commits = []
                    if ok and out.strip():
                        for line in out.strip().split('\n'):
                            parts = line.split('|')
                            if len(parts) >= 4:
                                commits.append({
                                    'hash': parts[0],
                                    'message': parts[1],
                                    'author': parts[2],
                                    'time': parts[3]
                                })
                        return {'success': True, 'commits': commits}
                    else:
                        return {'success': False, 'error': err or 'git log 执行失败', 'commits': []}
except Exception:
    # 兜底防御：若上述导入链出现异常，使用系统 git 命令实现
    class GitHelper:
        def __init__(self, repo_path: str):
            self.repo_path = str(repo_path)
        def _run(self, args):
            try:
                r = subprocess.run(['git'] + args, cwd=self.repo_path,
                                   capture_output=True, text=True, encoding='utf-8')
                return r.returncode == 0, r.stdout.strip(), r.stderr.strip()
            except Exception as e:
                return False, '', str(e)
        def get_status(self):
            ok, out, err = self._run(['status', '--porcelain'])
            if not ok:
                return {'clean': True, 'error': err}
            status = {'modified': [], 'added': [], 'deleted': [], 'untracked': [], 'clean': True}
            for line in out.split('\n'):
                if not line.strip():
                    continue
                code = line[:2]
                path = line[3:].strip()
                status['clean'] = False
                if code.startswith('M'):
                    status['modified'].append(path)
                elif code.startswith('A'):
                    status['added'].append(path)
                elif code.startswith('D'):
                    status['deleted'].append(path)
                elif code.startswith('??'):
                    status['untracked'].append(path)
            return status
        def commit(self, message: str, auto_add: bool = False):
            if auto_add:
                self._run(['add', '-A'])
            ok, _, _ = self._run(['commit', '-m', message])
            return ok
        def push(self, remote: str = 'origin', branch: str = None):
            if not branch:
                okb, outb, _ = self._run(['branch', '--show-current'])
                branch = outb.strip() if okb and outb.strip() else 'main'
            ok, _, _ = self._run(['push', remote, branch])
            return ok
        def get_commits(self, since: str = None, until: str = None):
            args = [
                'log',
                f"--after={since}" if since else '--all',
                f"--before={until}" if until else '',
                '--pretty=format:%h|%s|%an|%ad',
                '--date=format:%H:%M',
                '--no-merges'
            ]
            args = [a for a in args if a]
            ok, out, err = self._run(args)
            commits = []
            if ok and out.strip():
                for line in out.strip().split('\n'):
                    parts = line.split('|')
                    if len(parts) >= 4:
                        commits.append({
                            'hash': parts[0],
                            'message': parts[1],
                            'author': parts[2],
                            'time': parts[3]
                        })
                return {'success': True, 'commits': commits}
            else:
                return {'success': False, 'error': err or 'git log 执行失败', 'commits': []}

class YDSLabFinishProcessor:
    """YDS-Lab工作完成处理器"""
    
    def __init__(self, project_root: str = "s:/YDS-Lab"):
        self.project_root = Path(project_root)
        self.tools_dir = self.project_root / "tools"
        # 统一总经办目录至 01-struc/0B-general-manager（旧路径 GeneralOffice 仅作为历史记录，不再回退使用）
        self.docs_dir = self.project_root / "01-struc" / "0B-general-manager" / "Docs"
        self.ai_dir = self.project_root / "ai"
        self.logs_dir = self.project_root / "01-struc" / "0B-general-manager" / "logs"
        self.bak_dir = self.project_root / "01-struc" / "0B-general-manager" / "bak"
        
        # 初始化 Git Helper
        try:
            self.git_helper = GitHelper(str(self.project_root))
            print(f"✅ GitHelper 初始化成功")
        except Exception as e:
            print(f"❌ GitHelper 初始化失败: {e}")
            self.git_helper = None
        
        # 设置日志
        self.setup_logging()
        
        # 配置文件路径集中至 /config，兼容旧路径 01-struc/0B-general-manager/config 作为回退
        cfg_new = self.project_root / "config" / "finish_config.yaml"
        cfg_old = self.project_root / "01-struc" / "0B-general-manager" / "config" / "finish_config.yaml"
        self.config_file = cfg_new if cfg_new.exists() else cfg_old
        
        # 默认配置
        self.default_config = {
            'backup': {
                'enable_auto_backup': True,
                'backup_retention_days': 30,
                'backup_type': 'daily',  # daily, weekly, projects
                'exclude_patterns': [
                    '.git', '__pycache__', '*.pyc', '.venv', 'node_modules', 
                    'Backups', 'bak', '*.bak', '*.backup',  # 备份文件
                    '*.log', '*.tmp', '*.temp', 'temp', 'cache', '.cache',  # 临时文件
                    'api_keys.json', '*.key', '*.pem', '.env', '.env.*',  # 敏感文件
                    'logs', '*.out', 'downloads', '*.zip', '*.tar.gz',  # 日志和大文件
                    '.DS_Store', 'Thumbs.db', 'desktop.ini'  # 系统文件
                ]
            },
            'git': {
                'auto_commit': True,
                'commit_prefix': '工作完成',
                'push_to_remote': True,  # 启用 GitHub 推送
                'repository_name': 'YDS-Lab'
            },
            'reports': {
                'generate_daily_report': True,
                'include_git_commits': True,
                'include_file_changes': True,
                'include_ai_summary': True
            },
            'cleanup': {
                'auto_cleanup_temp': True,
                'cleanup_old_logs': True,
                'max_log_files': 50
            }
        }
        
        self.load_config()
        
    def setup_logging(self):
        """设置日志系统"""
        try:
            # 确保日志目录存在
            work_logs_dir = self.logs_dir / "工作记录"
            work_logs_dir.mkdir(parents=True, exist_ok=True)
            
            # 配置日志格式
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = work_logs_dir / f"finish_{timestamp}.log"
            
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(log_file, encoding='utf-8'),
                    logging.StreamHandler(sys.stdout)
                ]
            )
            
            self.logger = logging.getLogger(__name__)
            self.logger.info("YDS-Lab工作完成处理器初始化")
            
        except Exception as e:
            print(f"日志系统初始化失败: {e}")
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
                self.logger.info("工作完成配置加载成功")
            else:
                self.logger.warning("工作完成配置文件不存在，使用默认配置")
                self.save_config()
        except Exception as e:
            self.logger.error(f"配置文件加载失败: {e}")
            
    def save_config(self):
        """保存配置文件"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.default_config, f, default_flow_style=False, 
                         allow_unicode=True, indent=2)
            self.logger.info("默认工作完成配置文件已创建")
        except Exception as e:
            self.logger.error(f"配置文件保存失败: {e}")
            
    def get_current_session_info(self) -> Dict[str, any]:
        """获取当前工作会话信息"""
        now = datetime.now()
        weekdays_cn = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        
        return {
            'end_time': now.strftime('%Y-%m-%d %H:%M:%S'),
            'date': now.strftime('%Y-%m-%d'),
            'formatted_date': now.strftime('%Y年%m月%d日'),
            'weekday': weekdays_cn[now.weekday()],
            'timestamp': now.timestamp()
        }
        
    def get_daily_git_commits(self) -> Dict[str, any]:
        """获取当日Git提交记录"""
        self.logger.info("获取当日Git提交记录...")
        
        try:
            # 检查 GitHelper 是否可用
            if not self.git_helper:
                self.logger.warning("GitHelper 不可用，跳过Git提交记录获取")
                return {
                    'success': False,
                    'commits': [],
                    'total_commits': 0,
                    'error': 'GitHelper 不可用'
                }
            
            today = datetime.now().strftime("%Y-%m-%d")
            
            # 使用 GitHelper 获取提交记录
            try:
                commits_result = self.git_helper.get_commits(
                    since=f"{today} 00:00:00",
                    until=f"{today} 23:59:59"
                )
                
                if commits_result and commits_result.get('success', False):
                    return {
                        'success': True,
                        'commits': commits_result.get('commits', []),
                        'total_commits': len(commits_result.get('commits', []))
                    }
                else:
                    # 如果 GitHelper 失败，回退到系统命令
                    raise Exception("GitHelper 获取提交记录失败")
                    
            except Exception as git_error:
                self.logger.warning(f"GitHelper 获取提交记录失败: {git_error}，回退到系统命令")
                
                # 回退到系统 Git 命令
                cmd = [
                    "git", "log", 
                    f"--after={today} 00:00:00",
                    f"--before={today} 23:59:59",
                    "--pretty=format:%h|%s|%an|%ad",
                    "--date=format:%H:%M",
                    "--no-merges"
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    cwd=str(self.project_root),
                    timeout=30
                )
                
                commits = []
                if result.returncode == 0 and result.stdout.strip():
                    for line in result.stdout.strip().split('\n'):
                        parts = line.split('|')
                        if len(parts) >= 4:
                            commits.append({
                                'hash': parts[0],
                                'message': parts[1],
                                'author': parts[2],
                                'time': parts[3]
                            })
                            
                return {
                    'success': True,
                    'commits': commits,
                    'total_commits': len(commits)
                }
            
        except Exception as e:
            self.logger.error(f"获取Git提交记录失败: {e}")
            return {
                'success': False,
                'commits': [],
                'total_commits': 0,
                'error': str(e)
            }
            
    def analyze_file_changes(self) -> Dict[str, any]:
        """分析文件变更情况"""
        self.logger.info("分析文件变更情况...")
        
        try:
            # 检查 GitHelper 是否可用
            if not self.git_helper:
                self.logger.warning("GitHelper 不可用，跳过文件变更分析")
                return {
                    'modified': [],
                    'added': [],
                    'deleted': [],
                    'untracked': [],
                    'total_changes': 0
                }
            
            # 使用 GitHelper 获取工作目录状态
            status_result = self.git_helper.get_status()
            
            changes = {
                'modified': [],
                'added': [],
                'deleted': [],
                'untracked': [],
                'total_changes': 0
            }
            
            if status_result:
                # 直接使用 GitHelper 返回的数据结构
                changes['modified'] = status_result.get('modified', [])
                changes['added'] = status_result.get('added', [])
                changes['deleted'] = status_result.get('deleted', [])
                changes['untracked'] = status_result.get('untracked', [])
                        
                changes['total_changes'] = sum(len(v) for v in changes.values() if isinstance(v, list))
                
            return changes
            
        except Exception as e:
            self.logger.error(f"分析文件变更失败: {e}")
            return {
                'modified': [],
                'added': [],
                'deleted': [],
                'untracked': [],
                'total_changes': 0
            }
            
    def check_ai_agents_status(self) -> Dict[str, any]:
        """检查AI Agent状态"""
        self.logger.info("检查AI Agent状态...")
        
        agents_dir = self.ai_dir / "agents"
        tasks_dir = self.ai_dir / "tasks"
        memory_dir = self.ai_dir / "memory"
        
        status = {
            'agents_active': False,
            'total_agents': 0,
            'completed_tasks': 0,
            'memory_entries': 0,
            'session_summary': "无AI Agent活动记录"
        }
        
        try:
            # 检查Agent文件
            if agents_dir.exists():
                agent_files = list(agents_dir.glob("*.py"))
                status['total_agents'] = len(agent_files)
                status['agents_active'] = len(agent_files) > 0
                
            # 检查任务完成情况
            if tasks_dir.exists():
                task_files = list(tasks_dir.glob("*.json"))
                status['completed_tasks'] = len(task_files)
                
            # 检查记忆存储
            if memory_dir.exists():
                memory_files = list(memory_dir.glob("*.json"))
                status['memory_entries'] = len(memory_files)
                
            # 生成会话摘要
            if status['agents_active']:
                status['session_summary'] = f"本次会话共有{status['total_agents']}个AI Agent参与，完成{status['completed_tasks']}个任务，产生{status['memory_entries']}条记忆记录"
            else:
                status['session_summary'] = "本次会话未检测到AI Agent活动"
                
        except Exception as e:
            self.logger.error(f"检查AI Agent状态失败: {e}")
            status['error'] = str(e)
            
        return status
        
    def perform_project_backup(self) -> Dict[str, any]:
        """执行项目备份"""
        if not self.default_config['backup']['enable_auto_backup']:
            self.logger.info("自动备份已禁用")
            return {'success': False, 'reason': 'disabled'}
            
        self.logger.info("开始执行项目备份...")
        
        try:
            # 根据当前时间确定备份类型和目录
            now = datetime.now()
            timestamp = now.strftime("%Y%m%d_%H%M%S")
            date_str = now.strftime("%Y-%m-%d")
            
            # 确定备份类型：工作日备份到 daily，项目完成备份到 projects
            backup_type = self.default_config['backup'].get('backup_type', 'daily')
            
            if backup_type == 'weekly':
                backup_dir = self.bak_dir / "weekly"
                backup_name = f"weekly_{now.strftime('%Y_W%U')}_{timestamp}"
            elif backup_type == 'projects':
                backup_dir = self.bak_dir / "projects"
                backup_name = f"project_{timestamp}"
            else:  # daily
                backup_dir = self.bak_dir / "daily"
                backup_name = f"daily_{date_str}_{timestamp}"
            
            backup_path = backup_dir / backup_name
            
            # 确保备份目录存在
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # 排除模式
            exclude_patterns = self.default_config['backup']['exclude_patterns']
            
            # 复制项目文件
            def should_exclude(path: Path) -> bool:
                for pattern in exclude_patterns:
                    if pattern in str(path):
                        return True
                return False
                
            copied_files = 0
            skipped_files = 0
            
            for item in self.project_root.rglob("*"):
                if item.is_file() and not should_exclude(item):
                    relative_path = item.relative_to(self.project_root)
                    target_path = backup_path / relative_path
                    
                    # 创建目标目录
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # 复制文件
                    shutil.copy2(item, target_path)
                    copied_files += 1
                else:
                    skipped_files += 1
                    
            # 清理旧备份
            self.cleanup_old_backups()
            
            backup_info = {
                'success': True,
                'backup_path': str(backup_path),
                'backup_name': backup_name,
                'copied_files': copied_files,
                'skipped_files': skipped_files,
                'backup_size': self.get_directory_size(backup_path)
            }
            
            self.logger.info(f"项目备份完成: {backup_path}")
            return backup_info
            
        except Exception as e:
            self.logger.error(f"项目备份失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
            
    def cleanup_old_backups(self):
        """清理旧备份"""
        try:
            if not self.bak_dir.exists():
                return
                
            retention_days = self.default_config['backup']['backup_retention_days']
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            removed_count = 0
            for backup_dir in self.bak_dir.iterdir():
                if backup_dir.is_dir() and backup_dir.name.startswith('backup_'):
                    # 从目录名提取时间戳
                    try:
                        timestamp_str = backup_dir.name.replace('backup_', '')
                        backup_date = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                        
                        if backup_date < cutoff_date:
                            shutil.rmtree(backup_dir)
                            removed_count += 1
                            self.logger.info(f"删除过期备份: {backup_dir.name}")
                            
                    except ValueError:
                        # 无法解析时间戳，跳过
                        continue
                        
            if removed_count > 0:
                self.logger.info(f"清理了 {removed_count} 个过期备份")
                
        except Exception as e:
            self.logger.error(f"清理旧备份失败: {e}")
            
    def get_directory_size(self, path: Path) -> str:
        """获取目录大小"""
        try:
            total_size = 0
            for file_path in path.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    
            # 转换为可读格式
            for unit in ['B', 'KB', 'MB', 'GB']:
                if total_size < 1024.0:
                    return f"{total_size:.1f} {unit}"
                total_size /= 1024.0
            return f"{total_size:.1f} TB"
            
        except Exception:
            return "未知"
            
    def cleanup_temp_files(self):
        """清理临时文件"""
        if not self.default_config['cleanup']['auto_cleanup_temp']:
            return
            
        self.logger.info("清理临时文件...")
        
        try:
            temp_patterns = ['*.tmp', '*.temp', '*~', '.DS_Store', 'Thumbs.db']
            removed_count = 0
            
            for pattern in temp_patterns:
                for temp_file in self.project_root.rglob(pattern):
                    if temp_file.is_file():
                        temp_file.unlink()
                        removed_count += 1
                        
            if removed_count > 0:
                self.logger.info(f"清理了 {removed_count} 个临时文件")
                
        except Exception as e:
            self.logger.error(f"清理临时文件失败: {e}")
            
    def cleanup_old_logs(self):
        """清理旧日志文件"""
        if not self.default_config['cleanup']['cleanup_old_logs']:
            return
            
        self.logger.info("清理旧日志文件...")
        
        try:
            max_files = self.default_config['cleanup']['max_log_files']
            
            # 获取所有日志文件并按修改时间排序
            log_files = []
            for log_file in self.logs_dir.rglob("*.log"):
                if log_file.is_file():
                    log_files.append((log_file.stat().st_mtime, log_file))
                    
            # 按时间排序，保留最新的文件
            log_files.sort(reverse=True)
            
            if len(log_files) > max_files:
                files_to_remove = log_files[max_files:]
                for _, log_file in files_to_remove:
                    log_file.unlink()
                    
                self.logger.info(f"清理了 {len(files_to_remove)} 个旧日志文件")
                
        except Exception as e:
            self.logger.error(f"清理旧日志文件失败: {e}")
            
    def perform_git_push(self) -> Dict[str, any]:
        """执行 Git 推送操作"""
        if not self.default_config['git']['push_to_remote']:
            self.logger.info("Git 推送已禁用")
            return {'success': False, 'reason': 'disabled'}
            
        self.logger.info("开始执行 Git 推送...")
        
        try:
            # 检查是否有未提交的更改
            status = self.git_helper.get_status()
            
            # 检查是否有任何类型的变更（包括未跟踪文件）
            has_changes = (
                not status.get('clean', True) or 
                len(status.get('untracked', [])) > 0 or
                len(status.get('modified', [])) > 0 or
                len(status.get('added', [])) > 0 or
                len(status.get('deleted', [])) > 0
            )
            
            if has_changes:
                # 记录检测到的变更
                self.logger.info(f"检测到变更:")
                if status.get('modified'):
                    self.logger.info(f"  修改的文件: {status.get('modified')}")
                if status.get('added'):
                    self.logger.info(f"  新增的文件: {status.get('added')}")
                if status.get('deleted'):
                    self.logger.info(f"  删除的文件: {status.get('deleted')}")
                if status.get('untracked'):
                    self.logger.info(f"  未跟踪的文件: {status.get('untracked')}")
                
                # 自动提交更改
                commit_message = f"chore: {self.default_config['git']['commit_prefix']} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                
                if self.git_helper.commit(commit_message, auto_add=True):
                    self.logger.info(f"自动提交完成: {commit_message}")
                else:
                    self.logger.warning("自动提交失败")
                    return {'success': False, 'error': '自动提交失败'}
            
            # 执行推送
            if self.git_helper.push():
                push_info = {
                    'success': True,
                    'message': 'Git 推送成功',
                    'repository': self.default_config['git']['repository_name'],
                    'timestamp': datetime.now().isoformat()
                }
                self.logger.info("Git 推送成功")
                return push_info
            else:
                self.logger.error("Git 推送失败")
                return {'success': False, 'error': 'Git 推送失败'}
                
        except Exception as e:
            self.logger.error(f"Git 推送过程中发生错误: {e}")
            return {'success': False, 'error': str(e)}

    def generate_work_report(self, session_info: Dict, git_info: Dict, 
                            file_changes: Dict, ai_status: Dict, 
                            backup_info: Dict, push_info: Dict = None) -> str:
         """生成工作报告"""
         self.logger.info("生成工作报告...")
         
         report = f"""# YDS-Lab 工作完成报告
 
 > 生成时间: {session_info['formatted_date']} {session_info['weekday']} {session_info['end_time']}  
 > 项目根目录: `{self.project_root}`
 
 ## 📊 工作会话概览
 
 ### 时间信息
 - **结束时间**: {session_info['end_time']}
 - **工作日期**: {session_info['formatted_date']} {session_info['weekday']}
 
 ### Git提交记录
 """
         
         if git_info['success'] and git_info['total_commits'] > 0:
             report += f"- **今日提交数**: {git_info['total_commits']} 次\n\n"
             report += "#### 提交详情\n"
             for commit in git_info['commits']:
                 report += f"- `{commit['hash']}` {commit['message']} - {commit['author']} ({commit['time']})\n"
         else:
             report += "- **今日提交数**: 0 次\n"
             if not git_info['success']:
                 report += f"- **获取失败**: {git_info.get('error', '未知错误')}\n"
                 
         # 添加 Git 推送状态
         if push_info:
             report += f"""
 
 ### Git 推送状态
 """
             if push_info.get('success'):
                 report += f"""- **推送状态**: ✅ 成功
 - **仓库名称**: {push_info.get('repository', 'YDS-Lab')}
 - **推送时间**: {push_info.get('timestamp', '未知')}
 """
             else:
                 reason = push_info.get('reason', push_info.get('error', '未知原因'))
                 report += f"- **推送状态**: ❌ 失败 ({reason})\n"
                 
         report += f"""
 
 ### 文件变更统计
 - **总变更数**: {file_changes['total_changes']} 个文件
 - **修改文件**: {len(file_changes['modified'])} 个
 - **新增文件**: {len(file_changes['added'])} 个
 - **删除文件**: {len(file_changes['deleted'])} 个
 - **未跟踪文件**: {len(file_changes['untracked'])} 个
 
 """
         
         # 显示具体变更文件（限制数量）
         if file_changes['total_changes'] > 0:
             report += "#### 文件变更详情\n"
             
             for category, files in [
                 ('修改', file_changes['modified']),
                 ('新增', file_changes['added']),
                 ('删除', file_changes['deleted']),
                 ('未跟踪', file_changes['untracked'])
             ]:
                 if files:
                     report += f"\n**{category}文件**:\n"
                     for file in files[:5]:  # 只显示前5个
                         report += f"- `{file}`\n"
                     if len(files) > 5:
                         report += f"- ... 还有 {len(files) - 5} 个文件\n"
                         
         report += f"""
 
 ## 🤖 AI智能协作状态
 
 ### CrewAI多智能体系统
 - **Agent状态**: {'✅ 活跃' if ai_status['agents_active'] else '⚠️ 未激活'}
 - **Agent数量**: {ai_status['total_agents']} 个
 - **完成任务**: {ai_status['completed_tasks']} 个
 - **记忆条目**: {ai_status['memory_entries']} 条
 
 ### 会话摘要
 {ai_status['session_summary']}
 
 ## 💾 备份与维护
 
 ### 项目备份
 """
         
         if backup_info.get('success'):
             report += f"""- **备份状态**: ✅ 成功
 - **备份路径**: `{backup_info['backup_path']}`
 - **备份文件数**: {backup_info['copied_files']} 个
 - **跳过文件数**: {backup_info['skipped_files']} 个
 - **备份大小**: {backup_info['backup_size']}
 """
         else:
             reason = backup_info.get('reason', backup_info.get('error', '未知原因'))
             report += f"- **备份状态**: ❌ 失败 ({reason})\n"
             
         report += f"""
 
 ### 系统维护
 - **临时文件清理**: {'✅ 已执行' if self.default_config['cleanup']['auto_cleanup_temp'] else '⚠️ 已跳过'}
 - **日志文件管理**: {'✅ 已执行' if self.default_config['cleanup']['cleanup_old_logs'] else '⚠️ 已跳过'}
 """
         
         # 添加 Git 推送维护信息
         if push_info:
             push_status = '✅ 已执行' if push_info.get('success') else '❌ 失败'
             report += f"- **Git 推送**: {push_status}\n"
             
         report += f"""
 
 ## 📋 工作总结
 
 ### 本次会话成果
 """
         
         # 根据数据生成总结
         achievements = []
         if git_info['total_commits'] > 0:
             achievements.append(f"完成 {git_info['total_commits']} 次代码提交")
         if file_changes['total_changes'] > 0:
             achievements.append(f"处理 {file_changes['total_changes']} 个文件变更")
         if ai_status['completed_tasks'] > 0:
             achievements.append(f"AI Agent完成 {ai_status['completed_tasks']} 个任务")
         if backup_info.get('success'):
             achievements.append("成功执行项目备份")
         if push_info and push_info.get('success'):
             achievements.append("成功推送到 GitHub 仓库")
             
         if achievements:
             for achievement in achievements:
                 report += f"- ✅ {achievement}\n"
         else:
             report += "- 📝 本次会话主要进行了项目维护和状态检查\n"
             
         report += f"""
 
 ### 下次工作建议
 """
         
         # 生成建议
         suggestions = []
         if file_changes['untracked']:
             suggestions.append("处理未跟踪的文件，决定是否加入版本控制")
         if not ai_status['agents_active']:
             suggestions.append("考虑激活AI Agent系统以提高工作效率")
         if git_info['total_commits'] == 0:
             suggestions.append("及时提交代码变更，保持版本控制的连续性")
         if push_info and not push_info.get('success'):
             suggestions.append("检查 Git 推送配置，确保能正常同步到远程仓库")
             
         if suggestions:
             for suggestion in suggestions:
                 report += f"- 💡 {suggestion}\n"
         else:
             report += "- ✅ 项目状态良好，继续保持当前工作节奏\n"
             
         report += f"""
 
 ## 🔧 系统配置
 
 ### 当前配置
 - **自动备份**: {'启用' if self.default_config['backup']['enable_auto_backup'] else '禁用'}
 - **Git自动提交**: {'启用' if self.default_config['git']['auto_commit'] else '禁用'}
 - **Git推送到远程**: {'启用' if self.default_config['git']['push_to_remote'] else '禁用'}
 - **临时文件清理**: {'启用' if self.default_config['cleanup']['auto_cleanup_temp'] else '禁用'}
 - **备份保留天数**: {self.default_config['backup']['backup_retention_days']} 天
 
 ---
 
 *YDS-Lab AI智能协作系统 - 工作完成处理报告*  
 *生成时间: {session_info['end_time']}*
 """
         
         return report
        
    def save_work_report(self, report_content: str) -> str:
        """保存工作报告"""
        try:
            # 创建报告目录
            reports_dir = self.logs_dir / "工作记录"
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成报告文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"工作完成报告_{timestamp}.md"
            report_path = reports_dir / report_filename
            
            # 保存报告
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
                
            self.logger.info(f"工作报告已保存: {report_path}")
            return str(report_path)
            
        except Exception as e:
            self.logger.error(f"保存工作报告失败: {e}")
            return ""
            
    def perform_finish_process(self) -> Tuple[bool, str]:
        """执行完整的工作完成流程"""
        try:
            print("🏁 YDS-Lab 工作完成处理")
            print("=" * 50)
            
            # 1. 获取会话信息
            session_info = self.get_current_session_info()
            
            # 2. 获取Git提交记录
            git_info = self.get_daily_git_commits()
            
            # 3. 分析文件变更
            file_changes = self.analyze_file_changes()
            
            # 4. 检查AI Agent状态
            ai_status = self.check_ai_agents_status()
            
            # 5. 执行项目备份
            backup_info = self.perform_project_backup()
            
            # 6. 执行 Git 推送
            push_info = self.perform_git_push()
            
            # 7. 清理临时文件
            self.cleanup_temp_files()
            
            # 8. 清理旧日志
            self.cleanup_old_logs()
            
            # 9. 生成工作报告（包含推送信息）
            report_content = self.generate_work_report(
                session_info, git_info, file_changes, ai_status, backup_info, push_info
            )
            
            # 10. 保存报告
            report_path = self.save_work_report(report_content)
            
            # 11. 显示报告
            print(report_content)
            
            success_msg = f"✅ YDS-Lab工作完成处理成功 - 报告已保存至: {report_path}"
            return True, success_msg
            
        except Exception as e:
            error_msg = f"❌ 工作完成处理失败: {e}"
            self.logger.error(error_msg)
            return False, error_msg

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="YDS-Lab工作完成处理系统")
    parser.add_argument("--no-backup", action="store_true", help="跳过项目备份")
    parser.add_argument("--no-cleanup", action="store_true", help="跳过清理操作")
    parser.add_argument("--report-only", action="store_true", help="仅生成报告")
    parser.add_argument("--root", type=str, help="项目根目录路径")
    
    args = parser.parse_args()
    
    project_root = args.root if args.root else "s:/YDS-Lab"
    processor = YDSLabFinishProcessor(project_root=project_root)
    
    # 根据参数调整配置
    if args.no_backup:
        processor.default_config['backup']['enable_auto_backup'] = False
    if args.no_cleanup:
        processor.default_config['cleanup']['auto_cleanup_temp'] = False
        processor.default_config['cleanup']['cleanup_old_logs'] = False
        
    if args.report_only:
        # 仅生成报告模式
        print("📊 YDS-Lab 工作报告生成")
        print("=" * 30)
        
        session_info = processor.get_current_session_info()
        git_info = processor.get_daily_git_commits()
        file_changes = processor.analyze_file_changes()
        ai_status = processor.check_ai_agents_status()
        backup_info = {'success': False, 'reason': 'skipped'}
        
        report_content = processor.generate_work_report(
            session_info, git_info, file_changes, ai_status, backup_info
        )
        
        report_path = processor.save_work_report(report_content)
        print(report_content)
        print(f"\n📄 报告已保存: {report_path}")
        return 0
    else:
        # 完整处理模式
        success, message = processor.perform_finish_process()
        print(f"\n{message}")
        return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())