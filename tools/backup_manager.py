#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目备份管理工具
功能：
1. 创建项目完整备份
2. 管理备份版本
3. 恢复到指定版本
4. 清理过期备份
"""

import os
import shutil
import datetime
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class BackupInfo:
    """备份信息"""
    backup_id: str
    timestamp: str
    source_path: str
    backup_path: str
    size_bytes: int
    file_count: int
    description: str
    tags: List[str]

class BackupManager:
    """备份管理器"""
    
    def __init__(self, project_root: str, backup_root: str = None):
        self.project_root = Path(project_root).resolve()
        if backup_root:
            self.backup_root = Path(backup_root).resolve()
        else:
            # 按照V5.1规范：统一备份路径为项目根 bak 目录
            self.backup_root = self.project_root / "bak"
        
        self.backup_info_file = self.backup_root / "backup_info.json"
        self.backup_root.mkdir(exist_ok=True)
        
    def get_backup_info(self) -> Dict[str, BackupInfo]:
        """获取所有备份信息"""
        if not self.backup_info_file.exists():
            return {}
        
        try:
            with open(self.backup_info_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {k: BackupInfo(**v) for k, v in data.items()}
        except Exception as e:
            logger.error(f"读取备份信息失败: {e}")
            return {}
    
    def save_backup_info(self, backup_info: Dict[str, BackupInfo]):
        """保存备份信息"""
        try:
            data = {k: asdict(v) for k, v in backup_info.items()}
            with open(self.backup_info_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存备份信息失败: {e}")
    
    def create_backup(self, description: str = "", tags: List[str] = None) -> str:
        """创建备份"""
        timestamp = datetime.datetime.now()
        backup_id = timestamp.strftime('%Y%m%d_%H%M%S')
        
        # 创建备份目录
        backup_path = self.backup_root / backup_id
        backup_path.mkdir(exist_ok=True)
        
        try:
            # 复制项目文件
            file_count = 0
            total_size = 0
            
            # 排除文件和目录
            exclude_patterns = {
                '.git', '__pycache__', '.pytest_cache', 'node_modules',
                '.venv', 'venv', 'env', '*.pyc', '*.pyo', '*.pyd',
                '.DS_Store', 'Thumbs.db', 'encoding_backup', '*.log',
                # 关键：避免将备份目录自身复制到备份内产生递归
                'bak', 'backup', 'backups', 'Backup', 'Backups',
                # 可选：避免将日志与临时报告纳入备份膨胀
                'logs', 'reports'
            }
            
            for root, dirs, files in os.walk(self.project_root):
                # 过滤排除的目录（大小写不敏感）
                dirs[:] = [
                    d for d in dirs
                    if d.lower() not in {p.lower() for p in exclude_patterns}
                    and not d.startswith('.')
                ]
                
                for file in files:
                    if any(pattern in file for pattern in ['.pyc', '.pyo', '.pyd', '.log', '.tmp']):
                        continue
                    
                    src_file = Path(root) / file
                    rel_path = src_file.relative_to(self.project_root)
                    dest_file = backup_path / rel_path
                    
                    # 创建目标目录
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    try:
                        shutil.copy2(src_file, dest_file)
                        file_count += 1
                        total_size += src_file.stat().st_size
                    except Exception as e:
                        logger.warning(f"复制文件失败 {src_file}: {e}")
                        continue
            
            # 创建备份信息
            backup_info = BackupInfo(
                backup_id=backup_id,
                timestamp=timestamp.isoformat(),
                source_path=str(self.project_root),
                backup_path=str(backup_path),
                size_bytes=total_size,
                file_count=file_count,
                description=description or f"自动备份 - {timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
                tags=tags or ['auto']
            )
            
            # 保存备份信息
            all_backups = self.get_backup_info()
            all_backups[backup_id] = backup_info
            self.save_backup_info(all_backups)
            
            logger.info(f"备份创建成功: {backup_id}")
            logger.info(f"备份路径: {backup_path}")
            logger.info(f"文件数: {file_count}")
            logger.info(f"大小: {self.format_size(total_size)}")
            
            return backup_id
            
        except Exception as e:
            logger.error(f"创建备份失败: {e}")
            if backup_path.exists():
                shutil.rmtree(backup_path)
            raise
    
    def list_backups(self) -> List[BackupInfo]:
        """列出所有备份"""
        backups = self.get_backup_info()
        backup_list = list(backups.values())
        backup_list.sort(key=lambda x: x.timestamp, reverse=True)
        return backup_list
    
    def restore_backup(self, backup_id: str, target_path: str = None, force: bool = False) -> bool:
        """恢复到指定备份"""
        backups = self.get_backup_info()
        if backup_id not in backups:
            logger.error(f"备份不存在: {backup_id}")
            return False
        
        backup_info = backups[backup_id]
        backup_path = Path(backup_info.backup_path)
        
        if not backup_path.exists():
            logger.error(f"备份路径不存在: {backup_path}")
            return False
        
        if target_path:
            restore_path = Path(target_path)
        else:
            restore_path = self.project_root
        
        try:
            print(f"准备恢复到: {restore_path}")
            print(f"备份源: {backup_info.source_path}")
            print(f"备份时间: {backup_info.timestamp}")
            if not force:
                response = input("确认恢复? (y/N): ")
                if response.lower() != 'y':
                    print("恢复操作已取消")
                    return False
            
            # 恢复文件
            if restore_path.exists():
                backup_current = self.create_backup("恢复前自动备份", ["auto", "pre-restore"])
                logger.info(f"已创建恢复前备份: {backup_current}")
            
            # 清空目标目录（如果是项目根目录）
            if restore_path == self.project_root:
                for item in restore_path.iterdir():
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
            
            # 复制备份文件
            file_count = 0
            for root, dirs, files in os.walk(backup_path):
                for file in files:
                    src_file = Path(root) / file
                    rel_path = src_file.relative_to(backup_path)
                    dest_file = restore_path / rel_path
                    
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_file, dest_file)
                    file_count += 1
            
            logger.info(f"恢复完成: {file_count} 个文件")
            return True
            
        except Exception as e:
            logger.error(f"恢复失败: {e}")
            return False
    
    def delete_backup(self, backup_id: str, force: bool = False) -> bool:
        """删除备份"""
        backups = self.get_backup_info()
        if backup_id not in backups:
            logger.error(f"备份不存在: {backup_id}")
            return False
        
        backup_info = backups[backup_id]
        backup_path = Path(backup_info.backup_path)
        
        try:
            print(f"准备删除备份: {backup_id}")
            print(f"备份路径: {backup_path}")
            if not force:
                response = input("确认删除? (y/N): ")
                if response.lower() != 'y':
                    print("删除操作已取消")
                    return False
            
            # 删除备份目录
            if backup_path.exists():
                shutil.rmtree(backup_path)
            
            # 删除备份信息
            del backups[backup_id]
            self.save_backup_info(backups)
            
            logger.info(f"备份已删除: {backup_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除备份失败: {e}")
            return False
    
    def cleanup_old_backups(self, keep_count: int = 7) -> int:
        """清理旧备份（保留最新N个）"""
        backups = self.list_backups()
        deleted_count = 0
        
        if len(backups) <= keep_count:
            logger.info(f"备份数量 ({len(backups)}) 未超过保留限制 ({keep_count})，无需清理")
            return 0
        
        backups_to_delete = backups[keep_count:]
        
        for backup in backups_to_delete:
            if self.delete_backup(backup.backup_id):
                deleted_count += 1
        
        logger.info(f"清理完成，删除了 {deleted_count} 个旧备份")
        return deleted_count
    
    def format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def print_backup_summary(self):
        """打印备份摘要"""
        backups = self.list_backups()
        
        print("\n" + "="*60)
        print("备份管理摘要")
        print("="*60)
        print(f"备份存储位置: {self.backup_root}")
        print(f"当前备份数量: {len(backups)}")
        
        if backups:
            total_size = sum(backup.size_bytes for backup in backups)
            print(f"总备份大小: {self.format_size(total_size)}")
            
            print("\n备份列表:")
            for i, backup in enumerate(backups[:10], 1):  # 只显示前10个
                print(f"  {i}. {backup.backup_id}")
                print(f"     时间: {backup.timestamp[:19]}")
                print(f"     大小: {self.format_size(backup.size_bytes)}")
                print(f"     文件: {backup.file_count} 个")
                print(f"     描述: {backup.description}")
                if backup.tags:
                    print(f"     标签: {', '.join(backup.tags)}")
                print()
            
            if len(backups) > 10:
                print(f"  ... 还有 {len(backups) - 10} 个备份")
        
        print("="*60)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='项目备份管理工具')
    parser.add_argument('action', choices=['create', 'list', 'restore', 'delete', 'cleanup', 'summary'],
                       help='操作类型')
    parser.add_argument('--project-root', default='.', help='项目根目录')
    parser.add_argument('--backup-root', help='备份根目录')
    parser.add_argument('--backup-id', help='备份ID（用于恢复或删除）')
    parser.add_argument('--description', help='备份描述')
    parser.add_argument('--tags', nargs='*', help='备份标签')
    parser.add_argument('--keep-count', type=int, default=7, help='清理时保留的备份数量')
    parser.add_argument('--target', help='恢复目标路径')
    parser.add_argument('--force', action='store_true', help='非交互模式：跳过确认')
    parser.add_argument('--auto-cleanup', action='store_true', help='创建备份后自动清理旧备份')
    
    args = parser.parse_args()
    
    # 创建备份管理器
    manager = BackupManager(
        project_root=args.project_root,
        backup_root=args.backup_root
    )
    
    try:
        if args.action == 'create':
            backup_id = manager.create_backup(
                description=args.description,
                tags=args.tags
            )
            print(f"备份创建成功: {backup_id}")
            if args.auto_cleanup:
                deleted = manager.cleanup_old_backups(args.keep_count)
                print(f"自动清理完成，删除 {deleted} 个旧备份")
        
        elif args.action == 'list':
            backups = manager.list_backups()
            if not backups:
                print("没有找到备份")
            else:
                for backup in backups:
                    print(f"ID: {backup.backup_id}")
                    print(f"时间: {backup.timestamp[:19]}")
                    print(f"大小: {manager.format_size(backup.size_bytes)}")
                    print(f"文件数: {backup.file_count}")
                    print(f"描述: {backup.description}")
                    if backup.tags:
                        print(f"标签: {', '.join(backup.tags)}")
                    print("-" * 40)
        
        elif args.action == 'restore':
            if not args.backup_id:
                print("错误: 请指定 --backup-id")
                return 1
            success = manager.restore_backup(args.backup_id, args.target, args.force)
            if success:
                print("恢复成功")
            else:
                print("恢复失败")
                return 1
        
        elif args.action == 'delete':
            if not args.backup_id:
                print("错误: 请指定 --backup-id")
                return 1
            success = manager.delete_backup(args.backup_id, args.force)
            if success:
                print("删除成功")
            else:
                print("删除失败")
                return 1
        
        elif args.action == 'cleanup':
            deleted_count = manager.cleanup_old_backups(args.keep_count)
            print(f"清理完成，删除了 {deleted_count} 个备份")
        
        elif args.action == 'summary':
            manager.print_backup_summary()
    
    except KeyboardInterrupt:
        print("\n操作被用户取消")
        return 1
    except Exception as e:
        print(f"错误: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
