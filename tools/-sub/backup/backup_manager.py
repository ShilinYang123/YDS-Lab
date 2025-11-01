#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YDS-Lab 备份管理工具
提供项目文件的自动备份、恢复和管理功能
适配YDS-Lab项目结构和AI Agent协作需求
"""

import os
import sys
import shutil
import json
import zipfile
import tarfile
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import threading
import time
import schedule

class BackupManager:
    """备份管理器"""
    
    def __init__(self, project_root: str = None):
        """初始化备份管理器"""
        if project_root is None:
            self.project_root = Path(__file__).parent.parent.parent
        else:
            self.project_root = Path(project_root)
        
        # 备份相关路径
        self.backup_dir = self.project_root / "backups"
        self.config_dir = self.project_root / "config"
        self.logs_dir = self.project_root / "logs" / "backup"
        
        # 创建必要目录
        self.backup_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置文件
        self.backup_config_file = self.config_dir / "backup_config.json"
        
        # 备份状态
        self.backup_history = []
        self.scheduler_thread = None
        self.scheduler_active = False
        
        # 加载配置
        self.load_backup_config()
        self.load_backup_history()
    
    def load_backup_config(self) -> Dict[str, Any]:
        """加载备份配置"""
        default_config = {
            'backup_settings': {
                'compression': 'zip',  # zip, tar, tar.gz, tar.bz2
                'include_patterns': [
                    '*.py', '*.md', '*.json', '*.yaml', '*.yml',
                    '*.txt', '*.cfg', '*.ini', '*.toml',
                    'Docs/**/*', 'config/**/*', 'tools/**/*'
                ],
                'exclude_patterns': [
                    '*.log', '*.tmp', '*.cache', '*.pyc',
                    '__pycache__/**/*', '.git/**/*', 'backups/**/*',
                    'logs/**/*', 'temp/**/*', 'node_modules/**/*',
                    '.venv/**/*', 'venv/**/*', '.env'
                ],
                'max_backup_size_mb': 1000,
                'verify_backup': True
            },
            'schedule_settings': {
                'enabled': False,
                'daily_backup': {
                    'enabled': True,
                    'time': '02:00',
                    'keep_days': 7
                },
                'weekly_backup': {
                    'enabled': True,
                    'day': 'sunday',
                    'time': '03:00',
                    'keep_weeks': 4
                },
                'monthly_backup': {
                    'enabled': True,
                    'day': 1,
                    'time': '04:00',
                    'keep_months': 12
                }
            },
            'storage_settings': {
                'local_backup': True,
                'cloud_backup': False,
                'cloud_provider': 'none',  # s3, azure, gcp
                'cloud_config': {}
            },
            'retention_policy': {
                'max_backups': 50,
                'auto_cleanup': True,
                'cleanup_interval_days': 7
            }
        }
        
        try:
            if self.backup_config_file.exists():
                with open(self.backup_config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 合并默认配置
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    self.config = config
            else:
                self.config = default_config
                self.save_backup_config()
        except Exception as e:
            print(f"❌ 加载备份配置失败: {e}")
            self.config = default_config
        
        return self.config
    
    def save_backup_config(self) -> bool:
        """保存备份配置"""
        try:
            self.config_dir.mkdir(exist_ok=True)
            
            with open(self.backup_config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 备份配置已保存: {self.backup_config_file}")
            return True
            
        except Exception as e:
            print(f"❌ 保存备份配置失败: {e}")
            return False
    
    def load_backup_history(self) -> List[Dict[str, Any]]:
        """加载备份历史"""
        history_file = self.backup_dir / "backup_history.json"
        
        try:
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    self.backup_history = json.load(f)
            else:
                self.backup_history = []
        except Exception as e:
            print(f"❌ 加载备份历史失败: {e}")
            self.backup_history = []
        
        return self.backup_history
    
    def save_backup_history(self) -> bool:
        """保存备份历史"""
        history_file = self.backup_dir / "backup_history.json"
        
        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.backup_history, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"❌ 保存备份历史失败: {e}")
            return False
    
    def get_backup_files(self) -> List[Path]:
        """获取需要备份的文件列表"""
        include_patterns = self.config['backup_settings']['include_patterns']
        exclude_patterns = self.config['backup_settings']['exclude_patterns']
        
        files_to_backup = []
        
        # 遍历项目目录
        for root, dirs, files in os.walk(self.project_root):
            root_path = Path(root)
            
            # 检查目录是否应该被排除
            relative_root = root_path.relative_to(self.project_root)
            if self._should_exclude_path(str(relative_root), exclude_patterns):
                dirs.clear()  # 不遍历子目录
                continue
            
            for file in files:
                file_path = root_path / file
                relative_path = file_path.relative_to(self.project_root)
                
                # 检查文件是否匹配包含模式
                if self._should_include_file(str(relative_path), include_patterns):
                    # 检查文件是否应该被排除
                    if not self._should_exclude_path(str(relative_path), exclude_patterns):
                        files_to_backup.append(file_path)
        
        return files_to_backup
    
    def _should_include_file(self, file_path: str, patterns: List[str]) -> bool:
        """检查文件是否应该被包含"""
        import fnmatch
        
        for pattern in patterns:
            if fnmatch.fnmatch(file_path, pattern):
                return True
        
        return False
    
    def _should_exclude_path(self, path: str, patterns: List[str]) -> bool:
        """检查路径是否应该被排除"""
        import fnmatch
        
        for pattern in patterns:
            if fnmatch.fnmatch(path, pattern):
                return True
        
        return False
    
    def create_backup(self, backup_name: str = None, backup_type: str = 'manual') -> Optional[Dict[str, Any]]:
        """创建备份"""
        try:
            # 生成备份名称
            if backup_name is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_name = f"backup_{backup_type}_{timestamp}"
            
            print(f"🔄 开始创建备份: {backup_name}")
            
            # 获取要备份的文件
            files_to_backup = self.get_backup_files()
            
            if not files_to_backup:
                print("⚠️ 没有找到需要备份的文件")
                return None
            
            print(f"📁 找到 {len(files_to_backup)} 个文件需要备份")
            
            # 检查备份大小
            total_size = sum(f.stat().st_size for f in files_to_backup if f.exists())
            total_size_mb = total_size / (1024 * 1024)
            
            max_size_mb = self.config['backup_settings']['max_backup_size_mb']
            if total_size_mb > max_size_mb:
                print(f"⚠️ 备份大小 ({total_size_mb:.1f}MB) 超过限制 ({max_size_mb}MB)")
                return None
            
            # 创建备份文件
            compression = self.config['backup_settings']['compression']
            backup_file = self.backup_dir / f"{backup_name}.{compression}"
            
            if compression == 'zip':
                success = self._create_zip_backup(backup_file, files_to_backup)
            elif compression.startswith('tar'):
                success = self._create_tar_backup(backup_file, files_to_backup, compression)
            else:
                print(f"❌ 不支持的压缩格式: {compression}")
                return None
            
            if not success:
                return None
            
            # 验证备份
            if self.config['backup_settings']['verify_backup']:
                if not self._verify_backup(backup_file):
                    print("❌ 备份验证失败")
                    backup_file.unlink()
                    return None
            
            # 计算文件哈希
            file_hash = self._calculate_file_hash(backup_file)
            
            # 记录备份信息
            backup_info = {
                'name': backup_name,
                'type': backup_type,
                'file_path': str(backup_file),
                'file_size': backup_file.stat().st_size,
                'file_hash': file_hash,
                'files_count': len(files_to_backup),
                'created_at': datetime.now().isoformat(),
                'compression': compression,
                'verified': True
            }
            
            self.backup_history.append(backup_info)
            self.save_backup_history()
            
            print(f"✅ 备份创建成功: {backup_file}")
            print(f"📊 备份大小: {backup_info['file_size'] / (1024 * 1024):.1f}MB")
            
            # 清理旧备份
            if self.config['retention_policy']['auto_cleanup']:
                self.cleanup_old_backups()
            
            return backup_info
            
        except Exception as e:
            print(f"❌ 创建备份失败: {e}")
            return None
    
    def _create_zip_backup(self, backup_file: Path, files: List[Path]) -> bool:
        """创建ZIP备份"""
        try:
            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in files:
                    if file_path.exists():
                        relative_path = file_path.relative_to(self.project_root)
                        zipf.write(file_path, relative_path)
            
            return True
            
        except Exception as e:
            print(f"❌ 创建ZIP备份失败: {e}")
            return False
    
    def _create_tar_backup(self, backup_file: Path, files: List[Path], compression: str) -> bool:
        """创建TAR备份"""
        try:
            mode_map = {
                'tar': 'w',
                'tar.gz': 'w:gz',
                'tar.bz2': 'w:bz2'
            }
            
            mode = mode_map.get(compression, 'w')
            
            with tarfile.open(backup_file, mode) as tarf:
                for file_path in files:
                    if file_path.exists():
                        relative_path = file_path.relative_to(self.project_root)
                        tarf.add(file_path, arcname=relative_path)
            
            return True
            
        except Exception as e:
            print(f"❌ 创建TAR备份失败: {e}")
            return False
    
    def _verify_backup(self, backup_file: Path) -> bool:
        """验证备份文件"""
        try:
            if backup_file.suffix == '.zip':
                with zipfile.ZipFile(backup_file, 'r') as zipf:
                    # 测试ZIP文件完整性
                    bad_file = zipf.testzip()
                    return bad_file is None
            elif backup_file.suffix in ['.tar', '.gz', '.bz2']:
                with tarfile.open(backup_file, 'r') as tarf:
                    # 检查TAR文件
                    return True
            
            return True
            
        except Exception as e:
            print(f"❌ 验证备份失败: {e}")
            return False
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """计算文件哈希值"""
        try:
            hash_md5 = hashlib.md5()
            
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            
            return hash_md5.hexdigest()
            
        except Exception as e:
            print(f"❌ 计算文件哈希失败: {e}")
            return ""
    
    def restore_backup(self, backup_name: str, restore_path: str = None) -> bool:
        """恢复备份"""
        try:
            # 查找备份信息
            backup_info = None
            for backup in self.backup_history:
                if backup['name'] == backup_name:
                    backup_info = backup
                    break
            
            if not backup_info:
                print(f"❌ 未找到备份: {backup_name}")
                return False
            
            backup_file = Path(backup_info['file_path'])
            
            if not backup_file.exists():
                print(f"❌ 备份文件不存在: {backup_file}")
                return False
            
            # 验证备份文件
            if not self._verify_backup(backup_file):
                print(f"❌ 备份文件损坏: {backup_file}")
                return False
            
            # 确定恢复路径
            if restore_path is None:
                restore_path = self.project_root
            else:
                restore_path = Path(restore_path)
            
            restore_path.mkdir(parents=True, exist_ok=True)
            
            print(f"🔄 开始恢复备份: {backup_name}")
            print(f"📁 恢复到: {restore_path}")
            
            # 恢复文件
            compression = backup_info['compression']
            
            if compression == 'zip':
                success = self._restore_zip_backup(backup_file, restore_path)
            elif compression.startswith('tar'):
                success = self._restore_tar_backup(backup_file, restore_path)
            else:
                print(f"❌ 不支持的压缩格式: {compression}")
                return False
            
            if success:
                print(f"✅ 备份恢复成功: {backup_name}")
                return True
            else:
                print(f"❌ 备份恢复失败: {backup_name}")
                return False
            
        except Exception as e:
            print(f"❌ 恢复备份失败: {e}")
            return False
    
    def _restore_zip_backup(self, backup_file: Path, restore_path: Path) -> bool:
        """恢复ZIP备份"""
        try:
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                zipf.extractall(restore_path)
            
            return True
            
        except Exception as e:
            print(f"❌ 恢复ZIP备份失败: {e}")
            return False
    
    def _restore_tar_backup(self, backup_file: Path, restore_path: Path) -> bool:
        """恢复TAR备份"""
        try:
            with tarfile.open(backup_file, 'r') as tarf:
                tarf.extractall(restore_path)
            
            return True
            
        except Exception as e:
            print(f"❌ 恢复TAR备份失败: {e}")
            return False
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """列出所有备份"""
        # 刷新备份历史（检查文件是否还存在）
        valid_backups = []
        
        for backup in self.backup_history:
            backup_file = Path(backup['file_path'])
            if backup_file.exists():
                # 更新文件大小（可能已更改）
                backup['file_size'] = backup_file.stat().st_size
                valid_backups.append(backup)
        
        self.backup_history = valid_backups
        self.save_backup_history()
        
        return self.backup_history
    
    def delete_backup(self, backup_name: str) -> bool:
        """删除备份"""
        try:
            # 查找备份信息
            backup_info = None
            backup_index = -1
            
            for i, backup in enumerate(self.backup_history):
                if backup['name'] == backup_name:
                    backup_info = backup
                    backup_index = i
                    break
            
            if not backup_info:
                print(f"❌ 未找到备份: {backup_name}")
                return False
            
            backup_file = Path(backup_info['file_path'])
            
            # 删除备份文件
            if backup_file.exists():
                backup_file.unlink()
                print(f"🗑️ 已删除备份文件: {backup_file}")
            
            # 从历史记录中移除
            self.backup_history.pop(backup_index)
            self.save_backup_history()
            
            print(f"✅ 备份删除成功: {backup_name}")
            return True
            
        except Exception as e:
            print(f"❌ 删除备份失败: {e}")
            return False
    
    def cleanup_old_backups(self) -> int:
        """清理旧备份"""
        try:
            max_backups = self.config['retention_policy']['max_backups']
            
            # 按创建时间排序
            sorted_backups = sorted(
                self.backup_history,
                key=lambda x: x['created_at'],
                reverse=True
            )
            
            deleted_count = 0
            
            # 删除超出数量限制的备份
            if len(sorted_backups) > max_backups:
                backups_to_delete = sorted_backups[max_backups:]
                
                for backup in backups_to_delete:
                    if self.delete_backup(backup['name']):
                        deleted_count += 1
            
            # 删除过期的备份
            cleanup_interval = self.config['retention_policy']['cleanup_interval_days']
            cutoff_date = datetime.now() - timedelta(days=cleanup_interval)
            
            for backup in list(self.backup_history):
                created_at = datetime.fromisoformat(backup['created_at'])
                if created_at < cutoff_date and backup['type'] == 'manual':
                    if self.delete_backup(backup['name']):
                        deleted_count += 1
            
            if deleted_count > 0:
                print(f"🧹 已清理 {deleted_count} 个旧备份")
            
            return deleted_count
            
        except Exception as e:
            print(f"❌ 清理旧备份失败: {e}")
            return 0
    
    def get_backup_info(self, backup_name: str) -> Optional[Dict[str, Any]]:
        """获取备份信息"""
        for backup in self.backup_history:
            if backup['name'] == backup_name:
                return backup
        
        return None
    
    def start_scheduled_backup(self) -> bool:
        """启动定时备份"""
        if not self.config['schedule_settings']['enabled']:
            print("⚠️ 定时备份未启用")
            return False
        
        if self.scheduler_active:
            print("⚠️ 定时备份已在运行")
            return False
        
        try:
            # 清除现有任务
            schedule.clear()
            
            # 设置每日备份
            daily_config = self.config['schedule_settings']['daily_backup']
            if daily_config['enabled']:
                schedule.every().day.at(daily_config['time']).do(
                    self._scheduled_backup, 'daily'
                )
                print(f"📅 每日备份已设置: {daily_config['time']}")
            
            # 设置每周备份
            weekly_config = self.config['schedule_settings']['weekly_backup']
            if weekly_config['enabled']:
                getattr(schedule.every(), weekly_config['day']).at(weekly_config['time']).do(
                    self._scheduled_backup, 'weekly'
                )
                print(f"📅 每周备份已设置: {weekly_config['day']} {weekly_config['time']}")
            
            # 设置每月备份
            monthly_config = self.config['schedule_settings']['monthly_backup']
            if monthly_config['enabled']:
                # 注意：schedule库不直接支持每月，这里简化为每30天
                schedule.every(30).days.at(monthly_config['time']).do(
                    self._scheduled_backup, 'monthly'
                )
                print(f"📅 每月备份已设置: 每30天 {monthly_config['time']}")
            
            # 启动调度线程
            self.scheduler_active = True
            self.scheduler_thread = threading.Thread(
                target=self._scheduler_loop,
                daemon=True
            )
            self.scheduler_thread.start()
            
            print("⏰ 定时备份已启动")
            return True
            
        except Exception as e:
            print(f"❌ 启动定时备份失败: {e}")
            return False
    
    def stop_scheduled_backup(self) -> bool:
        """停止定时备份"""
        if not self.scheduler_active:
            print("⚠️ 定时备份未在运行")
            return False
        
        try:
            self.scheduler_active = False
            schedule.clear()
            
            if self.scheduler_thread and self.scheduler_thread.is_alive():
                self.scheduler_thread.join(timeout=5)
            
            print("⏰ 定时备份已停止")
            return True
            
        except Exception as e:
            print(f"❌ 停止定时备份失败: {e}")
            return False
    
    def _scheduler_loop(self):
        """调度循环"""
        while self.scheduler_active:
            try:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
            except Exception as e:
                print(f"❌ 调度循环异常: {e}")
                time.sleep(60)
    
    def _scheduled_backup(self, backup_type: str):
        """执行定时备份"""
        try:
            print(f"⏰ 执行定时备份: {backup_type}")
            
            backup_info = self.create_backup(backup_type=backup_type)
            
            if backup_info:
                print(f"✅ 定时备份完成: {backup_info['name']}")
                
                # 清理对应类型的旧备份
                self._cleanup_scheduled_backups(backup_type)
            else:
                print(f"❌ 定时备份失败: {backup_type}")
                
        except Exception as e:
            print(f"❌ 定时备份异常: {e}")
    
    def _cleanup_scheduled_backups(self, backup_type: str):
        """清理定时备份"""
        try:
            # 获取保留策略
            if backup_type == 'daily':
                keep_days = self.config['schedule_settings']['daily_backup']['keep_days']
                cutoff_date = datetime.now() - timedelta(days=keep_days)
            elif backup_type == 'weekly':
                keep_weeks = self.config['schedule_settings']['weekly_backup']['keep_weeks']
                cutoff_date = datetime.now() - timedelta(weeks=keep_weeks)
            elif backup_type == 'monthly':
                keep_months = self.config['schedule_settings']['monthly_backup']['keep_months']
                cutoff_date = datetime.now() - timedelta(days=keep_months * 30)
            else:
                return
            
            # 删除过期的同类型备份
            deleted_count = 0
            for backup in list(self.backup_history):
                if backup['type'] == backup_type:
                    created_at = datetime.fromisoformat(backup['created_at'])
                    if created_at < cutoff_date:
                        if self.delete_backup(backup['name']):
                            deleted_count += 1
            
            if deleted_count > 0:
                print(f"🧹 已清理 {deleted_count} 个过期的{backup_type}备份")
                
        except Exception as e:
            print(f"❌ 清理定时备份失败: {e}")
    
    def export_backup_config(self, export_path: str) -> bool:
        """导出备份配置"""
        try:
            export_data = {
                'config': self.config,
                'history': self.backup_history,
                'exported_at': datetime.now().isoformat()
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 备份配置已导出: {export_path}")
            return True
            
        except Exception as e:
            print(f"❌ 导出备份配置失败: {e}")
            return False
    
    def import_backup_config(self, import_path: str) -> bool:
        """导入备份配置"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # 导入配置
            if 'config' in import_data:
                self.config = import_data['config']
                self.save_backup_config()
            
            # 导入历史（可选）
            if 'history' in import_data:
                # 合并历史记录，避免重复
                existing_names = {b['name'] for b in self.backup_history}
                for backup in import_data['history']:
                    if backup['name'] not in existing_names:
                        self.backup_history.append(backup)
                
                self.save_backup_history()
            
            print(f"✅ 备份配置已导入: {import_path}")
            return True
            
        except Exception as e:
            print(f"❌ 导入备份配置失败: {e}")
            return False

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='YDS-Lab 备份管理工具')
    parser.add_argument('--project-root', help='指定项目根目录路径')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 创建备份命令
    create_parser = subparsers.add_parser('create', help='创建备份')
    create_parser.add_argument('--name', help='备份名称')
    create_parser.add_argument('--type', default='manual', help='备份类型')
    
    # 列出备份命令
    subparsers.add_parser('list', help='列出所有备份')
    
    # 恢复备份命令
    restore_parser = subparsers.add_parser('restore', help='恢复备份')
    restore_parser.add_argument('name', help='备份名称')
    restore_parser.add_argument('--path', help='恢复路径')
    
    # 删除备份命令
    delete_parser = subparsers.add_parser('delete', help='删除备份')
    delete_parser.add_argument('name', help='备份名称')
    
    # 清理备份命令
    subparsers.add_parser('cleanup', help='清理旧备份')
    
    # 备份信息命令
    info_parser = subparsers.add_parser('info', help='查看备份信息')
    info_parser.add_argument('name', help='备份名称')
    
    # 定时备份命令
    schedule_parser = subparsers.add_parser('schedule', help='定时备份管理')
    schedule_parser.add_argument('--start', action='store_true', help='启动定时备份')
    schedule_parser.add_argument('--stop', action='store_true', help='停止定时备份')
    
    # 配置管理命令
    config_parser = subparsers.add_parser('config', help='配置管理')
    config_parser.add_argument('--export', help='导出配置文件路径')
    config_parser.add_argument('--import', dest='import_path', help='导入配置文件路径')
    
    args = parser.parse_args()
    
    backup_manager = BackupManager(args.project_root)
    
    if args.command == 'create':
        backup_info = backup_manager.create_backup(args.name, args.type)
        if not backup_info:
            sys.exit(1)
        
    elif args.command == 'list':
        backups = backup_manager.list_backups()
        print(f"📋 备份列表 ({len(backups)} 个):")
        print("-" * 80)
        
        for backup in sorted(backups, key=lambda x: x['created_at'], reverse=True):
            size_mb = backup['file_size'] / (1024 * 1024)
            created_at = datetime.fromisoformat(backup['created_at'])
            
            print(f"📦 {backup['name']}")
            print(f"    类型: {backup['type']}")
            print(f"    大小: {size_mb:.1f}MB")
            print(f"    文件数: {backup['files_count']}")
            print(f"    创建时间: {created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"    压缩格式: {backup['compression']}")
            print()
        
    elif args.command == 'restore':
        success = backup_manager.restore_backup(args.name, args.path)
        if not success:
            sys.exit(1)
        
    elif args.command == 'delete':
        success = backup_manager.delete_backup(args.name)
        if not success:
            sys.exit(1)
        
    elif args.command == 'cleanup':
        deleted_count = backup_manager.cleanup_old_backups()
        print(f"🧹 清理完成，删除了 {deleted_count} 个旧备份")
        
    elif args.command == 'info':
        backup_info = backup_manager.get_backup_info(args.name)
        if backup_info:
            print(f"📦 备份信息: {args.name}")
            print("-" * 40)
            print(f"类型: {backup_info['type']}")
            print(f"文件路径: {backup_info['file_path']}")
            print(f"文件大小: {backup_info['file_size'] / (1024 * 1024):.1f}MB")
            print(f"文件数量: {backup_info['files_count']}")
            print(f"创建时间: {backup_info['created_at']}")
            print(f"压缩格式: {backup_info['compression']}")
            print(f"文件哈希: {backup_info['file_hash']}")
            print(f"已验证: {'是' if backup_info['verified'] else '否'}")
        else:
            print(f"❌ 未找到备份: {args.name}")
            sys.exit(1)
        
    elif args.command == 'schedule':
        if args.start:
            success = backup_manager.start_scheduled_backup()
            if success:
                print("按 Ctrl+C 停止定时备份...")
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    backup_manager.stop_scheduled_backup()
                    print("\n👋 定时备份已停止")
            else:
                sys.exit(1)
        elif args.stop:
            success = backup_manager.stop_scheduled_backup()
            if not success:
                sys.exit(1)
        else:
            print("❌ 请指定 --start 或 --stop")
        
    elif args.command == 'config':
        if args.export:
            success = backup_manager.export_backup_config(args.export)
            if not success:
                sys.exit(1)
        elif args.import_path:
            success = backup_manager.import_backup_config(args.import_path)
            if not success:
                sys.exit(1)
        else:
            print("❌ 请指定 --export 或 --import")
        
    else:
        # 默认显示状态
        print("🔧 YDS-Lab 备份管理工具")
        print("=" * 50)
        
        backups = backup_manager.list_backups()
        total_size = sum(b['file_size'] for b in backups)
        
        print(f"备份总数: {len(backups)}")
        print(f"总大小: {total_size / (1024 * 1024):.1f}MB")
        
        if backups:
            latest_backup = max(backups, key=lambda x: x['created_at'])
            created_at = datetime.fromisoformat(latest_backup['created_at'])
            print(f"最新备份: {latest_backup['name']} ({created_at.strftime('%Y-%m-%d %H:%M:%S')})")
        
        # 显示配置状态
        schedule_enabled = backup_manager.config['schedule_settings']['enabled']
        print(f"定时备份: {'启用' if schedule_enabled else '禁用'}")

if __name__ == "__main__":
    main()