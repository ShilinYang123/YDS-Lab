#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YDS-Lab 每日快照备份工具

功能：
- 自动创建项目快照
- 增量备份支持
- 压缩存储
- 备份验证
- 清理过期备份
- 备份恢复

适配YDS-Lab项目备份需求
"""

import os
import sys
import json
import yaml
import shutil
import zipfile
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
import logging
import subprocess
import tempfile
import threading
import time

class YDSLabDailySnapshot:
    """YDS-Lab每日快照备份工具"""
    
    def __init__(self, project_root: str = "s:/YDS-Lab"):
        self.project_root = Path(project_root)
        # 备份目录迁移：优先使用 01-struc/0B-general-manager/bak，兼容旧路径说明见子模块
        self.backup_dir = self.project_root / "01-struc" / "0B-general-manager" / "bak"
        self.snapshots_dir = self.backup_dir / "snapshots"
        self.config_file = self.backup_dir / "backup_config.yaml"
        
        # 确保目录存在
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置日志
        self.setup_logging()
        
        # 加载配置
        self.config = self.load_config()
        
        # 备份状态
        self.backup_stats = {
            'start_time': None,
            'end_time': None,
            'files_processed': 0,
            'files_backed_up': 0,
            'total_size': 0,
            'compressed_size': 0,
            'errors': []
        }
        
    def setup_logging(self):
        """设置日志系统"""
        try:
            logs_dir = self.project_root / "logs"
            logs_dir.mkdir(parents=True, exist_ok=True)
            
            log_file = logs_dir / "daily_snapshot.log"
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(log_file, encoding='utf-8'),
                    logging.StreamHandler(sys.stdout)
                ]
            )
            
            self.logger = logging.getLogger(__name__)
            self.logger.info("每日快照工具初始化")
            
        except Exception as e:
            print(f"日志系统初始化失败: {e}")
            self.logger = logging.getLogger(__name__)
    
    def load_config(self) -> Dict:
        """加载备份配置"""
        default_config = {
            'backup_schedule': {
                'enabled': True,
                'time': '02:00',  # 凌晨2点
                'timezone': 'Asia/Shanghai'
            },
            'retention': {
                'daily': 7,      # 保留7天的每日备份
                'weekly': 4,     # 保留4周的周备份
                'monthly': 12    # 保留12个月的月备份
            },
            'compression': {
                'enabled': True,
                'level': 6,      # 压缩级别 0-9
                'format': 'zip'  # zip, tar.gz, tar.bz2
            },
            'include_patterns': [
                '**/*.py',
                '**/*.md',
                '**/*.yaml',
                '**/*.yml',
                '**/*.json',
                '**/*.txt',
                '**/*.cfg',
                '**/*.ini',
                'Docs/**/*',
                '03-dev/**/*',  # 仅备份新项目路径
                'tools/**/*',
                'ai/**/*',
                'meta/**/*'
            ],
            'exclude_patterns': [
                '**/__pycache__/**',
                '**/*.pyc',
                '**/*.pyo',
                '**/.git/**',
                '**/node_modules/**',
                '**/venv/**',
                '**/env/**',
                '**/.vscode/**',
                '**/.idea/**',
                '**/backup/**',
                '**/logs/**/*.log',
                '**/*.tmp',
                '**/*.temp',
                '**/cache/**'
            ],
            'verification': {
                'enabled': True,
                'checksum_algorithm': 'sha256'
            },
            'notification': {
                'enabled': False,
                'email': '',
                'webhook': ''
            }
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    # 合并默认配置（浅合并）
                    merged = {**default_config, **config}
                    # 保障 include_patterns 中包含 03-dev（不再自动补充 projects）
                    inc = list(merged.get('include_patterns', []))
                    # 使用集合避免重复
                    inc_set = {p for p in inc}
                    changed = False
                    if '03-dev/**/*' not in inc_set:
                        inc.append('03-dev/**/*')
                        changed = True
                    merged['include_patterns'] = inc
                    if changed:
                        self.logger.info('备份配置已自动补充 include_patterns: 添加 03-dev/**/*')
                    return merged
            except Exception as e:
                self.logger.warning(f"配置文件加载失败，使用默认配置: {e}")
        
        # 保存默认配置
        self.save_config(default_config)
        return default_config
    
    def save_config(self, config: Dict):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            self.logger.info("配置已保存")
        except Exception as e:
            self.logger.error(f"配置保存失败: {e}")
    
    def should_include_file(self, file_path: Path) -> bool:
        """检查文件是否应该包含在备份中"""
        relative_path = file_path.relative_to(self.project_root)
        path_str = str(relative_path).replace('\\', '/')
        
        # 检查排除模式
        for pattern in self.config['exclude_patterns']:
            if file_path.match(pattern) or relative_path.match(pattern):
                return False
        
        # 检查包含模式
        for pattern in self.config['include_patterns']:
            if file_path.match(pattern) or relative_path.match(pattern):
                return True
        
        return False
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """计算文件哈希值"""
        algorithm = self.config['verification']['checksum_algorithm']
        hash_obj = hashlib.new(algorithm)
        
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except Exception as e:
            self.logger.error(f"计算文件哈希失败 {file_path}: {e}")
            return ""
    
    def create_snapshot(self, snapshot_name: str = None) -> Optional[Path]:
        """创建快照"""
        if snapshot_name is None:
            snapshot_name = f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        snapshot_path = self.snapshots_dir / f"{snapshot_name}.zip"
        manifest_path = self.snapshots_dir / f"{snapshot_name}_manifest.json"
        
        self.backup_stats['start_time'] = datetime.now()
        self.logger.info(f"开始创建快照: {snapshot_name}")
        
        try:
            # 收集要备份的文件
            files_to_backup = []
            for root, dirs, files in os.walk(self.project_root):
                root_path = Path(root)
                
                # 跳过备份目录本身
                if self.backup_dir in root_path.parents or root_path == self.backup_dir:
                    continue
                
                for file in files:
                    file_path = root_path / file
                    if self.should_include_file(file_path):
                        files_to_backup.append(file_path)
            
            self.logger.info(f"找到 {len(files_to_backup)} 个文件需要备份")
            
            # 创建压缩包
            manifest = {
                'snapshot_name': snapshot_name,
                'created_at': self.backup_stats['start_time'].isoformat(),
                'project_root': str(self.project_root),
                'files': {},
                'stats': {}
            }
            
            with zipfile.ZipFile(snapshot_path, 'w', 
                               zipfile.ZIP_DEFLATED, 
                               compresslevel=self.config['compression']['level']) as zipf:
                
                for file_path in files_to_backup:
                    try:
                        relative_path = file_path.relative_to(self.project_root)
                        arcname = str(relative_path).replace('\\', '/')
                        
                        # 添加文件到压缩包
                        zipf.write(file_path, arcname)
                        
                        # 记录文件信息
                        file_stat = file_path.stat()
                        file_hash = ""
                        if self.config['verification']['enabled']:
                            file_hash = self.calculate_file_hash(file_path)
                        
                        manifest['files'][arcname] = {
                            'size': file_stat.st_size,
                            'modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                            'hash': file_hash
                        }
                        
                        self.backup_stats['files_processed'] += 1
                        self.backup_stats['files_backed_up'] += 1
                        self.backup_stats['total_size'] += file_stat.st_size
                        
                        if self.backup_stats['files_processed'] % 100 == 0:
                            self.logger.info(f"已处理 {self.backup_stats['files_processed']} 个文件")
                        
                    except Exception as e:
                        error_msg = f"备份文件失败 {file_path}: {e}"
                        self.logger.error(error_msg)
                        self.backup_stats['errors'].append(error_msg)
            
            # 获取压缩后大小
            self.backup_stats['compressed_size'] = snapshot_path.stat().st_size
            
            # 更新统计信息
            manifest['stats'] = {
                'files_count': self.backup_stats['files_backed_up'],
                'total_size': self.backup_stats['total_size'],
                'compressed_size': self.backup_stats['compressed_size'],
                'compression_ratio': round(
                    (1 - self.backup_stats['compressed_size'] / max(self.backup_stats['total_size'], 1)) * 100, 2
                ),
                'errors_count': len(self.backup_stats['errors'])
            }
            
            # 保存清单文件
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            
            self.backup_stats['end_time'] = datetime.now()
            duration = (self.backup_stats['end_time'] - self.backup_stats['start_time']).total_seconds()
            
            self.logger.info(f"快照创建完成: {snapshot_path}")
            self.logger.info(f"备份统计: {self.backup_stats['files_backed_up']} 文件, "
                           f"{self.backup_stats['total_size']} 字节 -> "
                           f"{self.backup_stats['compressed_size']} 字节, "
                           f"耗时 {duration:.2f} 秒")
            
            return snapshot_path
            
        except Exception as e:
            error_msg = f"创建快照失败: {e}"
            self.logger.error(error_msg)
            self.backup_stats['errors'].append(error_msg)
            
            # 清理失败的文件
            if snapshot_path.exists():
                snapshot_path.unlink()
            if manifest_path.exists():
                manifest_path.unlink()
            
            return None
    
    def verify_snapshot(self, snapshot_path: Path) -> bool:
        """验证快照完整性"""
        if not self.config['verification']['enabled']:
            return True
        
        manifest_path = snapshot_path.with_suffix('').with_suffix('_manifest.json')
        if not manifest_path.exists():
            self.logger.error(f"清单文件不存在: {manifest_path}")
            return False
        
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            self.logger.info(f"验证快照: {snapshot_path.name}")
            
            with zipfile.ZipFile(snapshot_path, 'r') as zipf:
                # 检查压缩包完整性
                bad_files = zipf.testzip()
                if bad_files:
                    self.logger.error(f"压缩包损坏，损坏文件: {bad_files}")
                    return False
                
                # 验证文件数量
                zip_files = set(zipf.namelist())
                manifest_files = set(manifest['files'].keys())
                
                if zip_files != manifest_files:
                    missing = manifest_files - zip_files
                    extra = zip_files - manifest_files
                    if missing:
                        self.logger.error(f"缺失文件: {missing}")
                    if extra:
                        self.logger.error(f"额外文件: {extra}")
                    return False
                
                # 验证文件大小
                for file_info in zipf.filelist:
                    if file_info.filename in manifest['files']:
                        expected_size = manifest['files'][file_info.filename]['size']
                        if file_info.file_size != expected_size:
                            self.logger.error(f"文件大小不匹配 {file_info.filename}: "
                                            f"期望 {expected_size}, 实际 {file_info.file_size}")
                            return False
            
            self.logger.info("快照验证通过")
            return True
            
        except Exception as e:
            self.logger.error(f"快照验证失败: {e}")
            return False
    
    def restore_snapshot(self, snapshot_path: Path, restore_dir: Path = None) -> bool:
        """恢复快照"""
        if restore_dir is None:
            restore_dir = self.project_root / "restored" / snapshot_path.stem
        
        restore_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            self.logger.info(f"恢复快照到: {restore_dir}")
            
            with zipfile.ZipFile(snapshot_path, 'r') as zipf:
                zipf.extractall(restore_dir)
            
            self.logger.info("快照恢复完成")
            return True
            
        except Exception as e:
            self.logger.error(f"快照恢复失败: {e}")
            return False
    
    def cleanup_old_snapshots(self):
        """清理过期快照"""
        retention = self.config['retention']
        now = datetime.now()
        
        # 获取所有快照
        snapshots = []
        for snapshot_file in self.snapshots_dir.glob("snapshot_*.zip"):
            try:
                # 从文件名提取时间戳
                timestamp_str = snapshot_file.stem.split('_', 1)[1]
                timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                snapshots.append((timestamp, snapshot_file))
            except:
                continue
        
        snapshots.sort(key=lambda x: x[0], reverse=True)
        
        # 按保留策略分类
        daily_cutoff = now - timedelta(days=retention['daily'])
        weekly_cutoff = now - timedelta(weeks=retention['weekly'])
        monthly_cutoff = now - timedelta(days=retention['monthly'] * 30)
        
        to_keep = set()
        to_delete = []
        
        # 保留每日备份
        for timestamp, snapshot_file in snapshots:
            if timestamp >= daily_cutoff:
                to_keep.add(snapshot_file)
        
        # 保留每周备份（每周第一个）
        weekly_snapshots = {}
        for timestamp, snapshot_file in snapshots:
            if timestamp >= weekly_cutoff:
                week_key = timestamp.strftime('%Y-W%U')
                if week_key not in weekly_snapshots:
                    weekly_snapshots[week_key] = snapshot_file
                    to_keep.add(snapshot_file)
        
        # 保留每月备份（每月第一个）
        monthly_snapshots = {}
        for timestamp, snapshot_file in snapshots:
            if timestamp >= monthly_cutoff:
                month_key = timestamp.strftime('%Y-%m')
                if month_key not in monthly_snapshots:
                    monthly_snapshots[month_key] = snapshot_file
                    to_keep.add(snapshot_file)
        
        # 标记要删除的文件
        for timestamp, snapshot_file in snapshots:
            if snapshot_file not in to_keep:
                to_delete.append(snapshot_file)
        
        # 删除过期快照
        for snapshot_file in to_delete:
            try:
                manifest_file = snapshot_file.with_suffix('').with_suffix('_manifest.json')
                
                snapshot_file.unlink()
                if manifest_file.exists():
                    manifest_file.unlink()
                
                self.logger.info(f"删除过期快照: {snapshot_file.name}")
                
            except Exception as e:
                self.logger.error(f"删除快照失败 {snapshot_file}: {e}")
        
        if to_delete:
            self.logger.info(f"清理完成，删除了 {len(to_delete)} 个过期快照")
        else:
            self.logger.info("没有过期快照需要清理")
    
    def list_snapshots(self) -> List[Dict]:
        """列出所有快照"""
        snapshots = []
        
        for snapshot_file in self.snapshots_dir.glob("snapshot_*.zip"):
            manifest_file = snapshot_file.with_suffix('').with_suffix('_manifest.json')
            
            snapshot_info = {
                'name': snapshot_file.stem,
                'file': snapshot_file.name,
                'size': snapshot_file.stat().st_size,
                'created': datetime.fromtimestamp(snapshot_file.stat().st_ctime),
                'verified': False,
                'stats': {}
            }
            
            # 读取清单信息
            if manifest_file.exists():
                try:
                    with open(manifest_file, 'r', encoding='utf-8') as f:
                        manifest = json.load(f)
                        snapshot_info['stats'] = manifest.get('stats', {})
                        snapshot_info['verified'] = True
                except:
                    pass
            
            snapshots.append(snapshot_info)
        
        return sorted(snapshots, key=lambda x: x['created'], reverse=True)
    
    def run_daily_backup(self) -> bool:
        """执行每日备份"""
        if not self.config['backup_schedule']['enabled']:
            self.logger.info("每日备份已禁用")
            return False
        
        # 创建快照
        snapshot_name = f"daily_{datetime.now().strftime('%Y%m%d')}"
        snapshot_path = self.create_snapshot(snapshot_name)
        
        if snapshot_path is None:
            return False
        
        # 验证快照
        if not self.verify_snapshot(snapshot_path):
            self.logger.error("快照验证失败")
            return False
        
        # 清理过期快照
        self.cleanup_old_snapshots()
        
        return True

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='YDS-Lab每日快照备份工具')
    parser.add_argument('--create', '-c', metavar='NAME',
                       help='创建快照')
    parser.add_argument('--verify', '-v', metavar='SNAPSHOT',
                       help='验证快照')
    parser.add_argument('--restore', '-r', metavar='SNAPSHOT',
                       help='恢复快照')
    parser.add_argument('--restore-to', metavar='DIR',
                       help='恢复到指定目录')
    parser.add_argument('--list', '-l', action='store_true',
                       help='列出所有快照')
    parser.add_argument('--cleanup', action='store_true',
                       help='清理过期快照')
    parser.add_argument('--daily', action='store_true',
                       help='执行每日备份')
    parser.add_argument('--config', action='store_true',
                       help='显示配置信息')
    
    args = parser.parse_args()
    
    backup_tool = YDSLabDailySnapshot()
    
    if args.config:
        print("当前配置:")
        print(yaml.dump(backup_tool.config, default_flow_style=False, allow_unicode=True))
        return
    
    if args.list:
        snapshots = backup_tool.list_snapshots()
        if snapshots:
            print("可用快照:")
            for snapshot in snapshots:
                size_mb = snapshot['size'] / (1024 * 1024)
                verified = "✓" if snapshot['verified'] else "✗"
                print(f"  {snapshot['name']} ({size_mb:.1f}MB) {verified} - {snapshot['created']}")
        else:
            print("没有找到快照")
        return
    
    if args.create:
        snapshot_path = backup_tool.create_snapshot(args.create)
        if snapshot_path:
            print(f"快照已创建: {snapshot_path}")
        else:
            print("快照创建失败")
            sys.exit(1)
        return
    
    if args.verify:
        snapshot_path = backup_tool.snapshots_dir / f"{args.verify}.zip"
        if not snapshot_path.exists():
            print(f"快照不存在: {snapshot_path}")
            sys.exit(1)
        
        if backup_tool.verify_snapshot(snapshot_path):
            print("快照验证通过")
        else:
            print("快照验证失败")
            sys.exit(1)
        return
    
    if args.restore:
        snapshot_path = backup_tool.snapshots_dir / f"{args.restore}.zip"
        if not snapshot_path.exists():
            print(f"快照不存在: {snapshot_path}")
            sys.exit(1)
        
        restore_dir = None
        if args.restore_to:
            restore_dir = Path(args.restore_to)
        
        if backup_tool.restore_snapshot(snapshot_path, restore_dir):
            print("快照恢复成功")
        else:
            print("快照恢复失败")
            sys.exit(1)
        return
    
    if args.cleanup:
        backup_tool.cleanup_old_snapshots()
        return
    
    if args.daily:
        if backup_tool.run_daily_backup():
            print("每日备份完成")
        else:
            print("每日备份失败")
            sys.exit(1)
        return
    
    # 默认执行每日备份
    if backup_tool.run_daily_backup():
        print("每日备份完成")
    else:
        print("每日备份失败")
        sys.exit(1)

if __name__ == "__main__":
    main()