#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YDS-Lab Git辅助工具
提供Git版本控制的便捷操作和自动化功能
适配YDS-Lab项目结构和AI Agent协作需求
"""

import os
import sys
import subprocess
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import re
import tempfile

# 设置 Git 可执行文件路径
git_executable_paths = [
    r"C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\Common7\IDE\CommonExtensions\Microsoft\TeamFoundation\Team Explorer\Git\cmd\git.exe",
    r"C:\Program Files\Git\bin\git.exe",
    r"C:\Program Files (x86)\Git\bin\git.exe"
]

# 查找可用的 Git 可执行文件
git_executable = None
for path in git_executable_paths:
    if os.path.exists(path):
        git_executable = path
        break

# 设置环境变量
if git_executable:
    os.environ['GIT_PYTHON_GIT_EXECUTABLE'] = git_executable

try:
    import git as gitpython
    from git import Repo, InvalidGitRepositoryError
    GIT_PYTHON_AVAILABLE = True
    print(f"✅ GitPython 已加载，使用 Git: {git_executable}")
except ImportError as e:
    GIT_PYTHON_AVAILABLE = False
    print(f"⚠️ GitPython 导入失败: {e}")
    print("将使用系统 Git 命令")

class GitHelper:
    """Git辅助工具类"""
    
    def __init__(self, project_root: str = None):
        """初始化Git辅助工具"""
        if project_root is None:
            # 从tools/-sub/git_tools向上三级到达项目根目录
            self.project_root = Path(__file__).parent.parent.parent.parent
        else:
            self.project_root = Path(project_root)
        
        # 确保项目根目录存在
        self.project_root = self.project_root.resolve()
        
        # 初始化 Git 仓库对象
        self.repo = None
        if GIT_PYTHON_AVAILABLE:
            try:
                # 检查是否存在 .git 目录
                git_dir = self.project_root / ".git"
                if git_dir.exists():
                    self.repo = Repo(self.project_root)
                    print(f"✅ 使用 GitPython 连接到仓库: {self.project_root}")
                else:
                    print(f"⚠️ 当前目录不是Git仓库: {self.project_root}")
                    # 尝试初始化仓库
                    try:
                        self.repo = Repo.init(self.project_root)
                        print(f"✅ 已初始化新的Git仓库: {self.project_root}")
                    except Exception as e:
                        print(f"❌ 无法初始化Git仓库: {e}")
                        self.repo = None
            except Exception as e:
                print(f"❌ GitPython 连接失败: {e}")
                self.repo = None
        else:
            # 确保在Git仓库中
            self.git_dir = self.project_root / ".git"
            if not self.git_dir.exists():
                print(f"⚠️ 当前目录不是Git仓库: {self.project_root}")
                # 尝试使用系统命令初始化
                try:
                    result = subprocess.run([git_executable, 'init'], 
                                          cwd=self.project_root, 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        print(f"✅ 已使用系统命令初始化Git仓库: {self.project_root}")
                    else:
                        print(f"❌ 初始化Git仓库失败: {result.stderr}")
                except Exception as e:
                    print(f"❌ 无法初始化Git仓库: {e}")
        
        # 配置目录
        self.config_dir = self.project_root / "Struc" / "GeneralOffice" / "config"
        self.logs_dir = self.project_root / "logs" / "git"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Git配置
        self.git_config_file = self.config_dir / "git_config.json"
        
        # 加载配置
        self.load_git_config()
    
    def load_git_config(self) -> Dict[str, Any]:
        """加载Git配置"""
        default_config = {
            'auto_commit': {
                'enabled': False,
                'patterns': ['*.py', '*.md', '*.json', '*.yaml', '*.yml'],
                'exclude_patterns': ['*.log', '*.tmp', '__pycache__/*'],
                'commit_message_template': 'Auto commit: {files_changed} files changed'
            },
            'branch_management': {
                'main_branch': 'main',
                'develop_branch': 'develop',
                'feature_prefix': 'feature/',
                'hotfix_prefix': 'hotfix/',
                'release_prefix': 'release/'
            },
            'commit_rules': {
                'require_message': True,
                'min_message_length': 10,
                'conventional_commits': True,
                'types': ['feat', 'fix', 'docs', 'style', 'refactor', 'test', 'chore']
            },
            'hooks': {
                'pre_commit': True,
                'pre_push': True,
                'commit_msg': True
            }
        }
        
        try:
            if self.git_config_file.exists():
                with open(self.git_config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 合并默认配置
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    self.config = config
            else:
                self.config = default_config
                self.save_git_config()
        except Exception as e:
            print(f"❌ 加载Git配置失败: {e}")
            self.config = default_config
        
        return self.config
    
    def save_git_config(self) -> bool:
        """保存Git配置"""
        try:
            self.config_dir.mkdir(exist_ok=True)
            
            with open(self.git_config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Git配置已保存: {self.git_config_file}")
            return True
            
        except Exception as e:
            print(f"❌ 保存Git配置失败: {e}")
            return False
    
    def run_git_command(self, args: List[str], capture_output: bool = True, 
                       check: bool = True, timeout: int = 30) -> subprocess.CompletedProcess:
        """执行Git命令"""
        if GIT_PYTHON_AVAILABLE and self.repo:
            # 使用 GitPython 执行命令
            try:
                if args[0] == 'status':
                    if '--porcelain' in args:
                        # 返回简洁状态
                        status_output = ""
                        for item in self.repo.index.diff(None):
                            status_output += f"M  {item.a_path}\n"
                        for item in self.repo.index.diff("HEAD"):
                            status_output += f"M  {item.a_path}\n"
                        for item in self.repo.untracked_files:
                            status_output += f"?? {item}\n"
                        
                        # 创建模拟的 CompletedProcess 对象
                        class MockResult:
                            def __init__(self, stdout, stderr="", returncode=0):
                                self.stdout = stdout
                                self.stderr = stderr
                                self.returncode = returncode
                        
                        return MockResult(status_output.strip())
                
                elif args[0] == 'add':
                    if len(args) > 1:
                        if args[1] == '.':
                            self.repo.git.add(A=True)
                        else:
                            for file_path in args[1:]:
                                self.repo.index.add([file_path])
                    return MockResult("")
                
                elif args[0] == 'commit':
                    if '-m' in args:
                        message_idx = args.index('-m') + 1
                        if message_idx < len(args):
                            message = args[message_idx]
                            self.repo.index.commit(message)
                    return MockResult("")
                
                elif args[0] == 'push':
                    origin = self.repo.remote('origin')
                    origin.push()
                    return MockResult("")
                
                elif args[0] == 'log':
                    # 使用 GitPython 获取日志
                    try:
                        # 解析参数
                        max_count = 10
                        pretty_format = None
                        
                        for i, arg in enumerate(args):
                            if arg.startswith('-'):
                                try:
                                    max_count = int(arg[1:])
                                except ValueError:
                                    pass
                            elif arg.startswith('--pretty=format:'):
                                pretty_format = arg.split(':', 1)[1]
                        
                        # 获取提交记录
                        commits = list(self.repo.iter_commits(max_count=max_count))
                        
                        output_lines = []
                        for commit in commits:
                            if pretty_format:
                                # 格式化输出
                                line = pretty_format
                                line = line.replace('%H', commit.hexsha)
                                line = line.replace('%h', commit.hexsha[:7])
                                line = line.replace('%s', commit.message.strip().split('\n')[0])
                                line = line.replace('%an', commit.author.name)
                                line = line.replace('%ad', commit.committed_datetime.strftime('%Y-%m-%d'))
                                output_lines.append(line)
                            else:
                                output_lines.append(f"{commit.hexsha[:7]} {commit.message.strip().split('\n')[0]}")
                        
                        return MockResult('\n'.join(output_lines))
                        
                    except Exception as log_error:
                        print(f"GitPython log 错误: {log_error}")
                        # 回退到系统命令
                        pass
                
                else:
                    # 对于其他命令，使用 GitPython 的 git 对象
                    result = self.repo.git.execute(args)
                    return MockResult(result)
                    
            except Exception as e:
                print(f"❌ GitPython 命令执行失败: {' '.join(args)}")
                print(f"错误: {e}")
                # 如果 GitPython 失败，回退到系统命令
                pass
        
        # 使用系统 Git 命令
        # 确保使用正确的 Git 可执行文件路径
        git_executable = os.environ.get('GIT_PYTHON_GIT_EXECUTABLE')
        if not git_executable:
            # 尝试查找 Git 可执行文件
            git_executable = self._find_git_executable()
            if git_executable:
                os.environ['GIT_PYTHON_GIT_EXECUTABLE'] = git_executable
        
        if git_executable:
            cmd = [git_executable] + args
        else:
            cmd = ['git'] + args
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=capture_output,
                text=True,
                encoding='utf-8',
                timeout=timeout,
                check=check
            )
            return result
        except subprocess.CalledProcessError as e:
            if capture_output:
                print(f"❌ Git命令执行失败: {' '.join(cmd)}")
                print(f"错误输出: {e.stderr}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """获取Git状态"""
        try:
            if GIT_PYTHON_AVAILABLE and self.repo:
                # 使用 GitPython 获取状态
                try:
                    # 获取修改的文件
                    modified = []
                    added = []
                    deleted = []
                    untracked = []
                    
                    # 获取工作区和暂存区的差异
                    for item in self.repo.index.diff(None):
                        if item.change_type == 'M':
                            modified.append(item.a_path)
                        elif item.change_type == 'D':
                            deleted.append(item.a_path)
                    
                    # 获取暂存区和HEAD的差异
                    for item in self.repo.index.diff("HEAD"):
                        if item.change_type == 'A':
                            added.append(item.a_path)
                        elif item.change_type == 'M' and item.a_path not in modified:
                            modified.append(item.a_path)
                        elif item.change_type == 'D' and item.a_path not in deleted:
                            deleted.append(item.a_path)
                    
                    # 获取未跟踪的文件
                    untracked = self.repo.untracked_files
                    
                    # 获取当前分支
                    try:
                        current_branch = self.repo.active_branch.name
                    except:
                        current_branch = "HEAD"
                    
                    return {
                        'current_branch': current_branch,
                        'modified': modified,
                        'added': added,
                        'deleted': deleted,
                        'untracked': untracked,
                        'renamed': [],
                        'clean': len(modified) == 0 and len(added) == 0 and len(deleted) == 0 and len(untracked) == 0,
                        'ahead_count': 0,
                        'behind_count': 0
                    }
                    
                except Exception as git_error:
                    print(f"GitPython 错误: {git_error}")
                    # 如果 GitPython 失败，回退到系统命令
                    pass
            
            # 回退到系统 Git 命令
            result = self.run_git_command(['status', '--porcelain'])
            status_lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
            # 解析状态
            modified = []
            added = []
            deleted = []
            untracked = []
            renamed = []
            
            for line in status_lines:
                if len(line) < 3:
                    continue
                
                status_code = line[:2]
                file_path = line[3:]
                
                if status_code[0] == 'M' or status_code[1] == 'M':
                    modified.append(file_path)
                elif status_code[0] == 'A' or status_code[1] == 'A':
                    added.append(file_path)
                elif status_code[0] == 'D' or status_code[1] == 'D':
                    deleted.append(file_path)
                elif status_code[0] == 'R':
                    renamed.append(file_path)
                elif status_code == '??':
                    untracked.append(file_path)
            
            # 获取当前分支
            try:
                branch_result = self.run_git_command(['branch', '--show-current'])
                current_branch = branch_result.stdout.strip()
            except:
                current_branch = "unknown"
            
            # 获取远程状态
            try:
                self.run_git_command(['fetch', '--dry-run'], capture_output=False)
                ahead_result = self.run_git_command(['rev-list', '--count', 'HEAD', '^origin/' + current_branch])
                behind_result = self.run_git_command(['rev-list', '--count', 'origin/' + current_branch, '^HEAD'])
                
                ahead_count = int(ahead_result.stdout.strip()) if ahead_result.stdout.strip() else 0
                behind_count = int(behind_result.stdout.strip()) if behind_result.stdout.strip() else 0
            except:
                ahead_count = 0
                behind_count = 0
            
            return {
                'current_branch': current_branch,
                'modified': modified,
                'added': added,
                'deleted': deleted,
                'untracked': untracked,
                'renamed': renamed,
                'clean': len(status_lines) == 0,
                'ahead_count': ahead_count,
                'behind_count': behind_count
            }
            
        except Exception as e:
            print(f"❌ 获取Git状态失败: {e}")
            return {
                'current_branch': 'unknown',
                'modified': [],
                'added': [],
                'deleted': [],
                'untracked': [],
                'renamed': [],
                'clean': True,
                'ahead_count': 0,
                'behind_count': 0
            }
    
    def add_files(self, files: List[str] = None, all_files: bool = False) -> bool:
        """添加文件到暂存区"""
        try:
            if all_files:
                self.run_git_command(['add', '.'])
                print("✅ 已添加所有文件到暂存区")
            elif files:
                for file in files:
                    self.run_git_command(['add', file])
                print(f"✅ 已添加 {len(files)} 个文件到暂存区")
            else:
                print("⚠️ 没有指定要添加的文件")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ 添加文件失败: {e}")
            return False
    
    def commit(self, message: str, files: List[str] = None, 
               auto_add: bool = True) -> bool:
        """提交更改"""
        try:
            # 验证提交消息
            if not self.validate_commit_message(message):
                return False
            
            # 自动添加文件
            if auto_add:
                if files:
                    self.add_files(files)
                else:
                    self.add_files(all_files=True)
            
            # 提交
            self.run_git_command(['commit', '-m', message])
            print(f"✅ 提交成功: {message}")
            
            # 记录提交日志
            self.log_commit(message)
            
            return True
            
        except Exception as e:
            print(f"❌ 提交失败: {e}")
            return False
    
    def _find_git_executable(self) -> Optional[str]:
        """查找Git可执行文件"""
        # 已定义的路径
        for path in git_executable_paths:
            if os.path.exists(path):
                return path
        
        # 尝试从PATH环境变量中查找
        import shutil
        git_path = shutil.which('git')
        if git_path:
            return git_path
        
        # 尝试常见的安装路径
        common_paths = [
            r"C:\Program Files\Git\cmd\git.exe",
            r"C:\Program Files (x86)\Git\cmd\git.exe",
            "/usr/bin/git",
            "/usr/local/bin/git",
            "/opt/homebrew/bin/git"
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def validate_commit_message(self, message: str) -> bool:
        """验证提交消息"""
        rules = self.config.get('commit_rules', {})
        
        # 检查消息长度
        min_length = rules.get('min_message_length', 10)
        if len(message) < min_length:
            print(f"❌ 提交消息太短，至少需要 {min_length} 个字符")
            return False
        
        # 检查约定式提交格式
        if rules.get('conventional_commits', False):
            pattern = r'^(feat|fix|docs|style|refactor|test|chore)(\(.+\))?: .+'
            if not re.match(pattern, message):
                types = ', '.join(rules.get('types', []))
                print(f"❌ 提交消息不符合约定式提交格式")
                print(f"格式: <type>(<scope>): <description>")
                print(f"可用类型: {types}")
                return False
        
        return True
    
    def push(self, branch: str = None, force: bool = False) -> bool:
        """推送到远程仓库"""
        try:
            args = ['push']
            
            if force:
                args.append('--force')
            
            if branch:
                args.extend(['origin', branch])
            
            self.run_git_command(args)
            print(f"✅ 推送成功")
            
            return True
            
        except Exception as e:
            print(f"❌ 推送失败: {e}")
            return False
    
    def pull(self, branch: str = None, rebase: bool = False) -> bool:
        """从远程仓库拉取"""
        try:
            args = ['pull']
            
            if rebase:
                args.append('--rebase')
            
            if branch:
                args.extend(['origin', branch])
            
            self.run_git_command(args)
            print(f"✅ 拉取成功")
            
            return True
            
        except Exception as e:
            print(f"❌ 拉取失败: {e}")
            return False
    
    def create_branch(self, branch_name: str, from_branch: str = None) -> bool:
        """创建新分支"""
        try:
            args = ['checkout', '-b', branch_name]
            
            if from_branch:
                args.append(from_branch)
            
            self.run_git_command(args)
            print(f"✅ 创建并切换到分支: {branch_name}")
            
            return True
            
        except Exception as e:
            print(f"❌ 创建分支失败: {e}")
            return False
    
    def switch_branch(self, branch_name: str) -> bool:
        """切换分支"""
        try:
            self.run_git_command(['checkout', branch_name])
            print(f"✅ 切换到分支: {branch_name}")
            
            return True
            
        except Exception as e:
            print(f"❌ 切换分支失败: {e}")
            return False
    
    def delete_branch(self, branch_name: str, force: bool = False) -> bool:
        """删除分支"""
        try:
            args = ['branch']
            
            if force:
                args.append('-D')
            else:
                args.append('-d')
            
            args.append(branch_name)
            
            self.run_git_command(args)
            print(f"✅ 删除分支: {branch_name}")
            
            return True
            
        except Exception as e:
            print(f"❌ 删除分支失败: {e}")
            return False
    
    def list_branches(self, remote: bool = False) -> List[str]:
        """列出分支"""
        try:
            args = ['branch']
            
            if remote:
                args.append('-r')
            
            result = self.run_git_command(args)
            branches = []
            
            for line in result.stdout.strip().split('\n'):
                branch = line.strip()
                if branch.startswith('*'):
                    branch = branch[1:].strip()
                if branch and not branch.startswith('origin/HEAD'):
                    branches.append(branch)
            
            return branches
            
        except Exception as e:
            print(f"❌ 获取分支列表失败: {e}")
            return []
    
    def get_log(self, count: int = 10, oneline: bool = True) -> List[Dict[str, str]]:
        """获取提交日志"""
        try:
            args = ['log', f'-{count}']
            
            if oneline:
                args.append('--oneline')
            else:
                args.extend(['--pretty=format:%H|%an|%ad|%s', '--date=short'])
            
            result = self.run_git_command(args)
            commits = []
            
            for line in result.stdout.strip().split('\n'):
                if oneline:
                    parts = line.split(' ', 1)
                    if len(parts) == 2:
                        commits.append({
                            'hash': parts[0],
                            'message': parts[1]
                        })
                else:
                    parts = line.split('|')
                    if len(parts) == 4:
                        commits.append({
                            'hash': parts[0],
                            'author': parts[1],
                            'date': parts[2],
                            'message': parts[3]
                        })
            
            return commits
            
        except Exception as e:
            print(f"❌ 获取提交日志失败: {e}")
            return []
    
    def create_tag(self, tag_name: str, message: str = None) -> bool:
        """创建标签"""
        try:
            args = ['tag']
            
            if message:
                args.extend(['-a', tag_name, '-m', message])
            else:
                args.append(tag_name)
            
            self.run_git_command(args)
            print(f"✅ 创建标签: {tag_name}")
            
            return True
            
        except Exception as e:
            print(f"❌ 创建标签失败: {e}")
            return False
    
    def list_tags(self) -> List[str]:
        """列出标签"""
        try:
            result = self.run_git_command(['tag', '-l'])
            tags = result.stdout.strip().split('\n') if result.stdout.strip() else []
            return tags
            
        except Exception as e:
            print(f"❌ 获取标签列表失败: {e}")
            return []
    
    def stash_changes(self, message: str = None) -> bool:
        """暂存更改"""
        try:
            args = ['stash']
            
            if message:
                args.extend(['push', '-m', message])
            
            self.run_git_command(args)
            print(f"✅ 暂存更改成功")
            
            return True
            
        except Exception as e:
            print(f"❌ 暂存更改失败: {e}")
            return False
    
    def stash_pop(self) -> bool:
        """恢复暂存的更改"""
        try:
            self.run_git_command(['stash', 'pop'])
            print(f"✅ 恢复暂存更改成功")
            
            return True
            
        except Exception as e:
            print(f"❌ 恢复暂存更改失败: {e}")
            return False
    
    def list_stashes(self) -> List[str]:
        """列出暂存"""
        try:
            result = self.run_git_command(['stash', 'list'])
            stashes = result.stdout.strip().split('\n') if result.stdout.strip() else []
            return stashes
            
        except Exception as e:
            print(f"❌ 获取暂存列表失败: {e}")
            return []
    
    def diff(self, file_path: str = None, staged: bool = False) -> str:
        """查看差异"""
        try:
            args = ['diff']
            
            if staged:
                args.append('--staged')
            
            if file_path:
                args.append(file_path)
            
            result = self.run_git_command(args)
            return result.stdout
            
        except Exception as e:
            print(f"❌ 查看差异失败: {e}")
            return ""
    
    def reset_file(self, file_path: str, hard: bool = False) -> bool:
        """重置文件"""
        try:
            if hard:
                self.run_git_command(['checkout', 'HEAD', '--', file_path])
            else:
                self.run_git_command(['reset', 'HEAD', file_path])
            
            print(f"✅ 重置文件成功: {file_path}")
            return True
            
        except Exception as e:
            print(f"❌ 重置文件失败: {e}")
            return False
    
    def auto_commit_changes(self) -> bool:
        """自动提交更改"""
        if not self.config.get('auto_commit', {}).get('enabled', False):
            return False
        
        try:
            status = self.get_status()
            
            if status.get('clean', True):
                print("📝 没有需要提交的更改")
                return True
            
            # 获取更改的文件
            changed_files = (
                status.get('modified', []) + 
                status.get('added', []) + 
                status.get('deleted', []) +
                status.get('untracked', [])
            )
            
            # 过滤文件
            patterns = self.config['auto_commit'].get('patterns', [])
            exclude_patterns = self.config['auto_commit'].get('exclude_patterns', [])
            
            filtered_files = []
            for file in changed_files:
                # 检查包含模式
                if patterns:
                    match_pattern = False
                    for pattern in patterns:
                        if self._match_pattern(file, pattern):
                            match_pattern = True
                            break
                    if not match_pattern:
                        continue
                
                # 检查排除模式
                exclude_file = False
                for pattern in exclude_patterns:
                    if self._match_pattern(file, pattern):
                        exclude_file = True
                        break
                if exclude_file:
                    continue
                
                filtered_files.append(file)
            
            if not filtered_files:
                print("📝 没有符合自动提交条件的文件")
                return True
            
            # 生成提交消息
            template = self.config['auto_commit'].get('commit_message_template', 
                                                    'Auto commit: {files_changed} files changed')
            message = template.format(files_changed=len(filtered_files))
            
            # 提交
            return self.commit(message, filtered_files)
            
        except Exception as e:
            print(f"❌ 自动提交失败: {e}")
            return False
    
    def _match_pattern(self, file_path: str, pattern: str) -> bool:
        """匹配文件模式"""
        import fnmatch
        return fnmatch.fnmatch(file_path, pattern)
    
    def log_commit(self, message: str):
        """记录提交日志"""
        try:
            log_file = self.logs_dir / "commits.log"
            
            with open(log_file, 'a', encoding='utf-8') as f:
                timestamp = datetime.now().isoformat()
                f.write(f"{timestamp} - {message}\n")
                
        except Exception as e:
            print(f"⚠️ 记录提交日志失败: {e}")
    
    def generate_changelog(self, from_tag: str = None, to_tag: str = None) -> str:
        """生成变更日志"""
        try:
            args = ['log', '--pretty=format:- %s (%h)']
            
            if from_tag and to_tag:
                args.append(f"{from_tag}..{to_tag}")
            elif from_tag:
                args.append(f"{from_tag}..HEAD")
            
            result = self.run_git_command(args)
            
            changelog = f"# 变更日志\n\n"
            changelog += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            if from_tag:
                changelog += f"## 从 {from_tag} 到 {to_tag or 'HEAD'}\n\n"
            else:
                changelog += f"## 所有提交\n\n"
            
            changelog += result.stdout
            
            return changelog
            
        except Exception as e:
            print(f"❌ 生成变更日志失败: {e}")
            return ""
    
    def setup_hooks(self) -> bool:
        """设置Git钩子"""
        try:
            hooks_dir = self.git_dir / "hooks"
            hooks_dir.mkdir(exist_ok=True)
            
            # Pre-commit hook
            if self.config.get('hooks', {}).get('pre_commit', False):
                pre_commit_hook = hooks_dir / "pre-commit"
                pre_commit_content = """#!/bin/sh
# YDS-Lab Pre-commit Hook
echo "Running pre-commit checks..."

# 检查Python语法
python -m py_compile $(git diff --cached --name-only --diff-filter=ACM | grep '\\.py$')
if [ $? -ne 0 ]; then
    echo "Python syntax check failed"
    exit 1
fi

echo "Pre-commit checks passed"
exit 0
"""
                with open(pre_commit_hook, 'w', encoding='utf-8') as f:
                    f.write(pre_commit_content)
                
                # 设置执行权限
                if os.name != 'nt':  # 非Windows系统
                    os.chmod(pre_commit_hook, 0o755)
            
            print("✅ Git钩子设置完成")
            return True
            
        except Exception as e:
            print(f"❌ 设置Git钩子失败: {e}")
            return False

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='YDS-Lab Git辅助工具')
    parser.add_argument('--project-root', help='指定项目根目录路径')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 状态命令
    subparsers.add_parser('status', help='查看Git状态')
    
    # 添加命令
    add_parser = subparsers.add_parser('add', help='添加文件到暂存区')
    add_parser.add_argument('files', nargs='*', help='要添加的文件')
    add_parser.add_argument('--all', action='store_true', help='添加所有文件')
    
    # 提交命令
    commit_parser = subparsers.add_parser('commit', help='提交更改')
    commit_parser.add_argument('message', help='提交消息')
    commit_parser.add_argument('--files', nargs='*', help='要提交的文件')
    commit_parser.add_argument('--no-add', action='store_true', help='不自动添加文件')
    
    # 推送命令
    push_parser = subparsers.add_parser('push', help='推送到远程仓库')
    push_parser.add_argument('--branch', help='指定分支')
    push_parser.add_argument('--force', action='store_true', help='强制推送')
    
    # 拉取命令
    pull_parser = subparsers.add_parser('pull', help='从远程仓库拉取')
    pull_parser.add_argument('--branch', help='指定分支')
    pull_parser.add_argument('--rebase', action='store_true', help='使用rebase')
    
    # 分支命令
    branch_parser = subparsers.add_parser('branch', help='分支管理')
    branch_parser.add_argument('--list', action='store_true', help='列出分支')
    branch_parser.add_argument('--create', help='创建新分支')
    branch_parser.add_argument('--switch', help='切换分支')
    branch_parser.add_argument('--delete', help='删除分支')
    branch_parser.add_argument('--from', dest='from_branch', help='从指定分支创建')
    branch_parser.add_argument('--force', action='store_true', help='强制删除')
    
    # 日志命令
    log_parser = subparsers.add_parser('log', help='查看提交日志')
    log_parser.add_argument('--count', type=int, default=10, help='显示条数')
    log_parser.add_argument('--detailed', action='store_true', help='详细信息')
    
    # 标签命令
    tag_parser = subparsers.add_parser('tag', help='标签管理')
    tag_parser.add_argument('--list', action='store_true', help='列出标签')
    tag_parser.add_argument('--create', help='创建标签')
    tag_parser.add_argument('--message', help='标签消息')
    
    # 暂存命令
    stash_parser = subparsers.add_parser('stash', help='暂存管理')
    stash_parser.add_argument('--list', action='store_true', help='列出暂存')
    stash_parser.add_argument('--save', help='保存暂存')
    stash_parser.add_argument('--pop', action='store_true', help='恢复暂存')
    
    # 差异命令
    diff_parser = subparsers.add_parser('diff', help='查看差异')
    diff_parser.add_argument('file', nargs='?', help='指定文件')
    diff_parser.add_argument('--staged', action='store_true', help='查看暂存区差异')
    
    # 自动提交命令
    subparsers.add_parser('auto-commit', help='自动提交更改')
    
    # 变更日志命令
    changelog_parser = subparsers.add_parser('changelog', help='生成变更日志')
    changelog_parser.add_argument('--from-tag', help='起始标签')
    changelog_parser.add_argument('--to-tag', help='结束标签')
    changelog_parser.add_argument('--output', help='输出文件')
    
    # 钩子命令
    subparsers.add_parser('setup-hooks', help='设置Git钩子')
    
    args = parser.parse_args()
    
    git_helper = GitHelper(args.project_root)
    
    if args.command == 'status':
        status = git_helper.get_status()
        print(f"📊 Git状态:")
        print(f"  当前分支: {status.get('current_branch', 'unknown')}")
        print(f"  是否干净: {'是' if status.get('clean', False) else '否'}")
        
        if status.get('ahead_count', 0) > 0:
            print(f"  领先远程: {status['ahead_count']} 个提交")
        if status.get('behind_count', 0) > 0:
            print(f"  落后远程: {status['behind_count']} 个提交")
        
        if status.get('modified'):
            print(f"  已修改: {len(status['modified'])} 个文件")
        if status.get('added'):
            print(f"  已添加: {len(status['added'])} 个文件")
        if status.get('deleted'):
            print(f"  已删除: {len(status['deleted'])} 个文件")
        if status.get('untracked'):
            print(f"  未跟踪: {len(status['untracked'])} 个文件")
        
    elif args.command == 'add':
        if args.all:
            success = git_helper.add_files(all_files=True)
        elif args.files:
            success = git_helper.add_files(args.files)
        else:
            print("❌ 请指定要添加的文件或使用 --all")
            success = False
        
        if not success:
            sys.exit(1)
        
    elif args.command == 'commit':
        success = git_helper.commit(
            args.message, 
            args.files, 
            auto_add=not args.no_add
        )
        if not success:
            sys.exit(1)
        
    elif args.command == 'push':
        success = git_helper.push(args.branch, args.force)
        if not success:
            sys.exit(1)
        
    elif args.command == 'pull':
        success = git_helper.pull(args.branch, args.rebase)
        if not success:
            sys.exit(1)
        
    elif args.command == 'branch':
        if args.list:
            branches = git_helper.list_branches()
            print("📋 本地分支:")
            for branch in branches:
                print(f"  {branch}")
        elif args.create:
            success = git_helper.create_branch(args.create, args.from_branch)
            if not success:
                sys.exit(1)
        elif args.switch:
            success = git_helper.switch_branch(args.switch)
            if not success:
                sys.exit(1)
        elif args.delete:
            success = git_helper.delete_branch(args.delete, args.force)
            if not success:
                sys.exit(1)
        else:
            print("❌ 请指定分支操作")
        
    elif args.command == 'log':
        commits = git_helper.get_log(args.count, not args.detailed)
        print(f"📜 提交日志 (最近 {len(commits)} 条):")
        for commit in commits:
            if args.detailed:
                print(f"  {commit['hash'][:8]} - {commit['author']} ({commit['date']})")
                print(f"    {commit['message']}")
            else:
                print(f"  {commit['hash']} {commit['message']}")
        
    elif args.command == 'tag':
        if args.list:
            tags = git_helper.list_tags()
            print(f"🏷️ 标签列表 ({len(tags)} 个):")
            for tag in tags:
                print(f"  {tag}")
        elif args.create:
            success = git_helper.create_tag(args.create, args.message)
            if not success:
                sys.exit(1)
        else:
            print("❌ 请指定标签操作")
        
    elif args.command == 'stash':
        if args.list:
            stashes = git_helper.list_stashes()
            print(f"📦 暂存列表 ({len(stashes)} 个):")
            for stash in stashes:
                print(f"  {stash}")
        elif args.save:
            success = git_helper.stash_changes(args.save)
            if not success:
                sys.exit(1)
        elif args.pop:
            success = git_helper.stash_pop()
            if not success:
                sys.exit(1)
        else:
            print("❌ 请指定暂存操作")
        
    elif args.command == 'diff':
        diff_output = git_helper.diff(args.file, args.staged)
        if diff_output:
            print("📝 差异内容:")
            print(diff_output)
        else:
            print("📝 没有差异")
        
    elif args.command == 'auto-commit':
        success = git_helper.auto_commit_changes()
        if not success:
            sys.exit(1)
        
    elif args.command == 'changelog':
        changelog = git_helper.generate_changelog(args.from_tag, args.to_tag)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(changelog)
            print(f"✅ 变更日志已保存: {args.output}")
        else:
            print(changelog)
        
    elif args.command == 'setup-hooks':
        success = git_helper.setup_hooks()
        if not success:
            sys.exit(1)
        
    else:
        # 默认显示状态
        print("🔧 YDS-Lab Git辅助工具")
        print("=" * 50)
        
        status = git_helper.get_status()
        print(f"当前分支: {status.get('current_branch', 'unknown')}")
        print(f"仓库状态: {'干净' if status.get('clean', False) else '有未提交更改'}")
        
        if not status.get('clean', True):
            total_changes = (
                len(status.get('modified', [])) +
                len(status.get('added', [])) +
                len(status.get('deleted', [])) +
                len(status.get('untracked', []))
            )
            print(f"待处理文件: {total_changes} 个")

if __name__ == "__main__":
    main()