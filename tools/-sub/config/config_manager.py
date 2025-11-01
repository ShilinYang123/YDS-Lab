#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YDS-Lab 配置管理工具
管理项目配置文件、环境变量、MCP服务器配置等
适配YDS-Lab项目结构和AI Agent协作需求
"""

import os
import json
import yaml
import configparser
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
import shutil
import tempfile

class YDSConfigManager:
    """YDS-Lab 配置管理器"""
    
    def __init__(self, project_root: str = None):
        """初始化配置管理器"""
        if project_root is None:
            # 从tools/-sub/config向上三级到达项目根目录
            self.project_root = Path(__file__).parent.parent.parent.parent
        else:
            self.project_root = Path(project_root)
        
        # 配置文件路径
        self.config_dir = self.project_root / "Struc" / "GeneralOffice" / "config"
        self.config_dir.mkdir(exist_ok=True)
        
        # 主配置文件
        self.main_config_file = self.config_dir / "project_config.yaml"
        self.env_config_file = self.config_dir / "environment.yaml"
        self.mcp_config_file = self.config_dir / "mcp_servers.json"
        self.tools_config_file = self.config_dir / "tools_config.yaml"
        
        # 备份目录
        self.backup_dir = self.config_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        # 默认配置
        self.default_config = {
            'project': {
                'name': 'YDS-Lab',
                'version': '1.0.0',
                'description': 'YDS实验室AI Agent协作平台',
                'author': 'YDS-Lab Team'
            },
            'paths': {
                'tools': 'tools',
                'mcp': 'MCP',
                'ai': 'ai',
                'projects': 'projects',
                'docs': 'Docs',
                'logs': 'logs'
            },
            'environment': {
                'python_version': '3.8+',
                'virtual_env': '.venv',
                'requirements': 'requirements.txt'
            },
            'features': {
                'mcp_servers': True,
                'ai_agents': True,
                'quality_check': True,
                'auto_backup': True
            }
        }
    
    def load_config(self, config_file: Path = None) -> Dict[str, Any]:
        """加载配置文件"""
        if config_file is None:
            config_file = self.main_config_file
        
        if not config_file.exists():
            print(f"⚠️ 配置文件不存在: {config_file}")
            return {}
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                if config_file.suffix.lower() in ['.yaml', '.yml']:
                    return yaml.safe_load(f) or {}
                elif config_file.suffix.lower() == '.json':
                    return json.load(f)
                elif config_file.suffix.lower() in ['.ini', '.cfg']:
                    config = configparser.ConfigParser()
                    config.read(config_file, encoding='utf-8')
                    return {section: dict(config[section]) for section in config.sections()}
                else:
                    print(f"❌ 不支持的配置文件格式: {config_file.suffix}")
                    return {}
        except Exception as e:
            print(f"❌ 加载配置文件失败: {e}")
            return {}
    
    def save_config(self, config: Dict[str, Any], config_file: Path = None, backup: bool = True) -> bool:
        """保存配置文件"""
        if config_file is None:
            config_file = self.main_config_file
        
        try:
            # 备份原文件
            if backup and config_file.exists():
                self.backup_config(config_file)
            
            # 保存配置
            with open(config_file, 'w', encoding='utf-8') as f:
                if config_file.suffix.lower() in ['.yaml', '.yml']:
                    yaml.dump(config, f, default_flow_style=False, allow_unicode=True, indent=2)
                elif config_file.suffix.lower() == '.json':
                    json.dump(config, f, ensure_ascii=False, indent=2)
                elif config_file.suffix.lower() in ['.ini', '.cfg']:
                    config_parser = configparser.ConfigParser()
                    for section, options in config.items():
                        config_parser.add_section(section)
                        for key, value in options.items():
                            config_parser.set(section, key, str(value))
                    config_parser.write(f)
                else:
                    print(f"❌ 不支持的配置文件格式: {config_file.suffix}")
                    return False
            
            print(f"✅ 配置已保存: {config_file}")
            return True
            
        except Exception as e:
            print(f"❌ 保存配置文件失败: {e}")
            return False
    
    def backup_config(self, config_file: Path) -> Path:
        """备份配置文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{config_file.stem}_{timestamp}{config_file.suffix}"
        backup_path = self.backup_dir / backup_name
        
        try:
            shutil.copy2(config_file, backup_path)
            print(f"📦 配置已备份: {backup_path}")
            return backup_path
        except Exception as e:
            print(f"❌ 备份配置失败: {e}")
            return None
    
    def initialize_default_config(self) -> bool:
        """初始化默认配置"""
        try:
            print("🔧 初始化默认配置...")
            
            # 创建主配置文件
            if not self.main_config_file.exists():
                self.save_config(self.default_config, self.main_config_file, backup=False)
            
            # 创建环境配置
            env_config = {
                'development': {
                    'debug': True,
                    'log_level': 'DEBUG',
                    'auto_reload': True
                },
                'production': {
                    'debug': False,
                    'log_level': 'INFO',
                    'auto_reload': False
                },
                'paths': {
                    'python_executable': 'python',
                    'pip_executable': 'pip',
                    'virtual_env': '.venv'
                }
            }
            
            if not self.env_config_file.exists():
                self.save_config(env_config, self.env_config_file, backup=False)
            
            # 创建工具配置
            tools_config = {
                'quality_checker': {
                    'enabled': True,
                    'check_naming': True,
                    'check_content': True,
                    'output_format': 'markdown'
                },
                'mcp_health_checker': {
                    'enabled': True,
                    'auto_install': False,
                    'check_dependencies': True
                },
                'report_generator': {
                    'enabled': True,
                    'output_formats': ['markdown', 'json'],
                    'include_timestamps': True
                },
                'environment_manager': {
                    'enabled': True,
                    'auto_setup': False,
                    'clean_on_exit': False
                }
            }
            
            if not self.tools_config_file.exists():
                self.save_config(tools_config, self.tools_config_file, backup=False)
            
            print("✅ 默认配置初始化完成")
            return True
            
        except Exception as e:
            print(f"❌ 初始化默认配置失败: {e}")
            return False
    
    def get_config_value(self, key_path: str, config_file: Path = None, default: Any = None) -> Any:
        """获取配置值（支持点分隔的路径）"""
        config = self.load_config(config_file)
        
        keys = key_path.split('.')
        value = config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set_config_value(self, key_path: str, value: Any, config_file: Path = None) -> bool:
        """设置配置值（支持点分隔的路径）"""
        config = self.load_config(config_file)
        
        keys = key_path.split('.')
        current = config
        
        try:
            # 导航到目标位置
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            
            # 设置值
            current[keys[-1]] = value
            
            # 保存配置
            return self.save_config(config, config_file)
            
        except Exception as e:
            print(f"❌ 设置配置值失败: {e}")
            return False
    
    def merge_configs(self, base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
        """合并配置（递归合并字典）"""
        result = base_config.copy()
        
        for key, value in override_config.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self.merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def validate_config(self, config: Dict[str, Any] = None) -> Tuple[bool, List[str]]:
        """验证配置文件"""
        if config is None:
            config = self.load_config()
        
        errors = []
        
        # 检查必需的配置项
        required_sections = ['project', 'paths', 'environment']
        for section in required_sections:
            if section not in config:
                errors.append(f"缺少必需的配置节: {section}")
        
        # 检查项目信息
        if 'project' in config:
            project_config = config['project']
            required_fields = ['name', 'version']
            for field in required_fields:
                if field not in project_config:
                    errors.append(f"缺少项目配置字段: project.{field}")
        
        # 检查路径配置
        if 'paths' in config:
            paths_config = config['paths']
            for path_name, path_value in paths_config.items():
                path_obj = self.project_root / path_value
                if not path_obj.exists():
                    errors.append(f"路径不存在: {path_name} -> {path_obj}")
        
        return len(errors) == 0, errors
    
    def load_mcp_config(self) -> Dict[str, Any]:
        """加载MCP服务器配置"""
        if not self.mcp_config_file.exists():
            # 创建默认MCP配置
            default_mcp_config = {
                'servers': {},
                'global_settings': {
                    'timeout': 30,
                    'retry_count': 3,
                    'log_level': 'INFO'
                }
            }
            self.save_config(default_mcp_config, self.mcp_config_file, backup=False)
            return default_mcp_config
        
        return self.load_config(self.mcp_config_file)
    
    def update_mcp_server_config(self, server_name: str, server_config: Dict[str, Any]) -> bool:
        """更新MCP服务器配置"""
        mcp_config = self.load_mcp_config()
        
        if 'servers' not in mcp_config:
            mcp_config['servers'] = {}
        
        mcp_config['servers'][server_name] = server_config
        
        return self.save_config(mcp_config, self.mcp_config_file)
    
    def scan_mcp_servers(self) -> Dict[str, Dict[str, Any]]:
        """扫描MCP服务器目录并生成配置"""
        mcp_dir = self.project_root / "MCP"
        servers_config = {}
        
        if not mcp_dir.exists():
            print(f"⚠️ MCP目录不存在: {mcp_dir}")
            return servers_config
        
        # 扫描MCP服务器
        for category_dir in mcp_dir.iterdir():
            if category_dir.is_dir() and not category_dir.name.startswith('.'):
                category_name = category_dir.name
                
                for server_dir in category_dir.iterdir():
                    if server_dir.is_dir():
                        server_name = f"{category_name}_{server_dir.name}"
                        
                        # 检查服务器文件
                        python_files = list(server_dir.glob("*.py"))
                        js_files = list(server_dir.glob("*.js"))
                        config_files = list(server_dir.glob("*.json"))
                        
                        server_config = {
                            'name': server_dir.name,
                            'category': category_name,
                            'path': str(server_dir),
                            'type': 'python' if python_files else 'javascript' if js_files else 'unknown',
                            'main_file': str(python_files[0]) if python_files else str(js_files[0]) if js_files else None,
                            'config_file': str(config_files[0]) if config_files else None,
                            'enabled': True,
                            'auto_start': False
                        }
                        
                        servers_config[server_name] = server_config
        
        return servers_config
    
    def generate_claude_desktop_config(self) -> Dict[str, Any]:
        """生成Claude Desktop配置"""
        mcp_config = self.load_mcp_config()
        claude_config = {
            'mcpServers': {}
        }
        
        for server_name, server_info in mcp_config.get('servers', {}).items():
            if server_info.get('enabled', True):
                if server_info.get('type') == 'python':
                    claude_config['mcpServers'][server_name] = {
                        'command': 'python',
                        'args': [server_info['main_file']],
                        'env': server_info.get('env', {})
                    }
                elif server_info.get('type') == 'javascript':
                    claude_config['mcpServers'][server_name] = {
                        'command': 'node',
                        'args': [server_info['main_file']],
                        'env': server_info.get('env', {})
                    }
        
        return claude_config
    
    def export_config(self, output_file: Path, format: str = 'yaml') -> bool:
        """导出配置到文件"""
        try:
            # 收集所有配置
            all_config = {
                'main': self.load_config(self.main_config_file),
                'environment': self.load_config(self.env_config_file),
                'tools': self.load_config(self.tools_config_file),
                'mcp': self.load_mcp_config()
            }
            
            # 添加元数据
            all_config['_metadata'] = {
                'export_time': datetime.now().isoformat(),
                'project_root': str(self.project_root),
                'version': '1.0.0'
            }
            
            # 保存到指定格式
            if format.lower() == 'yaml':
                with open(output_file, 'w', encoding='utf-8') as f:
                    yaml.dump(all_config, f, default_flow_style=False, allow_unicode=True, indent=2)
            elif format.lower() == 'json':
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(all_config, f, ensure_ascii=False, indent=2)
            else:
                print(f"❌ 不支持的导出格式: {format}")
                return False
            
            print(f"✅ 配置已导出: {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ 导出配置失败: {e}")
            return False
    
    def import_config(self, import_file: Path) -> bool:
        """从文件导入配置"""
        try:
            # 加载导入文件
            with open(import_file, 'r', encoding='utf-8') as f:
                if import_file.suffix.lower() in ['.yaml', '.yml']:
                    imported_config = yaml.safe_load(f)
                elif import_file.suffix.lower() == '.json':
                    imported_config = json.load(f)
                else:
                    print(f"❌ 不支持的导入格式: {import_file.suffix}")
                    return False
            
            # 备份当前配置
            self.backup_all_configs()
            
            # 导入各部分配置
            if 'main' in imported_config:
                self.save_config(imported_config['main'], self.main_config_file)
            
            if 'environment' in imported_config:
                self.save_config(imported_config['environment'], self.env_config_file)
            
            if 'tools' in imported_config:
                self.save_config(imported_config['tools'], self.tools_config_file)
            
            if 'mcp' in imported_config:
                self.save_config(imported_config['mcp'], self.mcp_config_file)
            
            print(f"✅ 配置已导入: {import_file}")
            return True
            
        except Exception as e:
            print(f"❌ 导入配置失败: {e}")
            return False
    
    def backup_all_configs(self) -> List[Path]:
        """备份所有配置文件"""
        backup_files = []
        config_files = [
            self.main_config_file,
            self.env_config_file,
            self.tools_config_file,
            self.mcp_config_file
        ]
        
        for config_file in config_files:
            if config_file.exists():
                backup_path = self.backup_config(config_file)
                if backup_path:
                    backup_files.append(backup_path)
        
        return backup_files
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """列出所有备份文件"""
        backups = []
        
        for backup_file in self.backup_dir.glob("*"):
            if backup_file.is_file():
                stat = backup_file.stat()
                backups.append({
                    'name': backup_file.name,
                    'path': backup_file,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime)
                })
        
        return sorted(backups, key=lambda x: x['modified'], reverse=True)
    
    def clean_old_backups(self, keep_count: int = 10) -> int:
        """清理旧的备份文件"""
        backups = self.list_backups()
        
        if len(backups) <= keep_count:
            return 0
        
        removed_count = 0
        for backup in backups[keep_count:]:
            try:
                backup['path'].unlink()
                removed_count += 1
                print(f"🗑️ 已删除旧备份: {backup['name']}")
            except Exception as e:
                print(f"❌ 删除备份失败: {backup['name']} - {e}")
        
        return removed_count

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='YDS-Lab 配置管理工具')
    parser.add_argument('--project-root', help='指定项目根目录路径')
    parser.add_argument('--init', action='store_true', help='初始化默认配置')
    parser.add_argument('--validate', action='store_true', help='验证配置文件')
    parser.add_argument('--scan-mcp', action='store_true', help='扫描MCP服务器')
    parser.add_argument('--export', help='导出配置到文件')
    parser.add_argument('--import', dest='import_file', help='从文件导入配置')
    parser.add_argument('--format', default='yaml', choices=['yaml', 'json'], help='导出格式')
    parser.add_argument('--backup', action='store_true', help='备份所有配置')
    parser.add_argument('--list-backups', action='store_true', help='列出备份文件')
    parser.add_argument('--clean-backups', type=int, metavar='N', help='清理旧备份，保留N个最新的')
    parser.add_argument('--get', help='获取配置值（使用点分隔路径）')
    parser.add_argument('--set', nargs=2, metavar=('KEY', 'VALUE'), help='设置配置值')
    
    args = parser.parse_args()
    
    manager = YDSConfigManager(args.project_root)
    
    if args.init:
        manager.initialize_default_config()
    elif args.validate:
        is_valid, errors = manager.validate_config()
        if is_valid:
            print("✅ 配置验证通过")
        else:
            print("❌ 配置验证失败:")
            for error in errors:
                print(f"  - {error}")
    elif args.scan_mcp:
        servers = manager.scan_mcp_servers()
        print(f"🔍 发现 {len(servers)} 个MCP服务器:")
        for name, info in servers.items():
            print(f"  - {name}: {info['type']} ({info['category']})")
    elif args.export:
        output_file = Path(args.export)
        manager.export_config(output_file, args.format)
    elif args.import_file:
        import_file = Path(args.import_file)
        manager.import_config(import_file)
    elif args.backup:
        backups = manager.backup_all_configs()
        print(f"📦 已备份 {len(backups)} 个配置文件")
    elif args.list_backups:
        backups = manager.list_backups()
        print(f"📋 找到 {len(backups)} 个备份文件:")
        for backup in backups:
            print(f"  - {backup['name']} ({backup['size']} bytes, {backup['modified']})")
    elif args.clean_backups is not None:
        removed = manager.clean_old_backups(args.clean_backups)
        print(f"🧹 已清理 {removed} 个旧备份文件")
    elif args.get:
        value = manager.get_config_value(args.get)
        print(f"{args.get} = {value}")
    elif args.set:
        key, value = args.set
        # 尝试解析JSON值
        try:
            value = json.loads(value)
        except:
            pass  # 保持字符串值
        
        if manager.set_config_value(key, value):
            print(f"✅ 已设置: {key} = {value}")
        else:
            print(f"❌ 设置失败: {key}")
    else:
        # 默认显示配置状态
        print("🔧 YDS-Lab 配置管理工具")
        print("=" * 50)
        
        # 检查配置文件
        config_files = [
            ('主配置', manager.main_config_file),
            ('环境配置', manager.env_config_file),
            ('工具配置', manager.tools_config_file),
            ('MCP配置', manager.mcp_config_file)
        ]
        
        for name, file_path in config_files:
            status = "✅" if file_path.exists() else "❌"
            print(f"{name}: {status} {file_path}")
        
        # 验证配置
        is_valid, errors = manager.validate_config()
        print(f"\n配置验证: {'✅ 通过' if is_valid else '❌ 失败'}")
        if errors:
            for error in errors:
                print(f"  - {error}")

if __name__ == "__main__":
    main()