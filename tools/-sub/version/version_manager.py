#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YDS-Lab 版本管理工具
提供项目版本控制、发布管理、变更跟踪和标签管理功能
适配YDS-Lab项目结构和AI Agent协作需求
"""

import os
import sys
import json
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, asdict
from enum import Enum
import semantic_version
import tempfile
import shutil

try:
    import git
    from git import Repo, InvalidGitRepositoryError
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

class VersionType(Enum):
    """版本类型枚举"""
    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"
    PRERELEASE = "prerelease"
    BUILD = "build"

class ReleaseType(Enum):
    """发布类型枚举"""
    ALPHA = "alpha"
    BETA = "beta"
    RC = "rc"
    STABLE = "stable"

class ChangeType(Enum):
    """变更类型枚举"""
    FEATURE = "feat"
    FIX = "fix"
    DOCS = "docs"
    STYLE = "style"
    REFACTOR = "refactor"
    PERF = "perf"
    TEST = "test"
    CHORE = "chore"
    BREAKING = "breaking"

@dataclass
class VersionInfo:
    """版本信息"""
    version: str
    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None
    build: Optional[str] = None
    tag: Optional[str] = None
    commit_hash: Optional[str] = None
    commit_date: Optional[datetime] = None
    release_date: Optional[datetime] = None
    release_type: Optional[ReleaseType] = None
    changelog: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ChangelogEntry:
    """变更日志条目"""
    change_type: ChangeType
    scope: Optional[str]
    description: str
    breaking_change: bool = False
    commit_hash: Optional[str] = None
    author: Optional[str] = None
    date: Optional[datetime] = None
    
    def to_markdown(self) -> str:
        """转换为Markdown格式"""
        prefix = "⚠️ BREAKING CHANGE: " if self.breaking_change else ""
        scope_str = f"({self.scope})" if self.scope else ""
        
        type_emoji = {
            ChangeType.FEATURE: "✨",
            ChangeType.FIX: "🐛",
            ChangeType.DOCS: "📚",
            ChangeType.STYLE: "💄",
            ChangeType.REFACTOR: "♻️",
            ChangeType.PERF: "⚡",
            ChangeType.TEST: "✅",
            ChangeType.CHORE: "🔧",
            ChangeType.BREAKING: "💥"
        }
        
        emoji = type_emoji.get(self.change_type, "📝")
        return f"- {emoji} {prefix}{self.change_type.value}{scope_str}: {self.description}"

class VersionManager:
    """版本管理器"""
    
    def __init__(self, project_root: str = None):
        """初始化版本管理器"""
        if project_root is None:
            self.project_root = Path(__file__).parent.parent.parent
        else:
            self.project_root = Path(project_root)
        
        # 版本管理目录
        self.version_dir = self.project_root / "versions"
        self.config_dir = self.version_dir / "config"
        self.releases_dir = self.version_dir / "releases"
        self.changelogs_dir = self.version_dir / "changelogs"
        
        # 创建目录
        for directory in [self.version_dir, self.config_dir, self.releases_dir, self.changelogs_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # 配置文件
        self.config_file = self.config_dir / "version_config.json"
        self.version_file = self.project_root / "VERSION"
        self.package_json = self.project_root / "package.json"
        self.setup_py = self.project_root / "setup.py"
        self.pyproject_toml = self.project_root / "pyproject.toml"
        
        # Git仓库
        self.repo = None
        if GIT_AVAILABLE:
            try:
                self.repo = Repo(self.project_root)
            except InvalidGitRepositoryError:
                self.logger = logging.getLogger('yds_lab.version_manager')
                self.logger.warning("不是Git仓库，某些功能将不可用")
        
        # 设置日志
        self.logger = logging.getLogger('yds_lab.version_manager')
        
        # 加载配置
        self._load_config()
        
        # 当前版本信息
        self.current_version = self._get_current_version()
    
    def _load_config(self):
        """加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except Exception as e:
                self.logger.error(f"加载配置失败: {e}")
                self.config = {}
        else:
            self.config = {
                'version_format': 'semantic',  # semantic, simple, custom
                'tag_prefix': 'v',
                'auto_tag': True,
                'auto_changelog': True,
                'changelog_format': 'conventional',  # conventional, simple
                'release_branch': 'main',
                'develop_branch': 'develop',
                'hotfix_prefix': 'hotfix/',
                'feature_prefix': 'feature/',
                'release_prefix': 'release/',
                'commit_message_format': '{type}({scope}): {description}',
                'version_files': [
                    'VERSION',
                    'package.json',
                    'setup.py',
                    'pyproject.toml'
                ],
                'pre_release_hook': None,
                'post_release_hook': None,
                'notification_webhook': None
            }
            self._save_config()
    
    def _save_config(self):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
    
    def _get_current_version(self) -> Optional[VersionInfo]:
        """获取当前版本信息"""
        version_str = None
        
        # 从VERSION文件读取
        if self.version_file.exists():
            try:
                version_str = self.version_file.read_text().strip()
            except Exception:
                pass
        
        # 从package.json读取
        if not version_str and self.package_json.exists():
            try:
                with open(self.package_json, 'r', encoding='utf-8') as f:
                    package_data = json.load(f)
                    version_str = package_data.get('version')
            except Exception:
                pass
        
        # 从Git标签读取
        if not version_str and self.repo:
            try:
                tags = sorted(self.repo.tags, key=lambda t: t.commit.committed_date, reverse=True)
                if tags:
                    latest_tag = tags[0]
                    version_str = latest_tag.name
                    if version_str.startswith(self.config.get('tag_prefix', 'v')):
                        version_str = version_str[len(self.config.get('tag_prefix', 'v')):]
            except Exception:
                pass
        
        # 默认版本
        if not version_str:
            version_str = "0.1.0"
        
        return self._parse_version(version_str)
    
    def _parse_version(self, version_str: str) -> Optional[VersionInfo]:
        """解析版本字符串"""
        try:
            # 清理版本字符串
            version_str = version_str.strip()
            if version_str.startswith('v'):
                version_str = version_str[1:]
            
            # 使用semantic_version解析
            version = semantic_version.Version(version_str)
            
            # 获取Git信息
            commit_hash = None
            commit_date = None
            tag = None
            
            if self.repo:
                try:
                    # 查找对应的标签
                    tag_name = f"{self.config.get('tag_prefix', 'v')}{version_str}"
                    for repo_tag in self.repo.tags:
                        if repo_tag.name == tag_name:
                            tag = tag_name
                            commit_hash = repo_tag.commit.hexsha[:8]
                            commit_date = datetime.fromtimestamp(repo_tag.commit.committed_date)
                            break
                    
                    # 如果没有找到标签，使用当前提交
                    if not commit_hash:
                        commit_hash = self.repo.head.commit.hexsha[:8]
                        commit_date = datetime.fromtimestamp(self.repo.head.commit.committed_date)
                
                except Exception:
                    pass
            
            # 确定发布类型
            release_type = ReleaseType.STABLE
            if version.prerelease:
                prerelease_str = '.'.join(version.prerelease)
                if 'alpha' in prerelease_str:
                    release_type = ReleaseType.ALPHA
                elif 'beta' in prerelease_str:
                    release_type = ReleaseType.BETA
                elif 'rc' in prerelease_str:
                    release_type = ReleaseType.RC
            
            return VersionInfo(
                version=str(version),
                major=version.major,
                minor=version.minor,
                patch=version.patch,
                prerelease='.'.join(version.prerelease) if version.prerelease else None,
                build='.'.join(version.build) if version.build else None,
                tag=tag,
                commit_hash=commit_hash,
                commit_date=commit_date,
                release_type=release_type
            )
        
        except Exception as e:
            self.logger.error(f"解析版本失败 {version_str}: {e}")
            return None
    
    def bump_version(self, version_type: VersionType, prerelease: str = None) -> Optional[VersionInfo]:
        """升级版本"""
        if not self.current_version:
            self.logger.error("无法获取当前版本")
            return None
        
        try:
            current = semantic_version.Version(self.current_version.version)
            
            if version_type == VersionType.MAJOR:
                new_version = current.next_major()
            elif version_type == VersionType.MINOR:
                new_version = current.next_minor()
            elif version_type == VersionType.PATCH:
                new_version = current.next_patch()
            elif version_type == VersionType.PRERELEASE:
                if prerelease:
                    # 创建预发布版本
                    if current.prerelease:
                        # 升级现有预发布版本
                        prerelease_parts = list(current.prerelease)
                        if len(prerelease_parts) >= 2 and prerelease_parts[-1].isdigit():
                            prerelease_parts[-1] = str(int(prerelease_parts[-1]) + 1)
                        else:
                            prerelease_parts.append('1')
                        new_version = semantic_version.Version(
                            f"{current.major}.{current.minor}.{current.patch}-{'.'.join(prerelease_parts)}"
                        )
                    else:
                        new_version = semantic_version.Version(
                            f"{current.major}.{current.minor}.{current.patch}-{prerelease}.1"
                        )
                else:
                    self.logger.error("预发布版本需要指定预发布标识符")
                    return None
            else:
                self.logger.error(f"不支持的版本类型: {version_type}")
                return None
            
            # 创建新版本信息
            new_version_info = self._parse_version(str(new_version))
            
            if new_version_info:
                # 更新版本文件
                self._update_version_files(str(new_version))
                
                # 创建Git标签
                if self.config.get('auto_tag', True) and self.repo:
                    self._create_git_tag(str(new_version))
                
                # 生成变更日志
                if self.config.get('auto_changelog', True):
                    self._generate_changelog(new_version_info)
                
                # 更新当前版本
                self.current_version = new_version_info
                
                self.logger.info(f"版本已升级: {current} -> {new_version}")
                return new_version_info
            
            return None
        
        except Exception as e:
            self.logger.error(f"升级版本失败: {e}")
            return None
    
    def _update_version_files(self, version: str):
        """更新版本文件"""
        # 更新VERSION文件
        try:
            self.version_file.write_text(version)
            self.logger.info(f"已更新VERSION文件: {version}")
        except Exception as e:
            self.logger.error(f"更新VERSION文件失败: {e}")
        
        # 更新package.json
        if self.package_json.exists():
            try:
                with open(self.package_json, 'r', encoding='utf-8') as f:
                    package_data = json.load(f)
                
                package_data['version'] = version
                
                with open(self.package_json, 'w', encoding='utf-8') as f:
                    json.dump(package_data, f, indent=2, ensure_ascii=False)
                
                self.logger.info(f"已更新package.json: {version}")
            except Exception as e:
                self.logger.error(f"更新package.json失败: {e}")
        
        # 更新setup.py
        if self.setup_py.exists():
            try:
                content = self.setup_py.read_text(encoding='utf-8')
                
                # 使用正则表达式替换版本
                version_pattern = r'version\s*=\s*["\']([^"\']+)["\']'
                new_content = re.sub(version_pattern, f'version="{version}"', content)
                
                self.setup_py.write_text(new_content, encoding='utf-8')
                self.logger.info(f"已更新setup.py: {version}")
            except Exception as e:
                self.logger.error(f"更新setup.py失败: {e}")
        
        # 更新pyproject.toml
        if self.pyproject_toml.exists():
            try:
                content = self.pyproject_toml.read_text(encoding='utf-8')
                
                # 使用正则表达式替换版本
                version_pattern = r'version\s*=\s*["\']([^"\']+)["\']'
                new_content = re.sub(version_pattern, f'version = "{version}"', content)
                
                self.pyproject_toml.write_text(new_content, encoding='utf-8')
                self.logger.info(f"已更新pyproject.toml: {version}")
            except Exception as e:
                self.logger.error(f"更新pyproject.toml失败: {e}")
    
    def _create_git_tag(self, version: str):
        """创建Git标签"""
        if not self.repo:
            return
        
        try:
            tag_name = f"{self.config.get('tag_prefix', 'v')}{version}"
            
            # 检查标签是否已存在
            existing_tags = [tag.name for tag in self.repo.tags]
            if tag_name in existing_tags:
                self.logger.warning(f"标签已存在: {tag_name}")
                return
            
            # 创建标签
            self.repo.create_tag(tag_name, message=f"Release {version}")
            self.logger.info(f"已创建Git标签: {tag_name}")
        
        except Exception as e:
            self.logger.error(f"创建Git标签失败: {e}")
    
    def _generate_changelog(self, version_info: VersionInfo):
        """生成变更日志"""
        try:
            changelog_entries = self._get_changelog_entries(version_info)
            
            if not changelog_entries:
                self.logger.warning("没有找到变更记录")
                return
            
            # 生成变更日志内容
            changelog_content = self._format_changelog(version_info, changelog_entries)
            
            # 保存变更日志
            changelog_file = self.changelogs_dir / f"CHANGELOG_{version_info.version}.md"
            changelog_file.write_text(changelog_content, encoding='utf-8')
            
            # 更新主变更日志
            self._update_main_changelog(version_info, changelog_content)
            
            self.logger.info(f"已生成变更日志: {changelog_file}")
        
        except Exception as e:
            self.logger.error(f"生成变更日志失败: {e}")
    
    def _get_changelog_entries(self, version_info: VersionInfo) -> List[ChangelogEntry]:
        """获取变更日志条目"""
        if not self.repo:
            return []
        
        entries = []
        
        try:
            # 获取上一个版本的标签
            previous_tag = self._get_previous_tag()
            
            # 获取提交范围
            if previous_tag:
                commits = list(self.repo.iter_commits(f"{previous_tag}..HEAD"))
            else:
                commits = list(self.repo.iter_commits())
            
            # 解析提交消息
            for commit in commits:
                entry = self._parse_commit_message(commit)
                if entry:
                    entries.append(entry)
        
        except Exception as e:
            self.logger.error(f"获取变更日志条目失败: {e}")
        
        return entries
    
    def _get_previous_tag(self) -> Optional[str]:
        """获取上一个版本标签"""
        if not self.repo:
            return None
        
        try:
            tags = sorted(self.repo.tags, key=lambda t: t.commit.committed_date, reverse=True)
            
            # 跳过当前版本的标签
            current_tag = f"{self.config.get('tag_prefix', 'v')}{self.current_version.version}"
            
            for tag in tags:
                if tag.name != current_tag:
                    return tag.name
            
            return None
        
        except Exception:
            return None
    
    def _parse_commit_message(self, commit) -> Optional[ChangelogEntry]:
        """解析提交消息"""
        try:
            message = commit.message.strip()
            
            # 使用Conventional Commits格式解析
            pattern = r'^(\w+)(?:\(([^)]+)\))?: (.+)$'
            match = re.match(pattern, message)
            
            if not match:
                # 如果不符合格式，作为chore处理
                return ChangelogEntry(
                    change_type=ChangeType.CHORE,
                    scope=None,
                    description=message.split('\n')[0],
                    commit_hash=commit.hexsha[:8],
                    author=commit.author.name,
                    date=datetime.fromtimestamp(commit.committed_date)
                )
            
            type_str, scope, description = match.groups()
            
            # 映射变更类型
            try:
                change_type = ChangeType(type_str.lower())
            except ValueError:
                change_type = ChangeType.CHORE
            
            # 检查是否为破坏性变更
            breaking_change = 'BREAKING CHANGE' in message or type_str.endswith('!')
            
            return ChangelogEntry(
                change_type=change_type,
                scope=scope,
                description=description,
                breaking_change=breaking_change,
                commit_hash=commit.hexsha[:8],
                author=commit.author.name,
                date=datetime.fromtimestamp(commit.committed_date)
            )
        
        except Exception as e:
            self.logger.error(f"解析提交消息失败: {e}")
            return None
    
    def _format_changelog(self, version_info: VersionInfo, entries: List[ChangelogEntry]) -> str:
        """格式化变更日志"""
        lines = []
        
        # 版本标题
        lines.append(f"# {version_info.version}")
        lines.append("")
        
        # 版本信息
        if version_info.release_date:
            lines.append(f"**发布日期**: {version_info.release_date.strftime('%Y-%m-%d')}")
        else:
            lines.append(f"**发布日期**: {datetime.now().strftime('%Y-%m-%d')}")
        
        if version_info.commit_hash:
            lines.append(f"**提交哈希**: {version_info.commit_hash}")
        
        if version_info.release_type:
            lines.append(f"**发布类型**: {version_info.release_type.value}")
        
        lines.append("")
        
        # 按类型分组变更
        grouped_entries = {}
        for entry in entries:
            if entry.change_type not in grouped_entries:
                grouped_entries[entry.change_type] = []
            grouped_entries[entry.change_type].append(entry)
        
        # 定义显示顺序
        type_order = [
            ChangeType.BREAKING,
            ChangeType.FEATURE,
            ChangeType.FIX,
            ChangeType.PERF,
            ChangeType.REFACTOR,
            ChangeType.DOCS,
            ChangeType.STYLE,
            ChangeType.TEST,
            ChangeType.CHORE
        ]
        
        # 生成各类型的变更
        for change_type in type_order:
            if change_type in grouped_entries:
                type_entries = grouped_entries[change_type]
                
                # 类型标题
                type_names = {
                    ChangeType.BREAKING: "💥 破坏性变更",
                    ChangeType.FEATURE: "✨ 新功能",
                    ChangeType.FIX: "🐛 错误修复",
                    ChangeType.PERF: "⚡ 性能优化",
                    ChangeType.REFACTOR: "♻️ 代码重构",
                    ChangeType.DOCS: "📚 文档更新",
                    ChangeType.STYLE: "💄 代码格式",
                    ChangeType.TEST: "✅ 测试相关",
                    ChangeType.CHORE: "🔧 其他变更"
                }
                
                lines.append(f"## {type_names.get(change_type, change_type.value.title())}")
                lines.append("")
                
                # 变更条目
                for entry in type_entries:
                    lines.append(entry.to_markdown())
                
                lines.append("")
        
        return '\n'.join(lines)
    
    def _update_main_changelog(self, version_info: VersionInfo, changelog_content: str):
        """更新主变更日志"""
        main_changelog = self.project_root / "CHANGELOG.md"
        
        try:
            # 读取现有内容
            existing_content = ""
            if main_changelog.exists():
                existing_content = main_changelog.read_text(encoding='utf-8')
            
            # 在开头插入新版本的变更日志
            if existing_content:
                new_content = f"{changelog_content}\n\n---\n\n{existing_content}"
            else:
                new_content = changelog_content
            
            # 写入文件
            main_changelog.write_text(new_content, encoding='utf-8')
            
            self.logger.info("已更新主变更日志")
        
        except Exception as e:
            self.logger.error(f"更新主变更日志失败: {e}")
    
    def create_release(self, version: str = None, release_type: ReleaseType = ReleaseType.STABLE,
                      notes: str = None) -> Optional[Dict[str, Any]]:
        """创建发布"""
        try:
            # 使用指定版本或当前版本
            if version:
                version_info = self._parse_version(version)
            else:
                version_info = self.current_version
            
            if not version_info:
                self.logger.error("无法获取版本信息")
                return None
            
            # 执行预发布钩子
            if self.config.get('pre_release_hook'):
                self._execute_hook(self.config['pre_release_hook'], version_info)
            
            # 创建发布记录
            release_data = {
                'version': version_info.version,
                'release_type': release_type.value,
                'release_date': datetime.now().isoformat(),
                'commit_hash': version_info.commit_hash,
                'tag': version_info.tag,
                'notes': notes or f"Release {version_info.version}",
                'changelog_file': f"CHANGELOG_{version_info.version}.md",
                'artifacts': [],
                'metadata': {
                    'created_by': 'version_manager',
                    'project_root': str(self.project_root)
                }
            }
            
            # 保存发布记录
            release_file = self.releases_dir / f"release_{version_info.version}.json"
            with open(release_file, 'w', encoding='utf-8') as f:
                json.dump(release_data, f, indent=2, ensure_ascii=False)
            
            # 执行后发布钩子
            if self.config.get('post_release_hook'):
                self._execute_hook(self.config['post_release_hook'], version_info)
            
            # 发送通知
            if self.config.get('notification_webhook'):
                self._send_release_notification(release_data)
            
            self.logger.info(f"已创建发布: {version_info.version}")
            return release_data
        
        except Exception as e:
            self.logger.error(f"创建发布失败: {e}")
            return None
    
    def _execute_hook(self, hook_command: str, version_info: VersionInfo):
        """执行钩子命令"""
        try:
            # 替换变量
            command = hook_command.format(
                version=version_info.version,
                major=version_info.major,
                minor=version_info.minor,
                patch=version_info.patch,
                project_root=self.project_root
            )
            
            # 执行命令
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.logger.info(f"钩子执行成功: {command}")
            else:
                self.logger.error(f"钩子执行失败: {command}\n{result.stderr}")
        
        except Exception as e:
            self.logger.error(f"执行钩子失败: {e}")
    
    def _send_release_notification(self, release_data: Dict[str, Any]):
        """发送发布通知"""
        if not REQUESTS_AVAILABLE:
            return
        
        try:
            webhook_url = self.config.get('notification_webhook')
            if not webhook_url:
                return
            
            payload = {
                'text': f"🚀 新版本发布: {release_data['version']}",
                'attachments': [
                    {
                        'color': 'good',
                        'fields': [
                            {
                                'title': '版本',
                                'value': release_data['version'],
                                'short': True
                            },
                            {
                                'title': '发布类型',
                                'value': release_data['release_type'],
                                'short': True
                            },
                            {
                                'title': '发布时间',
                                'value': release_data['release_date'],
                                'short': True
                            },
                            {
                                'title': '说明',
                                'value': release_data['notes'],
                                'short': False
                            }
                        ]
                    }
                ]
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                self.logger.info("发布通知已发送")
            else:
                self.logger.error(f"发送发布通知失败: {response.status_code}")
        
        except Exception as e:
            self.logger.error(f"发送发布通知失败: {e}")
    
    def list_versions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """列出版本历史"""
        versions = []
        
        try:
            # 从发布记录获取
            for release_file in sorted(self.releases_dir.glob("release_*.json"), reverse=True):
                try:
                    with open(release_file, 'r', encoding='utf-8') as f:
                        release_data = json.load(f)
                    
                    versions.append({
                        'version': release_data['version'],
                        'release_type': release_data['release_type'],
                        'release_date': release_data['release_date'],
                        'commit_hash': release_data.get('commit_hash'),
                        'tag': release_data.get('tag'),
                        'notes': release_data.get('notes')
                    })
                    
                    if len(versions) >= limit:
                        break
                
                except Exception:
                    continue
            
            # 如果没有发布记录，从Git标签获取
            if not versions and self.repo:
                tags = sorted(self.repo.tags, key=lambda t: t.commit.committed_date, reverse=True)
                
                for tag in tags[:limit]:
                    version_str = tag.name
                    if version_str.startswith(self.config.get('tag_prefix', 'v')):
                        version_str = version_str[len(self.config.get('tag_prefix', 'v')):]
                    
                    versions.append({
                        'version': version_str,
                        'release_type': 'stable',
                        'release_date': datetime.fromtimestamp(tag.commit.committed_date).isoformat(),
                        'commit_hash': tag.commit.hexsha[:8],
                        'tag': tag.name,
                        'notes': tag.commit.message.strip()
                    })
        
        except Exception as e:
            self.logger.error(f"列出版本历史失败: {e}")
        
        return versions
    
    def compare_versions(self, version1: str, version2: str) -> Dict[str, Any]:
        """比较两个版本"""
        try:
            v1 = semantic_version.Version(version1)
            v2 = semantic_version.Version(version2)
            
            comparison = {
                'version1': str(v1),
                'version2': str(v2),
                'comparison': 'equal'
            }
            
            if v1 > v2:
                comparison['comparison'] = 'greater'
                comparison['difference'] = 'newer'
            elif v1 < v2:
                comparison['comparison'] = 'less'
                comparison['difference'] = 'older'
            else:
                comparison['difference'] = 'same'
            
            # 计算版本差异
            major_diff = v1.major - v2.major
            minor_diff = v1.minor - v2.minor
            patch_diff = v1.patch - v2.patch
            
            comparison['version_diff'] = {
                'major': major_diff,
                'minor': minor_diff,
                'patch': patch_diff
            }
            
            # 确定升级类型
            if major_diff != 0:
                comparison['upgrade_type'] = 'major'
            elif minor_diff != 0:
                comparison['upgrade_type'] = 'minor'
            elif patch_diff != 0:
                comparison['upgrade_type'] = 'patch'
            else:
                comparison['upgrade_type'] = 'none'
            
            return comparison
        
        except Exception as e:
            self.logger.error(f"比较版本失败: {e}")
            return {}
    
    def get_version_info(self, version: str = None) -> Optional[Dict[str, Any]]:
        """获取版本详细信息"""
        try:
            if version:
                version_info = self._parse_version(version)
            else:
                version_info = self.current_version
            
            if not version_info:
                return None
            
            # 获取发布记录
            release_file = self.releases_dir / f"release_{version_info.version}.json"
            release_data = {}
            
            if release_file.exists():
                with open(release_file, 'r', encoding='utf-8') as f:
                    release_data = json.load(f)
            
            # 获取变更日志
            changelog_file = self.changelogs_dir / f"CHANGELOG_{version_info.version}.md"
            changelog_content = ""
            
            if changelog_file.exists():
                changelog_content = changelog_file.read_text(encoding='utf-8')
            
            return {
                'version': version_info.version,
                'major': version_info.major,
                'minor': version_info.minor,
                'patch': version_info.patch,
                'prerelease': version_info.prerelease,
                'build': version_info.build,
                'tag': version_info.tag,
                'commit_hash': version_info.commit_hash,
                'commit_date': version_info.commit_date.isoformat() if version_info.commit_date else None,
                'release_date': version_info.release_date.isoformat() if version_info.release_date else None,
                'release_type': version_info.release_type.value if version_info.release_type else None,
                'release_data': release_data,
                'changelog': changelog_content,
                'metadata': version_info.metadata
            }
        
        except Exception as e:
            self.logger.error(f"获取版本信息失败: {e}")
            return None

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='YDS-Lab 版本管理工具')
    parser.add_argument('--project-root', help='指定项目根目录路径')
    parser.add_argument('--current', action='store_true', help='显示当前版本')
    parser.add_argument('--bump', choices=['major', 'minor', 'patch', 'prerelease'], help='升级版本')
    parser.add_argument('--prerelease', help='预发布标识符（用于prerelease）')
    parser.add_argument('--list', action='store_true', help='列出版本历史')
    parser.add_argument('--limit', type=int, default=20, help='版本历史限制数量')
    parser.add_argument('--info', help='显示指定版本信息')
    parser.add_argument('--compare', nargs=2, metavar=('V1', 'V2'), help='比较两个版本')
    parser.add_argument('--release', help='创建发布（指定版本）')
    parser.add_argument('--release-type', choices=['alpha', 'beta', 'rc', 'stable'], 
                       default='stable', help='发布类型')
    parser.add_argument('--notes', help='发布说明')
    parser.add_argument('--changelog', help='生成指定版本的变更日志')
    
    args = parser.parse_args()
    
    manager = VersionManager(args.project_root)
    
    # 显示当前版本
    if args.current:
        if manager.current_version:
            print(f"📦 当前版本: {manager.current_version.version}")
            print(f"发布类型: {manager.current_version.release_type.value if manager.current_version.release_type else 'unknown'}")
            if manager.current_version.commit_hash:
                print(f"提交哈希: {manager.current_version.commit_hash}")
            if manager.current_version.commit_date:
                print(f"提交时间: {manager.current_version.commit_date}")
            if manager.current_version.tag:
                print(f"Git标签: {manager.current_version.tag}")
        else:
            print("❌ 无法获取当前版本")
        return
    
    # 升级版本
    if args.bump:
        version_type = VersionType(args.bump)
        new_version = manager.bump_version(version_type, args.prerelease)
        
        if new_version:
            print(f"✅ 版本已升级: {new_version.version}")
            print(f"版本类型: {version_type.value}")
            if new_version.tag:
                print(f"Git标签: {new_version.tag}")
        else:
            print(f"❌ 版本升级失败")
        return
    
    # 列出版本历史
    if args.list:
        versions = manager.list_versions(args.limit)
        
        print(f"📋 版本历史 (最近{len(versions)}个):")
        print("="*60)
        
        for version in versions:
            print(f"版本: {version['version']}")
            print(f"类型: {version['release_type']}")
            print(f"日期: {version['release_date']}")
            if version.get('commit_hash'):
                print(f"提交: {version['commit_hash']}")
            if version.get('tag'):
                print(f"标签: {version['tag']}")
            if version.get('notes'):
                print(f"说明: {version['notes']}")
            print("-" * 60)
        return
    
    # 显示版本信息
    if args.info:
        info = manager.get_version_info(args.info)
        
        if info:
            print(f"📊 版本信息: {info['version']}")
            print("="*40)
            print(f"主版本: {info['major']}")
            print(f"次版本: {info['minor']}")
            print(f"修订版本: {info['patch']}")
            if info['prerelease']:
                print(f"预发布: {info['prerelease']}")
            if info['build']:
                print(f"构建: {info['build']}")
            if info['tag']:
                print(f"Git标签: {info['tag']}")
            if info['commit_hash']:
                print(f"提交哈希: {info['commit_hash']}")
            if info['commit_date']:
                print(f"提交时间: {info['commit_date']}")
            if info['release_date']:
                print(f"发布时间: {info['release_date']}")
            if info['release_type']:
                print(f"发布类型: {info['release_type']}")
            
            if info['changelog']:
                print(f"\n📝 变更日志:")
                print(info['changelog'])
        else:
            print(f"❌ 版本信息不存在: {args.info}")
        return
    
    # 比较版本
    if args.compare:
        v1, v2 = args.compare
        comparison = manager.compare_versions(v1, v2)
        
        if comparison:
            print(f"🔍 版本比较:")
            print(f"版本1: {comparison['version1']}")
            print(f"版本2: {comparison['version2']}")
            print(f"比较结果: {comparison['comparison']}")
            print(f"差异: {comparison['difference']}")
            print(f"升级类型: {comparison['upgrade_type']}")
            
            diff = comparison['version_diff']
            print(f"版本差异:")
            print(f"  主版本: {diff['major']}")
            print(f"  次版本: {diff['minor']}")
            print(f"  修订版本: {diff['patch']}")
        else:
            print(f"❌ 版本比较失败")
        return
    
    # 创建发布
    if args.release:
        release_type = ReleaseType(args.release_type)
        release_data = manager.create_release(args.release, release_type, args.notes)
        
        if release_data:
            print(f"✅ 发布已创建: {release_data['version']}")
            print(f"发布类型: {release_data['release_type']}")
            print(f"发布时间: {release_data['release_date']}")
            if release_data.get('notes'):
                print(f"发布说明: {release_data['notes']}")
        else:
            print(f"❌ 创建发布失败")
        return
    
    # 生成变更日志
    if args.changelog:
        version_info = manager._parse_version(args.changelog)
        if version_info:
            manager._generate_changelog(version_info)
            print(f"✅ 变更日志已生成: {args.changelog}")
        else:
            print(f"❌ 无效的版本号: {args.changelog}")
        return
    
    # 默认显示状态
    print("🔄 版本管理器")
    print("="*30)
    print(f"项目路径: {manager.project_root}")
    print(f"版本目录: {manager.version_dir}")
    
    if manager.current_version:
        print(f"当前版本: {manager.current_version.version}")
        print(f"发布类型: {manager.current_version.release_type.value if manager.current_version.release_type else 'unknown'}")
    else:
        print("当前版本: 未知")
    
    print(f"Git仓库: {'是' if manager.repo else '否'}")
    
    # 显示最近版本
    recent_versions = manager.list_versions(5)
    if recent_versions:
        print(f"\n📦 最近版本:")
        for version in recent_versions:
            print(f"  {version['version']}: {version['release_type']} ({version['release_date'][:10]})")

if __name__ == "__main__":
    main()