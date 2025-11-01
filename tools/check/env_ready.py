#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YDS-Lab 环境就绪检查工具

功能：
- 检查Python环境
- 验证依赖包
- 检查目录结构
- 验证配置文件
- 检查系统资源
- 网络连接测试
- 服务状态检查

适配YDS-Lab项目环境检查需求
"""

import os
import sys
import json
import yaml
import subprocess
import platform
import psutil
import socket
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import logging
import importlib
import pkg_resources
import tempfile
import shutil

class YDSLabEnvChecker:
    """YDS-Lab环境就绪检查器"""
    
    def __init__(self, project_root: str = "s:/YDS-Lab"):
        self.project_root = Path(project_root)
        self.check_results = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'unknown',
            'checks': {},
            'warnings': [],
            'errors': [],
            'recommendations': []
        }
        
        # 设置日志
        self.setup_logging()
        
        # 必需的目录结构
        self.required_dirs = [
            'Docs',
            'ai',
            'tools',
            'projects',
            'env',
            'Struc/GeneralOffice/logs',
            'logs',
            'backup'
        ]
        
        # 必需的Python包
        self.required_packages = {
            'yaml': 'pyyaml>=5.4.0',
            'requests': 'requests>=2.25.0',
            'psutil': 'psutil>=5.8.0',
            'pathlib': None,  # 内置包
            'json': None,     # 内置包
            'logging': None,  # 内置包
            'datetime': None, # 内置包
            'subprocess': None, # 内置包
            'platform': None,   # 内置包
            'socket': None,     # 内置包
            'tempfile': None,   # 内置包
            'shutil': None      # 内置包
        }
        
        # 可选的Python包
        self.optional_packages = {
            'numpy': 'numpy>=1.20.0',
            'pandas': 'pandas>=1.3.0',
            'matplotlib': 'matplotlib>=3.4.0',
            'jupyter': 'jupyter>=1.0.0',
            'flask': 'flask>=2.0.0',
            'fastapi': 'fastapi>=0.68.0',
            'sqlalchemy': 'sqlalchemy>=1.4.0',
            'redis': 'redis>=3.5.0',
            'celery': 'celery>=5.2.0'
        }
        
        # 系统要求
        self.system_requirements = {
            'python_version': (3, 8),  # 最低Python版本
            'memory_gb': 4,            # 最低内存要求(GB)
            'disk_space_gb': 10,       # 最低磁盘空间(GB)
            'cpu_cores': 2             # 最低CPU核心数
        }
        
        # 网络检查端点
        self.network_endpoints = [
            ('github.com', 443),
            ('pypi.org', 443),
            ('google.com', 80),
            ('baidu.com', 80)
        ]
        
    def setup_logging(self):
        """设置日志系统"""
        try:
            logs_dir = self.project_root / "Struc" / "GeneralOffice" / "logs"
            logs_dir.mkdir(parents=True, exist_ok=True)
            
            log_file = logs_dir / "env_checker.log"
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(log_file, encoding='utf-8'),
                    logging.StreamHandler(sys.stdout)
                ]
            )
            
            self.logger = logging.getLogger(__name__)
            self.logger.info("环境检查器初始化")
            
        except Exception as e:
            print(f"日志系统初始化失败: {e}")
            self.logger = logging.getLogger(__name__)
    
    def check_python_version(self) -> Dict:
        """检查Python版本"""
        result = {
            'name': 'Python版本检查',
            'status': 'pass',
            'details': {},
            'messages': []
        }
        
        try:
            current_version = sys.version_info
            required_version = self.system_requirements['python_version']
            
            result['details'] = {
                'current_version': f"{current_version.major}.{current_version.minor}.{current_version.micro}",
                'required_version': f"{required_version[0]}.{required_version[1]}+",
                'executable': sys.executable,
                'platform': platform.platform()
            }
            
            if current_version >= required_version:
                result['messages'].append(f"Python版本满足要求: {result['details']['current_version']}")
            else:
                result['status'] = 'fail'
                result['messages'].append(
                    f"Python版本过低: {result['details']['current_version']}, "
                    f"需要 {result['details']['required_version']}"
                )
                
        except Exception as e:
            result['status'] = 'error'
            result['messages'].append(f"Python版本检查失败: {e}")
        
        return result
    
    def check_required_packages(self) -> Dict:
        """检查必需的Python包"""
        result = {
            'name': '必需包检查',
            'status': 'pass',
            'details': {},
            'messages': []
        }
        
        missing_packages = []
        installed_packages = {}
        
        for package_name, requirement in self.required_packages.items():
            try:
                if requirement is None:
                    # 内置包
                    importlib.import_module(package_name)
                    installed_packages[package_name] = 'built-in'
                else:
                    # 第三方包
                    pkg = pkg_resources.get_distribution(package_name)
                    installed_packages[package_name] = pkg.version
                    
                    # 检查版本要求
                    if requirement:
                        pkg_resources.require([requirement])
                        
            except (ImportError, pkg_resources.DistributionNotFound, pkg_resources.VersionConflict) as e:
                missing_packages.append({
                    'package': package_name,
                    'requirement': requirement or 'built-in',
                    'error': str(e)
                })
        
        result['details'] = {
            'installed': installed_packages,
            'missing': missing_packages
        }
        
        if missing_packages:
            result['status'] = 'fail'
            result['messages'].append(f"缺少必需包: {[p['package'] for p in missing_packages]}")
        else:
            result['messages'].append(f"所有必需包已安装: {len(installed_packages)} 个")
        
        return result
    
    def check_optional_packages(self) -> Dict:
        """检查可选的Python包"""
        result = {
            'name': '可选包检查',
            'status': 'pass',
            'details': {},
            'messages': []
        }
        
        missing_packages = []
        installed_packages = {}
        
        for package_name, requirement in self.optional_packages.items():
            try:
                pkg = pkg_resources.get_distribution(package_name)
                installed_packages[package_name] = pkg.version
                
                # 检查版本要求
                if requirement:
                    pkg_resources.require([requirement])
                    
            except (pkg_resources.DistributionNotFound, pkg_resources.VersionConflict) as e:
                missing_packages.append({
                    'package': package_name,
                    'requirement': requirement,
                    'error': str(e)
                })
        
        result['details'] = {
            'installed': installed_packages,
            'missing': missing_packages
        }
        
        if missing_packages:
            result['status'] = 'warning'
            result['messages'].append(f"缺少可选包: {[p['package'] for p in missing_packages]}")
        
        result['messages'].append(f"已安装可选包: {len(installed_packages)} 个")
        
        return result
    
    def check_directory_structure(self) -> Dict:
        """检查目录结构"""
        result = {
            'name': '目录结构检查',
            'status': 'pass',
            'details': {},
            'messages': []
        }
        
        missing_dirs = []
        existing_dirs = []
        
        for dir_name in self.required_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists() and dir_path.is_dir():
                existing_dirs.append({
                    'name': dir_name,
                    'path': str(dir_path),
                    'size': self._get_dir_size(dir_path),
                    'files_count': len(list(dir_path.rglob('*')))
                })
            else:
                missing_dirs.append(dir_name)
        
        result['details'] = {
            'project_root': str(self.project_root),
            'existing': existing_dirs,
            'missing': missing_dirs
        }
        
        if missing_dirs:
            result['status'] = 'fail'
            result['messages'].append(f"缺少必需目录: {missing_dirs}")
        else:
            result['messages'].append(f"目录结构完整: {len(existing_dirs)} 个目录")
        
        return result
    
    def check_system_resources(self) -> Dict:
        """检查系统资源"""
        result = {
            'name': '系统资源检查',
            'status': 'pass',
            'details': {},
            'messages': []
        }
        
        try:
            # 内存检查
            memory = psutil.virtual_memory()
            memory_gb = memory.total / (1024**3)
            
            # 磁盘空间检查
            disk = psutil.disk_usage(str(self.project_root))
            disk_free_gb = disk.free / (1024**3)
            
            # CPU检查
            cpu_count = psutil.cpu_count()
            cpu_percent = psutil.cpu_percent(interval=1)
            
            result['details'] = {
                'memory': {
                    'total_gb': round(memory_gb, 2),
                    'available_gb': round(memory.available / (1024**3), 2),
                    'percent_used': memory.percent,
                    'required_gb': self.system_requirements['memory_gb']
                },
                'disk': {
                    'total_gb': round(disk.total / (1024**3), 2),
                    'free_gb': round(disk_free_gb, 2),
                    'percent_used': round((disk.used / disk.total) * 100, 2),
                    'required_gb': self.system_requirements['disk_space_gb']
                },
                'cpu': {
                    'cores': cpu_count,
                    'usage_percent': cpu_percent,
                    'required_cores': self.system_requirements['cpu_cores']
                }
            }
            
            # 检查是否满足要求
            issues = []
            
            if memory_gb < self.system_requirements['memory_gb']:
                issues.append(f"内存不足: {memory_gb:.1f}GB < {self.system_requirements['memory_gb']}GB")
            
            if disk_free_gb < self.system_requirements['disk_space_gb']:
                issues.append(f"磁盘空间不足: {disk_free_gb:.1f}GB < {self.system_requirements['disk_space_gb']}GB")
            
            if cpu_count < self.system_requirements['cpu_cores']:
                issues.append(f"CPU核心数不足: {cpu_count} < {self.system_requirements['cpu_cores']}")
            
            if issues:
                result['status'] = 'warning'
                result['messages'].extend(issues)
            else:
                result['messages'].append("系统资源满足要求")
                
        except Exception as e:
            result['status'] = 'error'
            result['messages'].append(f"系统资源检查失败: {e}")
        
        return result
    
    def check_network_connectivity(self) -> Dict:
        """检查网络连接"""
        result = {
            'name': '网络连接检查',
            'status': 'pass',
            'details': {},
            'messages': []
        }
        
        connectivity_results = []
        
        for host, port in self.network_endpoints:
            try:
                start_time = datetime.now()
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result_code = sock.connect_ex((host, port))
                sock.close()
                end_time = datetime.now()
                
                latency = (end_time - start_time).total_seconds() * 1000
                
                connectivity_results.append({
                    'host': host,
                    'port': port,
                    'status': 'success' if result_code == 0 else 'failed',
                    'latency_ms': round(latency, 2) if result_code == 0 else None,
                    'error_code': result_code if result_code != 0 else None
                })
                
            except Exception as e:
                connectivity_results.append({
                    'host': host,
                    'port': port,
                    'status': 'error',
                    'error': str(e)
                })
        
        result['details'] = {'endpoints': connectivity_results}
        
        failed_connections = [r for r in connectivity_results if r['status'] != 'success']
        
        if failed_connections:
            result['status'] = 'warning'
            result['messages'].append(f"部分网络连接失败: {len(failed_connections)} 个")
        else:
            result['messages'].append("网络连接正常")
        
        return result
    
    def check_config_files(self) -> Dict:
        """检查配置文件"""
        result = {
            'name': '配置文件检查',
            'status': 'pass',
            'details': {},
            'messages': []
        }
        
        config_files = [
            ('tools/update_structure.py', 'required'),
            ('tools/check_structure.py', 'required'),
            ('tools/start.py', 'required'),
            ('tools/finish.py', 'required'),
            ('Struc/GeneralOffice/logs/project_config.yaml', 'optional'),
            ('env/requirements.txt', 'optional'),
            ('backup/backup_config.yaml', 'optional')
        ]
        
        missing_required = []
        missing_optional = []
        existing_files = []
        
        for file_path, file_type in config_files:
            full_path = self.project_root / file_path
            
            if full_path.exists():
                try:
                    file_stat = full_path.stat()
                    existing_files.append({
                        'path': file_path,
                        'type': file_type,
                        'size': file_stat.st_size,
                        'modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                    })
                except Exception as e:
                    existing_files.append({
                        'path': file_path,
                        'type': file_type,
                        'error': str(e)
                    })
            else:
                if file_type == 'required':
                    missing_required.append(file_path)
                else:
                    missing_optional.append(file_path)
        
        result['details'] = {
            'existing': existing_files,
            'missing_required': missing_required,
            'missing_optional': missing_optional
        }
        
        if missing_required:
            result['status'] = 'fail'
            result['messages'].append(f"缺少必需配置文件: {missing_required}")
        
        if missing_optional:
            result['messages'].append(f"缺少可选配置文件: {missing_optional}")
        
        result['messages'].append(f"找到配置文件: {len(existing_files)} 个")
        
        return result
    
    def check_write_permissions(self) -> Dict:
        """检查写入权限"""
        result = {
            'name': '写入权限检查',
            'status': 'pass',
            'details': {},
            'messages': []
        }
        
        test_dirs = [
            self.project_root / 'logs',
            self.project_root / 'backup',
            self.project_root / 'projects',
            self.project_root / 'Struc' / 'GeneralOffice' / 'logs'
        ]
        
        permission_results = []
        
        for test_dir in test_dirs:
            try:
                # 确保目录存在
                test_dir.mkdir(parents=True, exist_ok=True)
                
                # 测试写入
                test_file = test_dir / f'write_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.tmp'
                
                with open(test_file, 'w') as f:
                    f.write('write test')
                
                # 测试读取
                with open(test_file, 'r') as f:
                    content = f.read()
                
                # 清理测试文件
                test_file.unlink()
                
                permission_results.append({
                    'directory': str(test_dir),
                    'writable': True,
                    'readable': True
                })
                
            except Exception as e:
                permission_results.append({
                    'directory': str(test_dir),
                    'writable': False,
                    'readable': False,
                    'error': str(e)
                })
        
        result['details'] = {'permissions': permission_results}
        
        failed_permissions = [r for r in permission_results if not r.get('writable', False)]
        
        if failed_permissions:
            result['status'] = 'fail'
            result['messages'].append(f"写入权限不足: {len(failed_permissions)} 个目录")
        else:
            result['messages'].append("写入权限正常")
        
        return result
    
    def _get_dir_size(self, dir_path: Path) -> int:
        """获取目录大小"""
        try:
            total_size = 0
            for file_path in dir_path.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            return total_size
        except:
            return 0
    
    def run_all_checks(self) -> Dict:
        """运行所有检查"""
        self.logger.info("开始环境检查")
        
        checks = [
            self.check_python_version,
            self.check_required_packages,
            self.check_optional_packages,
            self.check_directory_structure,
            self.check_system_resources,
            self.check_network_connectivity,
            self.check_config_files,
            self.check_write_permissions
        ]
        
        for check_func in checks:
            try:
                check_result = check_func()
                self.check_results['checks'][check_result['name']] = check_result
                
                # 收集警告和错误
                if check_result['status'] == 'warning':
                    self.check_results['warnings'].extend(check_result['messages'])
                elif check_result['status'] in ['fail', 'error']:
                    self.check_results['errors'].extend(check_result['messages'])
                
            except Exception as e:
                error_msg = f"检查失败 {check_func.__name__}: {e}"
                self.logger.error(error_msg)
                self.check_results['errors'].append(error_msg)
        
        # 确定总体状态
        failed_checks = [name for name, result in self.check_results['checks'].items() 
                        if result['status'] in ['fail', 'error']]
        warning_checks = [name for name, result in self.check_results['checks'].items() 
                         if result['status'] == 'warning']
        
        if failed_checks:
            self.check_results['overall_status'] = 'fail'
        elif warning_checks:
            self.check_results['overall_status'] = 'warning'
        else:
            self.check_results['overall_status'] = 'pass'
        
        # 生成建议
        self._generate_recommendations()
        
        self.logger.info(f"环境检查完成，状态: {self.check_results['overall_status']}")
        
        return self.check_results
    
    def _generate_recommendations(self):
        """生成改进建议"""
        recommendations = []
        
        # 基于检查结果生成建议
        for check_name, check_result in self.check_results['checks'].items():
            if check_result['status'] == 'fail':
                if check_name == '必需包检查':
                    missing = check_result['details'].get('missing', [])
                    if missing:
                        recommendations.append(
                            f"安装缺少的必需包: pip install {' '.join([p['package'] for p in missing])}"
                        )
                
                elif check_name == '目录结构检查':
                    missing = check_result['details'].get('missing', [])
                    if missing:
                        recommendations.append(
                            f"创建缺少的目录: {', '.join(missing)}"
                        )
                
                elif check_name == '配置文件检查':
                    missing = check_result['details'].get('missing_required', [])
                    if missing:
                        recommendations.append(
                            f"创建缺少的配置文件: {', '.join(missing)}"
                        )
            
            elif check_result['status'] == 'warning':
                if check_name == '可选包检查':
                    missing = check_result['details'].get('missing', [])
                    if missing:
                        recommendations.append(
                            f"考虑安装可选包以获得更好体验: pip install {' '.join([p['package'] for p in missing])}"
                        )
                
                elif check_name == '系统资源检查':
                    details = check_result['details']
                    if details.get('memory', {}).get('available_gb', 0) < 2:
                        recommendations.append("建议释放内存或增加系统内存")
                    if details.get('disk', {}).get('free_gb', 0) < 5:
                        recommendations.append("建议清理磁盘空间")
        
        self.check_results['recommendations'] = recommendations
    
    def save_report(self, output_file: str = None) -> Path:
        """保存检查报告"""
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"env_check_report_{timestamp}.json"
        
        report_path = self.project_root / "logs" / output_file
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.check_results, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"检查报告已保存: {report_path}")
        return report_path
    
    def print_summary(self):
        """打印检查摘要"""
        print(f"\n{'='*60}")
        print(f"YDS-Lab 环境检查报告")
        print(f"{'='*60}")
        print(f"检查时间: {self.check_results['timestamp']}")
        print(f"总体状态: {self.check_results['overall_status'].upper()}")
        
        print(f"\n检查结果:")
        for check_name, result in self.check_results['checks'].items():
            status_symbol = {
                'pass': '✓',
                'warning': '⚠',
                'fail': '✗',
                'error': '✗'
            }.get(result['status'], '?')
            
            print(f"  {status_symbol} {check_name}: {result['status']}")
            for message in result['messages']:
                print(f"    - {message}")
        
        if self.check_results['warnings']:
            print(f"\n警告 ({len(self.check_results['warnings'])}):")
            for warning in self.check_results['warnings']:
                print(f"  ⚠ {warning}")
        
        if self.check_results['errors']:
            print(f"\n错误 ({len(self.check_results['errors'])}):")
            for error in self.check_results['errors']:
                print(f"  ✗ {error}")
        
        if self.check_results['recommendations']:
            print(f"\n建议:")
            for i, recommendation in enumerate(self.check_results['recommendations'], 1):
                print(f"  {i}. {recommendation}")
        
        print(f"\n{'='*60}")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='YDS-Lab环境就绪检查工具')
    parser.add_argument('--output', '-o', metavar='FILE',
                       help='保存报告到文件')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='静默模式，只输出结果')
    parser.add_argument('--json', action='store_true',
                       help='输出JSON格式结果')
    
    args = parser.parse_args()
    
    checker = YDSLabEnvChecker()
    
    # 运行检查
    results = checker.run_all_checks()
    
    # 保存报告
    if args.output:
        checker.save_report(args.output)
    
    # 输出结果
    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    elif not args.quiet:
        checker.print_summary()
    
    # 设置退出码
    if results['overall_status'] == 'fail':
        sys.exit(1)
    elif results['overall_status'] == 'warning':
        sys.exit(2)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()