#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YDS-Lab 安全扫描工具
提供项目安全漏洞检测、敏感信息扫描和安全建议
适配YDS-Lab项目结构和AI Agent协作需求
"""

import os
import re
import json
import yaml
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime
import subprocess
import tempfile
from dataclasses import dataclass, asdict

@dataclass
class SecurityIssue:
    """安全问题数据类"""
    severity: str  # critical, high, medium, low, info
    category: str  # secrets, vulnerabilities, permissions, etc.
    title: str
    description: str
    file_path: str
    line_number: int = 0
    code_snippet: str = ""
    recommendation: str = ""
    cwe_id: str = ""
    cvss_score: float = 0.0

class SecurityScanner:
    """安全扫描器"""
    
    def __init__(self, project_root: str = None):
        """初始化安全扫描器"""
        if project_root is None:
            self.project_root = Path(__file__).parent.parent.parent
        else:
            self.project_root = Path(project_root)
        
        self.config_dir = self.project_root / "Struc" / "GeneralOffice" / "config"
        self.reports_dir = self.project_root / "reports" / "security"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # 扫描配置
        self.scan_config = self._load_scan_config()
        
        # 敏感信息模式
        self.secret_patterns = self._get_secret_patterns()
        
        # 漏洞模式
        self.vulnerability_patterns = self._get_vulnerability_patterns()
        
        # 文件扩展名映射
        self.file_extensions = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.sql': 'sql',
            '.sh': 'shell',
            '.ps1': 'powershell',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.json': 'json',
            '.xml': 'xml',
            '.html': 'html',
            '.htm': 'html',
            '.dockerfile': 'dockerfile',
            '.env': 'env'
        }
        
        # 扫描结果
        self.issues: List[SecurityIssue] = []
        self.scan_stats = {
            'files_scanned': 0,
            'issues_found': 0,
            'critical_issues': 0,
            'high_issues': 0,
            'medium_issues': 0,
            'low_issues': 0,
            'info_issues': 0
        }
    
    def _load_scan_config(self) -> Dict[str, Any]:
        """加载扫描配置"""
        config_file = self.config_dir / "security_config.yaml"
        
        default_config = {
            'scan_options': {
                'scan_secrets': True,
                'scan_vulnerabilities': True,
                'scan_permissions': True,
                'scan_dependencies': True,
                'scan_configuration': True,
                'deep_scan': False
            },
            'exclude_patterns': [
                '*.git/*',
                '*/__pycache__/*',
                '*/node_modules/*',
                '*/venv/*',
                '*/.venv/*',
                '*/logs/*',
                '*/temp/*',
                '*/tmp/*',
                '*.log',
                '*.tmp',
                '*.cache'
            ],
            'include_extensions': [
                '.py', '.js', '.ts', '.java', '.php', '.rb', '.go',
                '.rs', '.cpp', '.c', '.cs', '.sql', '.sh', '.ps1',
                '.yaml', '.yml', '.json', '.xml', '.html', '.htm',
                '.dockerfile', '.env', '.config', '.ini', '.cfg'
            ],
            'severity_levels': {
                'critical': 9.0,
                'high': 7.0,
                'medium': 5.0,
                'low': 3.0,
                'info': 1.0
            }
        }
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f)
                    default_config.update(user_config)
            except Exception as e:
                print(f"⚠️ 加载配置文件失败: {e}")
        
        return default_config
    
    def _get_secret_patterns(self) -> Dict[str, Dict[str, Any]]:
        """获取敏感信息检测模式"""
        return {
            'api_key': {
                'pattern': r'(?i)(api[_-]?key|apikey)\s*[:=]\s*["\']?([a-zA-Z0-9_-]{20,})["\']?',
                'severity': 'high',
                'description': '检测到API密钥',
                'recommendation': '将API密钥移至环境变量或安全配置文件'
            },
            'secret_key': {
                'pattern': r'(?i)(secret[_-]?key|secretkey)\s*[:=]\s*["\']?([a-zA-Z0-9_-]{20,})["\']?',
                'severity': 'high',
                'description': '检测到密钥',
                'recommendation': '将密钥移至环境变量或安全配置文件'
            },
            'password': {
                'pattern': r'(?i)(password|passwd|pwd)\s*[:=]\s*["\']([^"\']{8,})["\']',
                'severity': 'critical',
                'description': '检测到硬编码密码',
                'recommendation': '移除硬编码密码，使用环境变量或安全存储'
            },
            'private_key': {
                'pattern': r'-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----',
                'severity': 'critical',
                'description': '检测到私钥',
                'recommendation': '移除私钥文件，使用安全的密钥管理系统'
            },
            'aws_access_key': {
                'pattern': r'AKIA[0-9A-Z]{16}',
                'severity': 'critical',
                'description': '检测到AWS访问密钥',
                'recommendation': '立即轮换AWS密钥并使用IAM角色'
            },
            'github_token': {
                'pattern': r'ghp_[a-zA-Z0-9]{36}',
                'severity': 'high',
                'description': '检测到GitHub个人访问令牌',
                'recommendation': '撤销并重新生成GitHub令牌'
            },
            'jwt_token': {
                'pattern': r'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*',
                'severity': 'medium',
                'description': '检测到JWT令牌',
                'recommendation': '确保JWT令牌不包含敏感信息且有适当的过期时间'
            },
            'database_url': {
                'pattern': r'(?i)(database[_-]?url|db[_-]?url)\s*[:=]\s*["\']?(postgresql|mysql|mongodb)://[^"\']+["\']?',
                'severity': 'high',
                'description': '检测到数据库连接字符串',
                'recommendation': '将数据库连接信息移至环境变量'
            },
            'email': {
                'pattern': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                'severity': 'low',
                'description': '检测到邮箱地址',
                'recommendation': '确认邮箱地址是否应该公开'
            },
            'ip_address': {
                'pattern': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
                'severity': 'low',
                'description': '检测到IP地址',
                'recommendation': '确认IP地址是否应该硬编码'
            }
        }
    
    def _get_vulnerability_patterns(self) -> Dict[str, Dict[str, Any]]:
        """获取漏洞检测模式"""
        return {
            'sql_injection': {
                'pattern': r'(?i)(execute|query|select|insert|update|delete)\s*\(\s*["\'].*%s.*["\']',
                'severity': 'critical',
                'description': 'SQL注入漏洞',
                'recommendation': '使用参数化查询或ORM',
                'cwe_id': 'CWE-89'
            },
            'command_injection': {
                'pattern': r'(?i)(os\.system|subprocess\.call|exec|eval)\s*\([^)]*input\s*\(',
                'severity': 'critical',
                'description': '命令注入漏洞',
                'recommendation': '验证和清理用户输入，避免直接执行用户输入',
                'cwe_id': 'CWE-78'
            },
            'path_traversal': {
                'pattern': r'(?i)(open|file|read)\s*\([^)]*\.\./.*\)',
                'severity': 'high',
                'description': '路径遍历漏洞',
                'recommendation': '验证文件路径，使用安全的文件操作方法',
                'cwe_id': 'CWE-22'
            },
            'xss_vulnerability': {
                'pattern': r'(?i)(innerHTML|document\.write)\s*\+.*input',
                'severity': 'high',
                'description': 'XSS跨站脚本漏洞',
                'recommendation': '对用户输入进行HTML转义',
                'cwe_id': 'CWE-79'
            },
            'weak_crypto': {
                'pattern': r'(?i)(md5|sha1|des|rc4)\s*\(',
                'severity': 'medium',
                'description': '使用弱加密算法',
                'recommendation': '使用强加密算法如SHA-256、AES等',
                'cwe_id': 'CWE-327'
            },
            'hardcoded_crypto': {
                'pattern': r'(?i)(aes|des|rsa).*key\s*=\s*["\'][^"\']+["\']',
                'severity': 'high',
                'description': '硬编码加密密钥',
                'recommendation': '使用安全的密钥管理系统',
                'cwe_id': 'CWE-798'
            },
            'debug_mode': {
                'pattern': r'(?i)debug\s*=\s*true',
                'severity': 'medium',
                'description': '调试模式启用',
                'recommendation': '在生产环境中禁用调试模式',
                'cwe_id': 'CWE-489'
            },
            'unsafe_deserialization': {
                'pattern': r'(?i)(pickle\.loads|yaml\.load|json\.loads)\s*\([^)]*input',
                'severity': 'high',
                'description': '不安全的反序列化',
                'recommendation': '验证反序列化数据，使用安全的反序列化方法',
                'cwe_id': 'CWE-502'
            }
        }
    
    def scan_project(self) -> Dict[str, Any]:
        """扫描整个项目"""
        print("🔍 开始安全扫描...")
        
        # 重置扫描结果
        self.issues = []
        self.scan_stats = {
            'files_scanned': 0,
            'issues_found': 0,
            'critical_issues': 0,
            'high_issues': 0,
            'medium_issues': 0,
            'low_issues': 0,
            'info_issues': 0
        }
        
        # 获取要扫描的文件
        files_to_scan = self._get_files_to_scan()
        
        print(f"📁 找到 {len(files_to_scan)} 个文件需要扫描")
        
        # 扫描文件
        for file_path in files_to_scan:
            self._scan_file(file_path)
            self.scan_stats['files_scanned'] += 1
        
        # 扫描依赖
        if self.scan_config['scan_options']['scan_dependencies']:
            self._scan_dependencies()
        
        # 扫描配置
        if self.scan_config['scan_options']['scan_configuration']:
            self._scan_configuration()
        
        # 扫描权限
        if self.scan_config['scan_options']['scan_permissions']:
            self._scan_permissions()
        
        # 统计结果
        self._calculate_stats()
        
        print(f"✅ 扫描完成，发现 {self.scan_stats['issues_found']} 个安全问题")
        
        return {
            'issues': [asdict(issue) for issue in self.issues],
            'stats': self.scan_stats,
            'scan_time': datetime.now().isoformat()
        }
    
    def _get_files_to_scan(self) -> List[Path]:
        """获取需要扫描的文件列表"""
        files = []
        
        for root, dirs, filenames in os.walk(self.project_root):
            # 跳过排除的目录
            dirs[:] = [d for d in dirs if not self._should_exclude_path(Path(root) / d)]
            
            for filename in filenames:
                file_path = Path(root) / filename
                
                # 检查是否应该排除
                if self._should_exclude_path(file_path):
                    continue
                
                # 检查文件扩展名
                if file_path.suffix in self.scan_config['include_extensions']:
                    files.append(file_path)
        
        return files
    
    def _should_exclude_path(self, path: Path) -> bool:
        """检查路径是否应该被排除"""
        path_str = str(path.relative_to(self.project_root))
        
        for pattern in self.scan_config['exclude_patterns']:
            if self._match_pattern(path_str, pattern):
                return True
        
        return False
    
    def _match_pattern(self, text: str, pattern: str) -> bool:
        """匹配模式（支持通配符）"""
        import fnmatch
        return fnmatch.fnmatch(text, pattern)
    
    def _scan_file(self, file_path: Path):
        """扫描单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
            
            # 扫描敏感信息
            if self.scan_config['scan_options']['scan_secrets']:
                self._scan_secrets_in_content(file_path, content, lines)
            
            # 扫描漏洞
            if self.scan_config['scan_options']['scan_vulnerabilities']:
                self._scan_vulnerabilities_in_content(file_path, content, lines)
            
        except Exception as e:
            print(f"⚠️ 扫描文件失败 {file_path}: {e}")
    
    def _scan_secrets_in_content(self, file_path: Path, content: str, lines: List[str]):
        """在文件内容中扫描敏感信息"""
        for secret_type, pattern_info in self.secret_patterns.items():
            pattern = pattern_info['pattern']
            
            for match in re.finditer(pattern, content, re.MULTILINE):
                line_number = content[:match.start()].count('\n') + 1
                
                # 获取代码片段
                start_line = max(0, line_number - 2)
                end_line = min(len(lines), line_number + 1)
                code_snippet = '\n'.join(lines[start_line:end_line])
                
                issue = SecurityIssue(
                    severity=pattern_info['severity'],
                    category='secrets',
                    title=f"敏感信息泄露: {secret_type}",
                    description=pattern_info['description'],
                    file_path=str(file_path.relative_to(self.project_root)),
                    line_number=line_number,
                    code_snippet=code_snippet,
                    recommendation=pattern_info['recommendation']
                )
                
                self.issues.append(issue)
    
    def _scan_vulnerabilities_in_content(self, file_path: Path, content: str, lines: List[str]):
        """在文件内容中扫描漏洞"""
        for vuln_type, pattern_info in self.vulnerability_patterns.items():
            pattern = pattern_info['pattern']
            
            for match in re.finditer(pattern, content, re.MULTILINE):
                line_number = content[:match.start()].count('\n') + 1
                
                # 获取代码片段
                start_line = max(0, line_number - 2)
                end_line = min(len(lines), line_number + 1)
                code_snippet = '\n'.join(lines[start_line:end_line])
                
                issue = SecurityIssue(
                    severity=pattern_info['severity'],
                    category='vulnerabilities',
                    title=f"安全漏洞: {vuln_type}",
                    description=pattern_info['description'],
                    file_path=str(file_path.relative_to(self.project_root)),
                    line_number=line_number,
                    code_snippet=code_snippet,
                    recommendation=pattern_info['recommendation'],
                    cwe_id=pattern_info.get('cwe_id', '')
                )
                
                self.issues.append(issue)
    
    def _scan_dependencies(self):
        """扫描依赖安全问题"""
        print("📦 扫描依赖安全问题...")
        
        # 扫描Python依赖
        requirements_files = [
            'requirements.txt',
            'requirements-dev.txt',
            'Pipfile',
            'pyproject.toml'
        ]
        
        for req_file in requirements_files:
            req_path = self.project_root / req_file
            if req_path.exists():
                self._scan_python_dependencies(req_path)
        
        # 扫描Node.js依赖
        package_json = self.project_root / 'package.json'
        if package_json.exists():
            self._scan_nodejs_dependencies(package_json)
    
    def _scan_python_dependencies(self, requirements_file: Path):
        """扫描Python依赖"""
        try:
            # 使用safety检查已知漏洞（如果安装了）
            result = subprocess.run(
                ['safety', 'check', '-r', str(requirements_file), '--json'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                vulnerabilities = json.loads(result.stdout)
                
                for vuln in vulnerabilities:
                    issue = SecurityIssue(
                        severity='high',
                        category='dependencies',
                        title=f"依赖漏洞: {vuln['package']}",
                        description=f"版本 {vuln['installed_version']} 存在已知漏洞",
                        file_path=str(requirements_file.relative_to(self.project_root)),
                        recommendation=f"升级到安全版本: {vuln['safe_versions']}"
                    )
                    self.issues.append(issue)
            
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            # safety未安装或执行失败，跳过
            pass
        except Exception as e:
            print(f"⚠️ 扫描Python依赖失败: {e}")
    
    def _scan_nodejs_dependencies(self, package_json: Path):
        """扫描Node.js依赖"""
        try:
            # 使用npm audit检查漏洞
            result = subprocess.run(
                ['npm', 'audit', '--json'],
                cwd=package_json.parent,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.stdout:
                audit_result = json.loads(result.stdout)
                
                if 'vulnerabilities' in audit_result:
                    for package, vuln_info in audit_result['vulnerabilities'].items():
                        severity = vuln_info.get('severity', 'medium')
                        
                        issue = SecurityIssue(
                            severity=severity,
                            category='dependencies',
                            title=f"Node.js依赖漏洞: {package}",
                            description=f"发现 {vuln_info.get('via', [])} 漏洞",
                            file_path=str(package_json.relative_to(self.project_root)),
                            recommendation="运行 npm audit fix 修复漏洞"
                        )
                        self.issues.append(issue)
            
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            # npm未安装或执行失败，跳过
            pass
        except Exception as e:
            print(f"⚠️ 扫描Node.js依赖失败: {e}")
    
    def _scan_configuration(self):
        """扫描配置安全问题"""
        print("⚙️ 扫描配置安全问题...")
        
        # 检查Docker配置
        dockerfile = self.project_root / 'Dockerfile'
        if dockerfile.exists():
            self._scan_dockerfile(dockerfile)
        
        # 检查环境变量文件
        env_files = ['.env', '.env.local', '.env.production', '.env.development']
        for env_file in env_files:
            env_path = self.project_root / env_file
            if env_path.exists():
                self._scan_env_file(env_path)
        
        # 检查配置文件
        config_files = ['config.yaml', 'config.json', 'settings.py']
        for config_file in config_files:
            config_path = self.project_root / config_file
            if config_path.exists():
                self._scan_config_file(config_path)
    
    def _scan_dockerfile(self, dockerfile: Path):
        """扫描Dockerfile安全问题"""
        try:
            with open(dockerfile, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines, 1):
                line = line.strip()
                
                # 检查使用root用户
                if line.startswith('USER root') or 'USER 0' in line:
                    issue = SecurityIssue(
                        severity='medium',
                        category='configuration',
                        title='Docker容器使用root用户',
                        description='容器以root用户运行存在安全风险',
                        file_path=str(dockerfile.relative_to(self.project_root)),
                        line_number=i,
                        code_snippet=line,
                        recommendation='创建非特权用户运行应用'
                    )
                    self.issues.append(issue)
                
                # 检查暴露敏感端口
                if line.startswith('EXPOSE'):
                    ports = re.findall(r'\d+', line)
                    sensitive_ports = ['22', '3389', '5432', '3306', '27017']
                    
                    for port in ports:
                        if port in sensitive_ports:
                            issue = SecurityIssue(
                                severity='medium',
                                category='configuration',
                                title=f'暴露敏感端口: {port}',
                                description=f'端口 {port} 可能暴露敏感服务',
                                file_path=str(dockerfile.relative_to(self.project_root)),
                                line_number=i,
                                code_snippet=line,
                                recommendation='确认是否需要暴露此端口'
                            )
                            self.issues.append(issue)
        
        except Exception as e:
            print(f"⚠️ 扫描Dockerfile失败: {e}")
    
    def _scan_env_file(self, env_file: Path):
        """扫描环境变量文件"""
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines, 1):
                line = line.strip()
                
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    
                    # 检查空密码
                    if 'password' in key.lower() and not value:
                        issue = SecurityIssue(
                            severity='medium',
                            category='configuration',
                            title='空密码配置',
                            description=f'环境变量 {key} 密码为空',
                            file_path=str(env_file.relative_to(self.project_root)),
                            line_number=i,
                            code_snippet=line,
                            recommendation='设置强密码'
                        )
                        self.issues.append(issue)
                    
                    # 检查默认密码
                    default_passwords = ['password', '123456', 'admin', 'root']
                    if 'password' in key.lower() and value.lower() in default_passwords:
                        issue = SecurityIssue(
                            severity='high',
                            category='configuration',
                            title='使用默认密码',
                            description=f'环境变量 {key} 使用默认密码',
                            file_path=str(env_file.relative_to(self.project_root)),
                            line_number=i,
                            code_snippet=line,
                            recommendation='更改为强密码'
                        )
                        self.issues.append(issue)
        
        except Exception as e:
            print(f"⚠️ 扫描环境变量文件失败: {e}")
    
    def _scan_config_file(self, config_file: Path):
        """扫描配置文件"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查调试模式
            if re.search(r'(?i)debug\s*[:=]\s*true', content):
                issue = SecurityIssue(
                    severity='medium',
                    category='configuration',
                    title='启用调试模式',
                    description='配置文件中启用了调试模式',
                    file_path=str(config_file.relative_to(self.project_root)),
                    recommendation='在生产环境中禁用调试模式'
                )
                self.issues.append(issue)
            
            # 检查不安全的配置
            insecure_configs = [
                (r'(?i)ssl\s*[:=]\s*false', '禁用SSL', '启用SSL加密'),
                (r'(?i)verify\s*[:=]\s*false', '禁用证书验证', '启用证书验证'),
                (r'(?i)secure\s*[:=]\s*false', '禁用安全选项', '启用安全选项')
            ]
            
            for pattern, title, recommendation in insecure_configs:
                if re.search(pattern, content):
                    issue = SecurityIssue(
                        severity='medium',
                        category='configuration',
                        title=title,
                        description=f'配置文件中{title}',
                        file_path=str(config_file.relative_to(self.project_root)),
                        recommendation=recommendation
                    )
                    self.issues.append(issue)
        
        except Exception as e:
            print(f"⚠️ 扫描配置文件失败: {e}")
    
    def _scan_permissions(self):
        """扫描文件权限问题"""
        print("🔐 扫描文件权限问题...")
        
        # 检查敏感文件权限
        sensitive_files = [
            '.env', '.env.local', '.env.production',
            'config.yaml', 'config.json', 'settings.py',
            'id_rsa', 'id_dsa', 'id_ecdsa', 'id_ed25519',
            '*.key', '*.pem', '*.p12', '*.pfx'
        ]
        
        for pattern in sensitive_files:
            for file_path in self.project_root.rglob(pattern):
                if file_path.is_file():
                    self._check_file_permissions(file_path)
    
    def _check_file_permissions(self, file_path: Path):
        """检查文件权限"""
        try:
            # 在Windows上跳过权限检查
            if os.name == 'nt':
                return
            
            stat_info = file_path.stat()
            mode = stat_info.st_mode
            
            # 检查是否对其他用户可读
            if mode & 0o044:  # 其他用户可读
                issue = SecurityIssue(
                    severity='medium',
                    category='permissions',
                    title='敏感文件权限过宽',
                    description=f'文件 {file_path.name} 对其他用户可读',
                    file_path=str(file_path.relative_to(self.project_root)),
                    recommendation='限制文件权限为仅所有者可读写 (chmod 600)'
                )
                self.issues.append(issue)
            
            # 检查是否对其他用户可写
            if mode & 0o022:  # 其他用户可写
                issue = SecurityIssue(
                    severity='high',
                    category='permissions',
                    title='敏感文件权限过宽',
                    description=f'文件 {file_path.name} 对其他用户可写',
                    file_path=str(file_path.relative_to(self.project_root)),
                    recommendation='限制文件权限为仅所有者可读写 (chmod 600)'
                )
                self.issues.append(issue)
        
        except Exception as e:
            print(f"⚠️ 检查文件权限失败 {file_path}: {e}")
    
    def _calculate_stats(self):
        """计算统计信息"""
        self.scan_stats['issues_found'] = len(self.issues)
        
        for issue in self.issues:
            if issue.severity == 'critical':
                self.scan_stats['critical_issues'] += 1
            elif issue.severity == 'high':
                self.scan_stats['high_issues'] += 1
            elif issue.severity == 'medium':
                self.scan_stats['medium_issues'] += 1
            elif issue.severity == 'low':
                self.scan_stats['low_issues'] += 1
            else:
                self.scan_stats['info_issues'] += 1
    
    def generate_report(self, output_format: str = 'markdown') -> str:
        """生成安全扫描报告"""
        if output_format == 'markdown':
            return self._generate_markdown_report()
        elif output_format == 'json':
            return self._generate_json_report()
        elif output_format == 'html':
            return self._generate_html_report()
        else:
            raise ValueError(f"不支持的输出格式: {output_format}")
    
    def _generate_markdown_report(self) -> str:
        """生成Markdown格式报告"""
        report = []
        
        # 报告头部
        report.append("# 🔒 安全扫描报告")
        report.append("")
        report.append(f"**扫描时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"**项目路径**: {self.project_root}")
        report.append("")
        
        # 扫描统计
        report.append("## 📊 扫描统计")
        report.append("")
        report.append(f"- **扫描文件数**: {self.scan_stats['files_scanned']}")
        report.append(f"- **发现问题数**: {self.scan_stats['issues_found']}")
        report.append(f"- **严重问题**: {self.scan_stats['critical_issues']}")
        report.append(f"- **高危问题**: {self.scan_stats['high_issues']}")
        report.append(f"- **中危问题**: {self.scan_stats['medium_issues']}")
        report.append(f"- **低危问题**: {self.scan_stats['low_issues']}")
        report.append(f"- **信息问题**: {self.scan_stats['info_issues']}")
        report.append("")
        
        # 问题详情
        if self.issues:
            report.append("## 🚨 安全问题详情")
            report.append("")
            
            # 按严重程度分组
            severity_order = ['critical', 'high', 'medium', 'low', 'info']
            severity_icons = {
                'critical': '🔴',
                'high': '🟠',
                'medium': '🟡',
                'low': '🔵',
                'info': '⚪'
            }
            
            for severity in severity_order:
                severity_issues = [issue for issue in self.issues if issue.severity == severity]
                
                if severity_issues:
                    report.append(f"### {severity_icons[severity]} {severity.upper()} 级别问题")
                    report.append("")
                    
                    for i, issue in enumerate(severity_issues, 1):
                        report.append(f"#### {i}. {issue.title}")
                        report.append("")
                        report.append(f"**文件**: `{issue.file_path}`")
                        
                        if issue.line_number > 0:
                            report.append(f"**行号**: {issue.line_number}")
                        
                        report.append(f"**类别**: {issue.category}")
                        report.append(f"**描述**: {issue.description}")
                        
                        if issue.cwe_id:
                            report.append(f"**CWE ID**: {issue.cwe_id}")
                        
                        if issue.code_snippet:
                            report.append("**代码片段**:")
                            report.append("```")
                            report.append(issue.code_snippet)
                            report.append("```")
                        
                        report.append(f"**建议**: {issue.recommendation}")
                        report.append("")
        else:
            report.append("## ✅ 未发现安全问题")
            report.append("")
            report.append("恭喜！扫描未发现明显的安全问题。")
            report.append("")
        
        # 安全建议
        report.append("## 💡 安全建议")
        report.append("")
        report.append("1. **定期更新依赖**: 保持所有依赖库为最新版本")
        report.append("2. **使用环境变量**: 将敏感信息存储在环境变量中")
        report.append("3. **启用HTTPS**: 在生产环境中使用HTTPS")
        report.append("4. **输入验证**: 对所有用户输入进行验证和清理")
        report.append("5. **最小权限原则**: 为应用程序分配最小必要权限")
        report.append("6. **定期安全扫描**: 将安全扫描集成到CI/CD流程中")
        report.append("")
        
        return '\n'.join(report)
    
    def _generate_json_report(self) -> str:
        """生成JSON格式报告"""
        report_data = {
            'scan_info': {
                'scan_time': datetime.now().isoformat(),
                'project_path': str(self.project_root),
                'scanner_version': '1.0.0'
            },
            'statistics': self.scan_stats,
            'issues': [asdict(issue) for issue in self.issues]
        }
        
        return json.dumps(report_data, ensure_ascii=False, indent=2)
    
    def _generate_html_report(self) -> str:
        """生成HTML格式报告"""
        # 简化的HTML报告
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>安全扫描报告</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
        .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
        .stat-card {{ background: #fff; border: 1px solid #ddd; padding: 15px; border-radius: 5px; }}
        .issue {{ border-left: 4px solid #ccc; padding: 15px; margin: 10px 0; }}
        .critical {{ border-left-color: #dc3545; }}
        .high {{ border-left-color: #fd7e14; }}
        .medium {{ border-left-color: #ffc107; }}
        .low {{ border-left-color: #0dcaf0; }}
        .info {{ border-left-color: #6c757d; }}
        .code {{ background: #f8f9fa; padding: 10px; border-radius: 3px; font-family: monospace; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔒 安全扫描报告</h1>
        <p><strong>扫描时间</strong>: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>项目路径</strong>: {self.project_root}</p>
    </div>
    
    <h2>📊 扫描统计</h2>
    <div class="stats">
        <div class="stat-card">
            <h3>扫描文件</h3>
            <p>{self.scan_stats['files_scanned']}</p>
        </div>
        <div class="stat-card">
            <h3>发现问题</h3>
            <p>{self.scan_stats['issues_found']}</p>
        </div>
        <div class="stat-card">
            <h3>严重问题</h3>
            <p>{self.scan_stats['critical_issues']}</p>
        </div>
        <div class="stat-card">
            <h3>高危问题</h3>
            <p>{self.scan_stats['high_issues']}</p>
        </div>
    </div>
"""
        
        if self.issues:
            html += "<h2>🚨 安全问题详情</h2>"
            
            for issue in self.issues:
                html += f"""
    <div class="issue {issue.severity}">
        <h3>{issue.title}</h3>
        <p><strong>文件</strong>: {issue.file_path}</p>
        <p><strong>严重程度</strong>: {issue.severity.upper()}</p>
        <p><strong>描述</strong>: {issue.description}</p>
        <p><strong>建议</strong>: {issue.recommendation}</p>
"""
                
                if issue.code_snippet:
                    html += f'<div class="code">{issue.code_snippet}</div>'
                
                html += "</div>"
        
        html += """
</body>
</html>
"""
        
        return html
    
    def save_report(self, output_format: str = 'markdown', filename: str = None) -> str:
        """保存扫描报告"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"security_scan_{timestamp}.{output_format}"
        
        report_content = self.generate_report(output_format)
        report_path = self.reports_dir / filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"📄 报告已保存: {report_path}")
        return str(report_path)
    
    def get_issues_by_severity(self, severity: str) -> List[SecurityIssue]:
        """按严重程度获取问题"""
        return [issue for issue in self.issues if issue.severity == severity]
    
    def get_issues_by_category(self, category: str) -> List[SecurityIssue]:
        """按类别获取问题"""
        return [issue for issue in self.issues if issue.category == category]
    
    def get_critical_issues(self) -> List[SecurityIssue]:
        """获取严重问题"""
        return self.get_issues_by_severity('critical')
    
    def has_critical_issues(self) -> bool:
        """检查是否有严重问题"""
        return len(self.get_critical_issues()) > 0

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='YDS-Lab 安全扫描工具')
    parser.add_argument('--project-root', help='指定项目根目录路径')
    parser.add_argument('--output-format', choices=['markdown', 'json', 'html'], 
                       default='markdown', help='输出格式')
    parser.add_argument('--output-file', help='输出文件名')
    parser.add_argument('--config', help='配置文件路径')
    parser.add_argument('--deep-scan', action='store_true', help='启用深度扫描')
    parser.add_argument('--no-deps', action='store_true', help='跳过依赖扫描')
    parser.add_argument('--no-config', action='store_true', help='跳过配置扫描')
    parser.add_argument('--no-permissions', action='store_true', help='跳过权限扫描')
    
    args = parser.parse_args()
    
    scanner = SecurityScanner(args.project_root)
    
    # 更新扫描配置
    if args.deep_scan:
        scanner.scan_config['scan_options']['deep_scan'] = True
    
    if args.no_deps:
        scanner.scan_config['scan_options']['scan_dependencies'] = False
    
    if args.no_config:
        scanner.scan_config['scan_options']['scan_configuration'] = False
    
    if args.no_permissions:
        scanner.scan_config['scan_options']['scan_permissions'] = False
    
    # 执行扫描
    scan_result = scanner.scan_project()
    
    # 保存报告
    report_path = scanner.save_report(args.output_format, args.output_file)
    
    # 输出摘要
    print("\n" + "="*50)
    print("📋 扫描摘要")
    print("="*50)
    print(f"扫描文件: {scan_result['stats']['files_scanned']}")
    print(f"发现问题: {scan_result['stats']['issues_found']}")
    print(f"严重问题: {scan_result['stats']['critical_issues']}")
    print(f"高危问题: {scan_result['stats']['high_issues']}")
    print(f"中危问题: {scan_result['stats']['medium_issues']}")
    print(f"低危问题: {scan_result['stats']['low_issues']}")
    
    # 如果有严重问题，返回非零退出码
    if scanner.has_critical_issues():
        print("\n⚠️ 发现严重安全问题，请立即处理！")
        sys.exit(1)
    else:
        print("\n✅ 扫描完成，未发现严重安全问题")

if __name__ == "__main__":
    main()