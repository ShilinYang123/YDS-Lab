#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YDS-Lab 自动Git提交工具

功能：
- 自动检测文件变更
- 智能生成提交信息
- 批量提交代码
- 推送到远程仓库
- 提交历史管理

适配YDS-Lab项目Git工作流需求
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging
import re

class YDSLabAutoPush:
    """YDS-Lab自动Git提交工具"""
    
    def __init__(self, project_root: str = "s:/YDS-Lab"):
        self.project_root = Path(project_root)
        self.git_dir = self.project_root / ".git"
        
        # 设置日志
        self.setup_logging()
        
        # 检查Git仓库
        if not self.is_git_repository():
            self.logger.error("当前目录不是Git仓库")
            raise ValueError("当前目录不是Git仓库")
        
        # 提交信息模板
        self.commit_templates = {
            'feat': '新功能',
            'fix': '修复',
            'docs': '文档',
            'style': '格式',
            'refactor': '重构',
            'test': '测试',
            'chore': '构建'
        }
        
        # 文件类型映射
        self.file_type_mapping = {
            '.py': 'Python代码',
            '.js': 'JavaScript代码',
            '.html': 'HTML文件',
            '.css': 'CSS样式',
            '.md': '文档',
            '.json': '配置文件',
            '.yaml': '配置文件',
            '.yml': '配置文件',
            '.txt': '文本文件'
        }
        # 大文件与黑名单后缀保护阈值（>10MB + 黑名单后缀则阻止提交）
        self.large_file_threshold = 10 * 1024 * 1024
        self.blacklist_exts = {'.exe', '.zip', '.7z', '.tar', '.iso'}
        
    def setup_logging(self):
        """设置日志系统"""
        try:
            logs_dir = self.project_root / "Struc" / "GeneralOffice" / "logs"
            logs_dir.mkdir(parents=True, exist_ok=True)
            
            log_file = logs_dir / "auto_push.log"
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(log_file, encoding='utf-8'),
                    logging.StreamHandler(sys.stdout)
                ]
            )
            
            self.logger = logging.getLogger(__name__)
            self.logger.info("自动Git提交工具初始化")
            
        except Exception as e:
            print(f"日志系统初始化失败: {e}")
            self.logger = logging.getLogger(__name__)
    
    def is_git_repository(self) -> bool:
        """检查是否为Git仓库"""
        return self.git_dir.exists() and self.git_dir.is_dir()
    
    def run_git_command(self, command: List[str]) -> Tuple[bool, str, str]:
        """执行Git命令"""
        try:
            result = subprocess.run(
                ['git'] + command,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            success = result.returncode == 0
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()
            
            if success:
                self.logger.debug(f"Git命令成功: git {' '.join(command)}")
            else:
                self.logger.error(f"Git命令失败: git {' '.join(command)}, 错误: {stderr}")
            
            return success, stdout, stderr
            
        except Exception as e:
            self.logger.error(f"执行Git命令异常: {e}")
            return False, "", str(e)
    
    def get_status(self) -> Dict[str, List[str]]:
        """获取Git状态"""
        success, stdout, stderr = self.run_git_command(['status', '--porcelain'])
        
        if not success:
            return {}
        
        status = {
            'modified': [],
            'added': [],
            'deleted': [],
            'untracked': []
        }
        
        for line in stdout.split('\n'):
            if not line.strip():
                continue
            
            status_code = line[:2]
            file_path = line[3:].strip()
            
            if status_code.startswith('M'):
                status['modified'].append(file_path)
            elif status_code.startswith('A'):
                status['added'].append(file_path)
            elif status_code.startswith('D'):
                status['deleted'].append(file_path)
            elif status_code.startswith('??'):
                status['untracked'].append(file_path)
        
        return status
    
    def generate_commit_message(self, status: Dict[str, List[str]]) -> str:
        """智能生成提交信息"""
        if not any(status.values()):
            return "chore: 无变更"
        
        # 分析文件变更类型
        all_files = []
        for file_list in status.values():
            all_files.extend(file_list)
        
        # 统计文件类型
        file_types = {}
        for file_path in all_files:
            ext = Path(file_path).suffix.lower()
            file_type = self.file_type_mapping.get(ext, '其他文件')
            file_types[file_type] = file_types.get(file_type, 0) + 1
        
        # 生成提交信息
        if len(status['added']) > 0 and len(status['modified']) == 0:
            commit_type = 'feat'
            main_type = max(file_types.items(), key=lambda x: x[1])[0]
            message = f"新增{main_type}"
        elif len(status['modified']) > 0:
            commit_type = 'fix' if any('.py' in f for f in status['modified']) else 'docs'
            main_type = max(file_types.items(), key=lambda x: x[1])[0]
            message = f"更新{main_type}"
        elif len(status['deleted']) > 0:
            commit_type = 'chore'
            message = "删除文件"
        else:
            commit_type = 'chore'
            message = "代码整理"
        
        # 添加详细信息
        details = []
        if status['added']:
            details.append(f"新增{len(status['added'])}个文件")
        if status['modified']:
            details.append(f"修改{len(status['modified'])}个文件")
        if status['deleted']:
            details.append(f"删除{len(status['deleted'])}个文件")
        
        if details:
            message += f" ({', '.join(details)})"
        
        return f"{commit_type}: {message}"
    
    def add_all_changes(self) -> bool:
        """添加所有变更到暂存区"""
        success, stdout, stderr = self.run_git_command(['add', '.'])
        
        if success:
            self.logger.info("所有变更已添加到暂存区")
        else:
            self.logger.error(f"添加变更失败: {stderr}")
        
        return success
    
    def commit_changes(self, message: str) -> bool:
        """提交变更"""
        success, stdout, stderr = self.run_git_command(['commit', '-m', message])
        
        if success:
            self.logger.info(f"提交成功: {message}")
        else:
            self.logger.error(f"提交失败: {stderr}")
        
        return success
    
    def push_to_remote(self, remote: str = 'origin', branch: str = 'main') -> bool:
        """推送到远程仓库"""
        success, stdout, stderr = self.run_git_command(['push', remote, branch])
        
        if success:
            self.logger.info(f"推送成功到 {remote}/{branch}")
        else:
            self.logger.error(f"推送失败: {stderr}")
        
        return success
    
    def get_current_branch(self) -> str:
        """获取当前分支名"""
        success, stdout, stderr = self.run_git_command(['branch', '--show-current'])
        
        if success:
            return stdout.strip()
        else:
            return 'main'  # 默认分支

    def scan_blocking_files(self, status: Dict[str, List[str]]) -> List[Tuple[str, int, str]]:
        """扫描将要提交的文件列表，找出超过阈值且在黑名单后缀中的文件。
        返回 [(relative_path, size_bytes, ext), ...]
        """
        candidates: List[Tuple[str, int, str]] = []
        check_keys = ['untracked', 'added', 'modified']
        for key in check_keys:
            for rel in status.get(key, []):
                p = self.project_root / rel
                ext = p.suffix.lower()
                try:
                    size = p.stat().st_size if p.exists() else 0
                except Exception:
                    size = 0
                if ext in self.blacklist_exts and size > self.large_file_threshold:
                    candidates.append((rel, size, ext))
        return candidates
    
    def auto_push(self, message: str = None, remote: str = 'origin', 
                  push: bool = True) -> bool:
        """自动提交并推送"""
        try:
            self.logger.info("开始自动Git提交流程")
            
            # 获取状态
            status = self.get_status()
            
            if not any(status.values()):
                self.logger.info("没有变更需要提交")
                return True
            
            # 显示状态
            self.logger.info("检测到以下变更:")
            for status_type, files in status.items():
                if files:
                    self.logger.info(f"  {status_type}: {len(files)} 个文件")
            # 安全保护：提交前检查大文件/黑名单后缀
            blocked = self.scan_blocking_files(status)
            if blocked:
                self.logger.error("检测到超限或黑名单后缀的大文件，已阻止提交：")
                for rel, size, ext in blocked:
                    try:
                        mb = size / 1024 / 1024
                    except Exception:
                        mb = 0
                    self.logger.error(f"  - {rel} ({ext}, {mb:.1f} MB)")
                self.logger.error("请将安装包/归档文件移至 downloads/ 目录（该目录已在 .gitignore 中被忽略），或改用 Git LFS 管理。")
                return False
            
            # 添加变更
            if not self.add_all_changes():
                return False
            
            # 生成提交信息
            if not message:
                message = self.generate_commit_message(status)
            
            # 提交变更
            if not self.commit_changes(message):
                return False
            
            # 推送到远程
            if push:
                current_branch = self.get_current_branch()
                if not self.push_to_remote(remote, current_branch):
                    self.logger.warning("推送失败，但本地提交成功")
                    return True
            
            self.logger.info("自动Git提交流程完成")
            return True
            
        except Exception as e:
            self.logger.error(f"自动提交过程中发生异常: {e}")
            return False
    
    def get_commit_history(self, count: int = 10) -> List[Dict]:
        """获取提交历史"""
        success, stdout, stderr = self.run_git_command([
            'log', f'-{count}', '--pretty=format:%H|%an|%ad|%s', '--date=short'
        ])
        
        if not success:
            return []
        
        history = []
        for line in stdout.split('\n'):
            if not line.strip():
                continue
            
            parts = line.split('|', 3)
            if len(parts) == 4:
                history.append({
                    'hash': parts[0],
                    'author': parts[1],
                    'date': parts[2],
                    'message': parts[3]
                })
        
        return history

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='YDS-Lab自动Git提交工具')
    parser.add_argument('--message', '-m', help='提交信息')
    parser.add_argument('--remote', '-r', default='origin', help='远程仓库名')
    parser.add_argument('--no-push', action='store_true', help='不推送到远程')
    parser.add_argument('--status', action='store_true', help='显示Git状态')
    parser.add_argument('--history', action='store_true', help='显示提交历史')
    
    args = parser.parse_args()
    
    try:
        auto_push = YDSLabAutoPush()
        
        if args.status:
            status = auto_push.get_status()
            print("Git状态:")
            for status_type, files in status.items():
                if files:
                    print(f"  {status_type}:")
                    for file in files:
                        print(f"    - {file}")
            return
        
        if args.history:
            history = auto_push.get_commit_history()
            print("提交历史:")
            for commit in history:
                print(f"  {commit['date']} - {commit['message']} ({commit['author']})")
            return
        
        # 执行自动提交
        success = auto_push.auto_push(
            message=args.message,
            remote=args.remote,
            push=not args.no_push
        )
        
        if success:
            print("自动提交成功!")
        else:
            print("自动提交失败!")
            sys.exit(1)
            
    except Exception as e:
        print(f"程序执行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()