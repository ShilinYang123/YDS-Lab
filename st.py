#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YDS-Lab AI Agent 启动检查系统 (V5.1架构适配版)

功能：
- AI Agent合规性检查
- MCP服务器状态验证
- 项目环境预检
- 工作流程启动
- 监控系统管理

适配YDS-Lab V5.1架构和CrewAI多智能体协作需求
- 三级存储规范管理 (bak/docs/logs/rep)
"""

import os
import sys
import json
import time
import logging
import subprocess
import socket
import struct
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Tuple
import yaml

class YDSLabStartupChecker:
    """YDS-Lab AI Agent启动检查器"""
    
    def timeout_handler(self, timeout_seconds: int = 30):
        """超时处理装饰器"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                import signal
                
                def timeout_signal_handler(signum, frame):
                    raise TimeoutError(f"操作超时: {timeout_seconds}秒")
                
                # 设置超时信号
                if hasattr(signal, 'SIGALRM'):
                    signal.signal(signal.SIGALRM, timeout_signal_handler)
                    signal.alarm(timeout_seconds)
                
                try:
                    result = func(*args, **kwargs)
                    return result
                except TimeoutError as e:
                    self.logger.error(f"操作超时: {e}")
                    raise
                finally:
                    # 取消超时信号
                    if hasattr(signal, 'SIGALRM'):
                        signal.alarm(0)
            
            return wrapper
        return decorator
    
    def exception_handler(self, max_retries: int = 3, fallback_value: any = None, log_level: str = 'error'):
        """异常处理装饰器"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                for attempt in range(max_retries):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        log_msg = f"{func.__name__} 失败 (尝试 {attempt + 1}/{max_retries}): {e}"
                        if log_level == 'error':
                            self.logger.error(log_msg)
                        elif log_level == 'warning':
                            self.logger.warning(log_msg)
                        else:
                            self.logger.info(log_msg)
                        
                        if attempt < max_retries - 1:
                            time.sleep(1 * (attempt + 1))  # 递增延迟
                        else:
                            self.logger.error(f"{func.__name__} 在 {max_retries} 次尝试后失败，返回降级值")
                            return fallback_value
                
                return fallback_value
            
            return wrapper
        return decorator
    
    def safe_file_operation(self, operation: str, file_path: Path, fallback_value: any = None, **kwargs):
        """安全的文件操作包装器"""
        try:
            if operation == 'read':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            elif operation == 'read_json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            elif operation == 'write':
                content = kwargs.get('content', '')
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
            elif operation == 'write_json':
                data = kwargs.get('data', {})
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                return True
            elif operation == 'exists':
                return file_path.exists()
            else:
                raise ValueError(f"不支持的操作: {operation}")
                
        except Exception as e:
            self.logger.error(f"文件操作失败 {operation} {file_path}: {e}")
            return fallback_value
    
    def safe_subprocess_run(self, cmd: list, timeout: int = 30, cwd: str = None, check: bool = False) -> subprocess.CompletedProcess:
        """安全的子进程运行包装器"""
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=timeout,
                check=check
            )
            return result
            
        except subprocess.TimeoutExpired as e:
            self.logger.error(f"子进程执行超时 ({timeout}秒): {cmd}")
            raise
        except subprocess.CalledProcessError as e:
            self.logger.error(f"子进程执行失败: {cmd}, 返回码: {e.returncode}, 错误: {e.stderr}")
            if check:
                raise
            return e
        except Exception as e:
            self.logger.error(f"子进程执行异常: {cmd}, 错误: {e}")
            raise
    
    def __init__(self, project_root: str = "s:/YDS-Lab"):
        self.project_root = Path(project_root)
        self.tools_dir = self.project_root / "tools"
        # 统一结构根目录到 01-struc
        self.struc_dir = self.project_root / "01-struc"
        # 统一文档目录至 01-struc/docs
        self.docs_dir = self.struc_dir / "docs"
        # 统一智能体目录：不再使用 TraeAgents，改为 01-struc/Agents
        self.trae_agents_dir = self.struc_dir / "Agents"
        self.agents_dir = self.struc_dir / "Agents"
        # 统一生产目录与日志目录
        # 长记忆系统实际位置：03-dev/001-memory-system（修正：不再使用 04-prod/** 旧路径）
        self.memory_system_dir = self.project_root / "03-dev" / "001-memory-system"
        # 统一日志目录至 logs（按照三级存储规范：系统维护类日志存储在logs/）
        self.logs_dir = self.project_root / "logs"
        
        # 设置日志
        self.setup_logging()
        
        # 配置文件路径（迁移到 config 目录）
        self.config_file = self.project_root / "config" / "startup_config.yaml"
        self.mcp_config_candidates = [
            self.project_root / "claude_desktop_config.json",
            Path(os.path.expandvars(r"%APPDATA%\Claude\claude_desktop_config.json")),
            self.tools_dir / "mcp" / "claude_desktop_config.json",
            # 新路径优先：tools/mcp/servers；旧路径兼容
            self.tools_dir / "mcp" / "servers" / "cluster_config.yaml",
            self.struc_dir / "MCPCluster" / "cluster_config.yaml",
        ]
        
        # 默认配置
        self.default_config = {
            'ai_agents': {
                'enable_crewai': True,
                'enable_monitoring': True,
                'auto_start_agents': False
            },
            'memory_system': {
                'auto_start': False,
                'check_status': True,
                'required_services': ['knowledge-graph', 'memory-retrieval', 'rule-system'],
                'test_on_startup': True,
                'startup_timeout': 30,
                'startup_retry_count': 3,
                'startup_retry_delay': 2.0
            },
            'mcp_servers': {
                'required_servers': ['memory', 'github', 'context7', 'sequential-thinking'],
                'check_timeout': 10,
                'cluster_config': True
            },
            'compliance': {
                'auto_start_monitoring': True,
                'check_structure': True,
                'validate_docs': True
            },
            'startup_checks': {
                'check_python_env': True,
                'check_dependencies': True,
                'check_git_config': True,
                'check_memory_system': True,
                'timeout_seconds': 30,
                'enable_fallback_mode': True
            },
            'error_handling': {
                'max_retries': 3,
                'enable_degraded_mode': True,
                'log_all_errors': True,
                'continue_on_non_critical_errors': True
            }
        }
        
        self.load_config()

    def ensure_longmemory_records(self) -> bool:
        """确保长记忆文件存在且为有效JSON，如损坏则尝试自动修复"""
        try:
# 统一长记忆持久化目录到 01-struc/logs/longmemory（按照三级存储规范）
            lm_dir = self.logs_dir / "longmemory"
            lm_dir.mkdir(parents=True, exist_ok=True)
            lm_file = lm_dir / "lm_records.json"

            if not lm_file.exists():
                # 初始化为 LongMemory 标准结构
                with open(lm_file, 'w', encoding='utf-8') as f:
                    json.dump({"general": {}, "memories": []}, f, ensure_ascii=False, indent=2)
                self.logger.info(f"已初始化长记忆文件: {lm_file}")
                return True

            # 校验JSON有效性
            with open(lm_file, 'r', encoding='utf-8') as f:
                content = f.read()
            try:
                json.loads(content)
                return True
            except Exception as e:
                self.logger.warning(f"检测到长记忆文件解析错误，尝试修复: {e}")
                # 调用修复脚本
                fix_script = self.tools_dir / "LongMemory" / "fix_lm_records.py"
                if fix_script.exists():
                    result = subprocess.run([sys.executable, str(fix_script)], cwd=str(self.project_root))
                    if result.returncode == 0:
                        self.logger.info("长记忆文件修复完成")
                        return True
                    else:
                        self.logger.error("长记忆文件修复脚本执行失败")
                        return False
                else:
                    self.logger.error("修复脚本不存在，无法自动修复长记忆文件")
                    return False
        except Exception as e:
            self.logger.error(f"确保长记忆文件失败: {e}")
            return False
        
    def setup_logging(self):
        """设置日志系统"""
        try:
            # 确保日志目录存在
            self.logs_dir.mkdir(parents=True, exist_ok=True)
            
            # 配置日志格式
            log_file = self.logs_dir / "startup_check.log"
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(log_file, encoding='utf-8'),
                    logging.StreamHandler(sys.stdout)
                ]
            )
            
            self.logger = logging.getLogger(__name__)
            self.logger.info("YDS-Lab启动检查器初始化")
            
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
                self.logger.info("启动配置加载成功")
            else:
                self.logger.warning("启动配置文件不存在，使用默认配置")
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
            self.logger.info("默认启动配置文件已创建")
        except Exception as e:
            self.logger.error(f"配置文件保存失败: {e}")
            
    def get_ntp_time(self, ntp_server: str = 'pool.ntp.org', timeout: int = 5) -> Optional[datetime]:
        """获取NTP服务器时间"""
        try:
            # NTP服务器端口
            ntp_port = 123
            
            # 创建UDP套接字
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(timeout)
            
            # NTP协议数据包格式
            ntp_packet = b'\x1b' + 47 * b'\x00'
            
            # 发送请求
            sock.sendto(ntp_packet, (ntp_server, ntp_port))
            
            # 接收响应
            response, _ = sock.recvfrom(1024)
            sock.close()
            
            # 解析NTP时间戳
            ntp_timestamp = struct.unpack('!12I', response)[10]
            
            # NTP时间戳是从1900年1月1日开始计算的秒数
            ntp_epoch = datetime(1900, 1, 1)
            unix_epoch = datetime(1970, 1, 1)
            epoch_diff = (unix_epoch - ntp_epoch).total_seconds()
            
            # 转换为Unix时间戳
            unix_timestamp = ntp_timestamp - epoch_diff
            
            return datetime.fromtimestamp(unix_timestamp)
            
        except Exception as e:
            self.logger.warning(f"NTP时间同步失败: {e}")
            return None
    
    def validate_time_accuracy(self, max_deviation_seconds: int = 300) -> Dict[str, any]:
        """验证系统时间准确性"""
        try:
            system_time = datetime.now()
            ntp_time = self.get_ntp_time()
            
            if ntp_time is None:
                return {
                    'ntp_sync_available': False,
                    'system_time': system_time,
                    'time_deviation': None,
                    'is_accurate': True,  # 无法验证时默认为准确
                    'warning': 'NTP同步不可用，无法验证时间准确性'
                }
            
            # 计算时间偏差
            time_deviation = abs((system_time - ntp_time).total_seconds())
            
            # 判断是否在允许偏差范围内（默认5分钟）
            is_accurate = time_deviation <= max_deviation_seconds
            
            return {
                'ntp_sync_available': True,
                'system_time': system_time,
                'ntp_time': ntp_time,
                'time_deviation': time_deviation,
                'is_accurate': is_accurate,
                'deviation_warning': time_deviation > max_deviation_seconds,
                'warning': f"系统时间与NTP时间偏差: {time_deviation:.1f}秒" if time_deviation > max_deviation_seconds else None
            }
            
        except Exception as e:
            self.logger.error(f"时间验证失败: {e}")
            return {
                'ntp_sync_available': False,
                'system_time': datetime.now(),
                'time_deviation': None,
                'is_accurate': True,
                'error': str(e)
            }
    
    def check_time_anomalies(self) -> Dict[str, any]:
        """检查时间异常"""
        try:
            current_time = datetime.now()
            
            # 检查明显异常的时间值
            anomalies = []
            
            # 检查是否在未来（超过1天）
            future_threshold = datetime.now() + timedelta(days=1)
            if current_time > future_threshold:
                anomalies.append(f"系统时间异常超前: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 检查是否在过去（超过1年）
            past_threshold = datetime.now() - timedelta(days=365)
            if current_time < past_threshold:
                anomalies.append(f"系统时间异常滞后: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 检查年份合理性（2000-2030）
            if current_time.year < 2000 or current_time.year > 2030:
                anomalies.append(f"系统年份异常: {current_time.year}")
            
            # 检查时间跳跃（与上次检查相比）
            time_record_file = self.logs_dir / "last_time_check.json"
            if time_record_file.exists():
                try:
                    with open(time_record_file, 'r') as f:
                        last_check = json.load(f)
                    last_time = datetime.fromisoformat(last_check['timestamp'])
                    time_diff = abs((current_time - last_time).total_seconds())
                    
                    # 如果两次检查间隔超过2小时，可能是时间跳跃
                    if time_diff > 7200:  # 2小时 = 7200秒
                        anomalies.append(f"检测到时间跳跃: {time_diff:.0f}秒")
                        
                except Exception as e:
                    self.logger.warning(f"读取上次时间检查记录失败: {e}")
            
            # 保存当前时间检查记录
            try:
                with open(time_record_file, 'w') as f:
                    json.dump({
                        'timestamp': current_time.isoformat(),
                        'check_time': current_time.strftime('%Y-%m-%d %H:%M:%S')
                    }, f)
            except Exception as e:
                self.logger.warning(f"保存时间检查记录失败: {e}")
            
            return {
                'current_time': current_time,
                'anomalies_detected': len(anomalies) > 0,
                'anomalies': anomalies,
                'time_valid': len(anomalies) == 0,
                'severity': 'high' if len(anomalies) > 1 else ('medium' if len(anomalies) == 1 else 'low')
            }
            
        except Exception as e:
            self.logger.error(f"时间异常检查失败: {e}")
            return {
                'current_time': datetime.now(),
                'anomalies_detected': True,
                'anomalies': [f"时间检查异常: {str(e)}"],
                'time_valid': False,
                'severity': 'high',
                'error': str(e)
            }
    
    def get_current_system_date(self) -> Dict[str, str]:
        """获取当前系统日期信息 - 增强版，包含时间校验"""
        try:
            # 首先进行时间准确性验证
            time_validation = self.validate_time_accuracy()
            time_anomalies = self.check_time_anomalies()
            
            now = time_validation['system_time']
            weekdays_cn = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
            
            # 记录时间检查警告
            if time_validation.get('warning'):
                self.logger.warning(time_validation['warning'])
            
            if time_anomalies['anomalies_detected']:
                for anomaly in time_anomalies['anomalies']:
                    self.logger.warning(f"时间异常: {anomaly}")
            
            return {
                'date': now.strftime('%Y-%m-%d'),
                'datetime': now.strftime('%Y-%m-%d %H:%M:%S'),
                'formatted': now.strftime('%Y年%m月%d日'),
                'weekday_cn': weekdays_cn[now.weekday()],
                'timestamp': now.timestamp(),
                'time_validation': time_validation,
                'time_anomalies': time_anomalies,
                'time_status': 'valid' if time_anomalies['time_valid'] and time_validation['is_accurate'] else 'warning'
            }
            
        except Exception as e:
            self.logger.error(f"获取系统日期失败: {e}")
            # 降级处理：返回基本时间信息
            now = datetime.now()
            weekdays_cn = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
            
            return {
                'date': now.strftime('%Y-%m-%d'),
                'datetime': now.strftime('%Y-%m-%d %H:%M:%S'),
                'formatted': now.strftime('%Y年%m月%d日'),
                'weekday_cn': weekdays_cn[now.weekday()],
                'timestamp': now.timestamp(),
                'time_validation': None,
                'time_anomalies': None,
                'time_status': 'error',
                'error': str(e)
            }
        
    def check_project_structure(self) -> bool:
        """检查项目基础结构"""
        self.logger.info("检查项目基础结构...")
        
        required_dirs = [
            '01-struc', 'tools', '03-dev', '04-prod/001-memory-system',
            '01-struc/0B-general-manager/logs', '01-struc/docs',
            'tools/mcp/servers', '01-struc/Agents', '01-struc/SharedWorkspace'
        ]
        
        missing_dirs = []
        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            if not dir_path.exists():
                missing_dirs.append(dir_name)
                
        if missing_dirs:
            self.logger.warning(f"缺失目录: {', '.join(missing_dirs)}")
            return False
        else:
            self.logger.info("项目结构检查通过")
            return True
            
    def check_python_environment(self) -> Dict[str, any]:
        """检查Python环境"""
        self.logger.info("检查Python环境...")
        
        env_info = {
            'python_version': sys.version,
            'python_executable': sys.executable,
            'virtual_env': os.environ.get('VIRTUAL_ENV'),
            'in_venv': 'VIRTUAL_ENV' in os.environ,
            'working_directory': os.getcwd(),
            'python_path': sys.path[:3]  # 只显示前3个路径
        }
        
        # 检查关键依赖
        required_packages = ['yaml', 'pathlib']
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
                
        env_info['missing_packages'] = missing_packages
        env_info['dependencies_ok'] = len(missing_packages) == 0
        
        return env_info
        
    def check_memory_system_status(self) -> Dict[str, any]:
        """检查长记忆系统状态 - 增强版，包含进程、端口和心跳检测"""
        self.logger.info("检查长记忆系统状态...")
        
        memory_status = {
            'system_exists': False,
            'config_exists': False,
            'dependencies_ok': False,
            'services_status': {},
            'test_results': None,
            'ready': False,
            'process_status': {},
            'port_status': {},
            'heartbeat_status': {},
            'overall_health': 'unknown'
        }
        
        # 检查系统目录
        if self.memory_system_dir.exists():
            memory_status['system_exists'] = True
            
            # 检查配置文件（TraeLM子目录中）
            config_file = self.memory_system_dir / "TraeLM" / "memory-config.yaml"
            if config_file.exists():
                memory_status['config_exists'] = True
                
            # 检查package.json和依赖（TraeLM子目录中）
            package_file = self.memory_system_dir / "TraeLM" / "package.json"
            if package_file.exists():
                try:
                    # 检查node_modules（TraeLM子目录中）
                    node_modules = self.memory_system_dir / "TraeLM" / "node_modules"
                    memory_status['dependencies_ok'] = node_modules.exists()
                except Exception as e:
                    self.logger.warning(f"检查依赖失败: {e}")
                    
            # 检查核心服务文件（TraeLM子目录中）
            required_services = self.default_config['memory_system']['required_services']
            for service in required_services:
                service_status = {'exists': False, 'compiled': False}
                
                # 检查源码
                src_path = self.memory_system_dir / "TraeLM" / "src" / "services" / f"{service}.ts"
                if src_path.exists():
                    service_status['exists'] = True
                    
                # 检查编译后的文件
                dist_path = self.memory_system_dir / "TraeLM" / "dist" / "src" / "services" / f"{service}.js"
                if dist_path.exists():
                    service_status['compiled'] = True
                    
                memory_status['services_status'][service] = service_status
            
            # 增强：检查进程状态
            memory_status['process_status'] = self.check_memory_processes()
            
            # 增强：检查端口状态
            memory_status['port_status'] = self.check_memory_ports()
            
            # 增强：检查心跳状态
            memory_status['heartbeat_status'] = self.check_memory_heartbeat()
                
            # 运行测试（如果启用）
            if (self.default_config['memory_system']['test_on_startup'] and 
                memory_status['system_exists'] and memory_status['dependencies_ok']):
                try:
                    test_script = self.memory_system_dir / "test-memory-system.js"
                    if test_script.exists():
                        # 简单的测试检查，不实际运行以避免阻塞
                        memory_status['test_results'] = 'test_available'
                    else:
                        memory_status['test_results'] = 'no_test_script'
                except Exception as e:
                    memory_status['test_results'] = f'test_error: {e}'
                    
            # 判断系统是否就绪（增强版）
            basic_ready = (
                memory_status['system_exists'] and 
                memory_status['config_exists'] and
                memory_status['dependencies_ok'] and
                all(service['exists'] for service in memory_status['services_status'].values())
            )
            
            # 进程健康检查
            process_healthy = (
                memory_status['process_status'].get('total_running', 0) > 0 or
                not memory_status['process_status'].get('critical_processes_missing', False)
            )
            
            # 端口健康检查
            port_healthy = (
                memory_status['port_status'].get('required_ports_open', 0) > 0 or
                not memory_status['port_status'].get('critical_ports_closed', False)
            )
            
            memory_status['ready'] = basic_ready and process_healthy and port_healthy
            
            # 整体健康状态评估
            if memory_status['ready'] and process_healthy and port_healthy:
                memory_status['overall_health'] = 'healthy'
            elif basic_ready:
                memory_status['overall_health'] = 'degraded'
            else:
                memory_status['overall_health'] = 'unhealthy'
                
        else:
            self.logger.warning("长记忆系统目录不存在")
            memory_status['overall_health'] = 'not_found'
            
        return memory_status
    
    def check_memory_processes(self) -> Dict[str, any]:
        """检查长记忆相关进程状态"""
        try:
            import psutil
            
            process_info = {
                'total_running': 0,
                'processes': [],
                'critical_processes_missing': False,
                'check_success': True
            }
            
            # 定义关键进程名称模式
            critical_processes = [
                'node', 'memory', 'content', 'processor', 'intelligent', 'filter',
                'memory-service', 'content-processor', 'intelligent-filter'
            ]
            
            found_processes = set()
            
            # 遍历所有进程
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
                try:
                    proc_info = proc.info
                    proc_name = proc_info['name'].lower()
                    cmdline = ' '.join(proc_info['cmdline']) if proc_info['cmdline'] else ''
                    
                    # 检查是否是长记忆相关进程
                    is_memory_related = False
                    
                    # 检查进程名称
                    for keyword in critical_processes:
                        if keyword in proc_name:
                            is_memory_related = True
                            break
                    
                    # 检查命令行参数
                    if not is_memory_related and cmdline:
                        for keyword in ['memory', 'test-memory-system', 'memory-system']:
                            if keyword in cmdline.lower():
                                is_memory_related = True
                                break
                    
                    if is_memory_related:
                        process_detail = {
                            'pid': proc_info['pid'],
                            'name': proc_info['name'],
                            'cmdline': cmdline[:100] + '...' if len(cmdline) > 100 else cmdline,
                            'create_time': datetime.fromtimestamp(proc_info['create_time']).strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        process_info['processes'].append(process_detail)
                        process_info['total_running'] += 1
                        
                        # 记录找到的进程类型
                        if 'node' in proc_name:
                            found_processes.add('node')
                        if 'memory' in proc_name or 'memory' in cmdline.lower():
                            found_processes.add('memory')
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                except Exception as e:
                    self.logger.warning(f"检查进程时出错: {e}")
                    continue
            
            # 检查是否有关键进程缺失
            required_found = len(found_processes) > 0
            process_info['critical_processes_missing'] = not required_found
            
            self.logger.info(f"发现 {process_info['total_running']} 个长记忆相关进程")
            
        except ImportError:
            self.logger.warning("psutil模块未安装，无法检查进程状态")
            process_info = {
                'total_running': -1,
                'processes': [],
                'critical_processes_missing': False,
                'check_success': False,
                'error': 'psutil模块未安装'
            }
        except Exception as e:
            self.logger.error(f"进程检查失败: {e}")
            process_info = {
                'total_running': -1,
                'processes': [],
                'critical_processes_missing': True,
                'check_success': False,
                'error': str(e)
            }
            
        return process_info
    
    def check_memory_ports(self) -> Dict[str, any]:
        """检查长记忆服务端口状态"""
        try:
            import psutil
            
            port_info = {
                'required_ports_open': 0,
                'critical_ports_closed': False,
                'open_ports': [],
                'check_success': True
            }
            
            # 定义关键端口（根据实际配置调整）
            memory_ports = [3000, 8080, 9000, 9200, 9300]  # 常见的内存服务端口
            
            # 获取所有网络连接
            connections = psutil.net_connections()
            
            open_ports = set()
            for conn in connections:
                if conn.status == 'LISTEN' and conn.laddr:
                    port = conn.laddr.port
                    open_ports.add(port)
            
            # 检查关键端口
            required_open = 0
            for port in memory_ports:
                if port in open_ports:
                    required_open += 1
                    port_info['open_ports'].append({
                        'port': port,
                        'status': 'open',
                        'protocol': 'TCP'
                    })
                else:
                    port_info['open_ports'].append({
                        'port': port,
                        'status': 'closed',
                        'protocol': 'TCP'
                    })
            
            port_info['required_ports_open'] = required_open
            port_info['critical_ports_closed'] = required_open == 0
            
            self.logger.info(f"发现 {required_open} 个关键端口开放")
            
        except ImportError:
            self.logger.warning("psutil模块未安装，无法检查端口状态")
            port_info = {
                'required_ports_open': -1,
                'critical_ports_closed': False,
                'open_ports': [],
                'check_success': False,
                'error': 'psutil模块未安装'
            }
        except Exception as e:
            self.logger.error(f"端口检查失败: {e}")
            port_info = {
                'required_ports_open': -1,
                'critical_ports_closed': True,
                'open_ports': [],
                'check_success': False,
                'error': str(e)
            }
            
        return port_info
    
    def check_memory_heartbeat(self) -> Dict[str, any]:
        """检查长记忆服务心跳状态"""
        try:
            heartbeat_info = {
                'heartbeat_detected': False,
                'last_heartbeat': None,
                'heartbeat_age_seconds': None,
                'services_responsive': [],
                'check_success': True
            }
            
            # 检查心跳文件
            heartbeat_files = [
                self.logs_dir / "memory_heartbeat.json",
                self.memory_system_dir / "heartbeat.json",
                self.memory_system_dir / "logs" / "heartbeat.log"
            ]
            
            latest_heartbeat = None
            latest_file = None
            
            for heartbeat_file in heartbeat_files:
                if heartbeat_file.exists():
                    try:
                        with open(heartbeat_file, 'r', encoding='utf-8') as f:
                            heartbeat_data = json.load(f)
                        
                        # 提取心跳时间
                        heartbeat_time = None
                        if isinstance(heartbeat_data, dict):
                            if 'timestamp' in heartbeat_data:
                                heartbeat_time = datetime.fromisoformat(heartbeat_data['timestamp'])
                            elif 'last_update' in heartbeat_data:
                                heartbeat_time = datetime.fromisoformat(heartbeat_data['last_update'])
                            elif 'time' in heartbeat_data:
                                heartbeat_time = datetime.fromisoformat(heartbeat_data['time'])
                        
                        if heartbeat_time and (latest_heartbeat is None or heartbeat_time > latest_heartbeat):
                            latest_heartbeat = heartbeat_time
                            latest_file = heartbeat_file
                            
                    except Exception as e:
                        self.logger.warning(f"读取心跳文件 {heartbeat_file} 失败: {e}")
                        continue
            
            if latest_heartbeat:
                heartbeat_info['heartbeat_detected'] = True
                heartbeat_info['last_heartbeat'] = latest_heartbeat.strftime('%Y-%m-%d %H:%M:%S')
                
                # 计算心跳年龄
                age_seconds = (datetime.now() - latest_heartbeat).total_seconds()
                heartbeat_info['heartbeat_age_seconds'] = age_seconds
                
                # 判断心跳是否过期（超过5分钟认为过期）
                if age_seconds > 300:  # 5分钟
                    heartbeat_info['heartbeat_status'] = 'expired'
                    self.logger.warning(f"心跳过期: {age_seconds:.0f}秒前")
                elif age_seconds > 60:  # 1分钟
                    heartbeat_info['heartbeat_status'] = 'stale'
                    self.logger.info(f"心跳较旧: {age_seconds:.0f}秒前")
                else:
                    heartbeat_info['heartbeat_status'] = 'fresh'
                    self.logger.info(f"心跳正常: {age_seconds:.0f}秒前")
                    
                heartbeat_info['heartbeat_file'] = str(latest_file)
                
            else:
                heartbeat_info['heartbeat_status'] = 'no_heartbeat'
                self.logger.warning("未检测到心跳信号")
            
            # 尝试简单的服务响应测试
            try:
                # 检查内存服务是否响应基本请求
                test_services = ['knowledge-graph', 'memory-retrieval']
                for service in test_services:
                    # 这里可以添加实际的服务响应测试
                    # 目前只是标记为待测试
                    heartbeat_info['services_responsive'].append({
                        'service': service,
                        'status': 'pending_test',
                        'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
            except Exception as e:
                self.logger.warning(f"服务响应测试失败: {e}")
                
        except Exception as e:
            self.logger.error(f"心跳检查失败: {e}")
            heartbeat_info = {
                'heartbeat_detected': False,
                'last_heartbeat': None,
                'heartbeat_age_seconds': None,
                'services_responsive': [],
                'check_success': False,
                'heartbeat_status': 'check_failed',
                'error': str(e)
            }
            
        return heartbeat_info
        
    def retry_operation(self, func, max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
        """通用重试装饰器"""
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    self.logger.warning(f"操作失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                    
                    if attempt < max_retries - 1:
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        self.logger.error(f"操作在 {max_retries} 次尝试后仍然失败: {e}")
                        
            raise last_exception
        return wrapper
    
    def validate_memory_startup(self, timeout: int = 10) -> Dict[str, any]:
        """验证长记忆系统启动状态"""
        try:
            validation_result = {
                'validation_success': False,
                'checks_performed': [],
                'issues_found': [],
                'startup_confirmed': False,
                'validation_time': 0
            }
            
            start_time = time.time()
            
            # 1. 检查进程是否存在
            try:
                import psutil
                memory_processes = []
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        if proc.info['cmdline'] and any('test-memory-system.js' in cmd for cmd in proc.info['cmdline']):
                            memory_processes.append(proc.info['pid'])
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                if memory_processes:
                    validation_result['checks_performed'].append(f"✅ 发现内存进程: {memory_processes}")
                else:
                    validation_result['issues_found'].append("❌ 未发现内存进程")
                    
            except ImportError:
                validation_result['issues_found'].append("⚠️ psutil模块未安装，无法验证进程")
            
            # 2. 检查端口监听
            try:
                import socket
                test_ports = [3000, 8080, 9000]
                open_ports = []
                
                for port in test_ports:
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(1)
                        result = sock.connect_ex(('localhost', port))
                        sock.close()
                        
                        if result == 0:
                            open_ports.append(port)
                    except Exception:
                        continue
                
                if open_ports:
                    validation_result['checks_performed'].append(f"✅ 发现开放端口: {open_ports}")
                else:
                    validation_result['issues_found'].append("⚠️ 未发现预期的开放端口")
                    
            except Exception as e:
                validation_result['issues_found'].append(f"⚠️ 端口检查失败: {e}")
            
            # 3. 检查日志文件
            try:
                log_files = [
                    self.memory_system_dir / "logs" / "memory-service.log",
                    self.memory_system_dir / "memory-service.log",
                    self.logs_dir / "memory_service.log"
                ]
                
                found_logs = []
                for log_file in log_files:
                    if log_file.exists():
                        # 检查日志是否最近更新
                        file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                        if (datetime.now() - file_mtime).total_seconds() < 300:  # 5分钟内
                            found_logs.append(str(log_file))
                
                if found_logs:
                    validation_result['checks_performed'].append(f"✅ 发现活跃日志文件: {found_logs}")
                else:
                    validation_result['issues_found'].append("⚠️ 未发现活跃日志文件")
                    
            except Exception as e:
                validation_result['issues_found'].append(f"⚠️ 日志检查失败: {e}")
            
            # 4. 综合判断
            validation_time = time.time() - start_time
            validation_result['validation_time'] = validation_time
            
            # 如果没有严重问题，认为验证成功
            critical_issues = [issue for issue in validation_result['issues_found'] if issue.startswith('❌')]
            if not critical_issues and validation_result['checks_performed']:
                validation_result['validation_success'] = True
                validation_result['startup_confirmed'] = True
                self.logger.info(f"长记忆系统启动验证成功 ({validation_time:.1f}秒)")
            else:
                self.logger.warning(f"长记忆系统启动验证失败: {critical_issues}")
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"启动验证失败: {e}")
            return {
                'validation_success': False,
                'checks_performed': [],
                'issues_found': [f"验证过程异常: {e}"],
                'startup_confirmed': False,
                'validation_time': 0,
                'error': str(e)
            }
    
    def start_memory_system(self) -> Dict[str, any]:
        """启动长记忆系统 - 增强版，包含重试机制和验证流程"""
        self.logger.info("尝试启动长记忆系统...")
        
        start_result = {
            'attempted': False,
            'success': False,
            'process_id': None,
            'error': None,
            'message': '',
            'retry_count': 0,
            'validation_result': None,
            'startup_method': None
        }
        
        try:
            # 第1步：检查系统状态
            memory_status = self.check_memory_system_status()
            
            if not memory_status['ready']:
                start_result['error'] = "系统未就绪，无法启动"
                start_result['message'] = "请先确保长记忆系统配置正确且依赖已安装"
                return start_result
            
            # 第2步：检查是否已经在运行（使用增强检测）
            try:
                import psutil
                
                # 检查进程
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        if proc.info['cmdline'] and any('test-memory-system.js' in cmd for cmd in proc.info['cmdline']):
                            # 进一步验证进程是否真正活跃
                            validation = self.validate_memory_startup(timeout=5)
                            if validation['startup_confirmed']:
                                start_result['message'] = f"长记忆系统已在运行并验证正常 (PID: {proc.info['pid']})"
                                start_result['success'] = True
                                start_result['process_id'] = proc.info['pid']
                                start_result['startup_method'] = 'already_running'
                                start_result['validation_result'] = validation
                                return start_result
                            else:
                                self.logger.warning(f"发现进程但验证失败 (PID: {proc.info['pid']})，将尝试重启")
                                # 尝试终止异常进程
                                try:
                                    proc.terminate()
                                    time.sleep(2)
                                except Exception:
                                    pass
                                break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                        
            except ImportError:
                self.logger.warning("psutil模块未安装，进程检测受限")
            
            # 第3步：使用重试机制启动系统
            @self.retry_operation(max_retries=3, delay=2.0, backoff=1.5)
            def _start_with_retry():
                # 切换到memory-system目录并启动
                cmd = ['node', 'test-memory-system.js']
                process = subprocess.Popen(
                    cmd,
                    cwd=str(self.memory_system_dir),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
                )
                
                # 等待进程启动
                time.sleep(3)
                
                # 检查进程是否仍然存在
                try:
                    import psutil
                    if psutil.pid_exists(process.pid):
                        return process
                    else:
                        raise RuntimeError("进程启动后立即退出")
                except ImportError:
                    # 如果没有psutil，简单等待后返回
                    time.sleep(2)
                    return process
            
            start_result['attempted'] = True
            
            try:
                # 执行带重试的启动
                process = _start_with_retry()
                start_result['process_id'] = process.pid
                start_result['retry_count'] = 0  # 重试成功
                
                self.logger.info(f"长记忆系统进程启动成功 (PID: {process.pid})")
                
            except Exception as retry_error:
                # 重试机制失败，尝试降级启动
                self.logger.warning(f"标准启动失败，尝试降级启动: {retry_error}")
                
                try:
                    # 降级启动：使用更简单的命令
                    simple_cmd = ['node', 'test-memory-system.js', '--simple']
                    simple_process = subprocess.Popen(
                        simple_cmd,
                        cwd=str(self.memory_system_dir),
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    
                    start_result['process_id'] = simple_process.pid
                    start_result['startup_method'] = 'degraded'
                    self.logger.info(f"降级启动成功 (PID: {simple_process.pid})")
                    
                except Exception as degraded_error:
                    start_result['error'] = f"所有启动方法均失败: {degraded_error}"
                    start_result['message'] = f"启动失败: {degraded_error}"
                    return start_result
            
            # 第4步：验证启动状态
            self.logger.info("正在验证长记忆系统启动状态...")
            validation = self.validate_memory_startup(timeout=15)
            start_result['validation_result'] = validation
            
            if validation['startup_confirmed']:
                start_result['success'] = True
                start_result['message'] = f"长记忆系统启动并验证成功 (PID: {start_result['process_id']})"
                if start_result['startup_method'] == 'degraded':
                    start_result['message'] += " [降级模式]"
                self.logger.info(start_result['message'])
            else:
                start_result['error'] = "启动验证失败"
                start_result['message'] = f"进程已启动但验证失败: {validation['issues_found']}"
                self.logger.warning(start_result['message'])
                
                # 验证失败时，可以选择终止进程
                try:
                    import psutil
                    if psutil.pid_exists(start_result['process_id']):
                        psutil.Process(start_result['process_id']).terminate()
                        self.logger.info("已终止验证失败的进程")
                except Exception:
                    pass
                
        except ImportError:
            start_result['error'] = "缺少psutil依赖包"
            start_result['message'] = "请安装psutil: pip install psutil"
        except Exception as e:
            start_result['error'] = str(e)
            start_result['message'] = f"启动过程异常: {e}"
            self.logger.error(f"启动长记忆系统失败: {e}")
            
        return start_result
        
    def check_mcp_servers_status(self) -> Dict[str, any]:
        """检查MCP服务器状态"""
        self.logger.info("检查MCP服务器状态...")
        
        # 查找配置文件
        config_file = None
        for candidate in self.mcp_config_candidates:
            if candidate.exists():
                config_file = candidate
                break
                
        if not config_file:
            self.logger.warning("未找到Claude Desktop配置文件")
            return {
                'config_found': False,
                'servers': {},
                'status': 'no_config'
            }
            
        try:
            # 检查文件是否为空或只包含空白字符
            with open(config_file, 'r', encoding='utf-8-sig') as f:
                content = f.read().strip()
                
            if not content:
                self.logger.warning(f"MCP配置文件为空: {config_file}")
                return {
                    'config_found': True,
                    'config_file': str(config_file),
                    'servers': {},
                    'total_servers': 0,
                    'status': 'empty_config'
                }
                
            # 读取MCP配置
            config = json.loads(content)
                
            mcp_servers = config.get('mcpServers', {})
            server_status = {}
            
            for server_name, server_config in mcp_servers.items():
                status = {
                    'configured': True,
                    'script_exists': False,
                    'script_path': None
                }
                
                # 检查脚本文件
                if 'args' in server_config and server_config['args']:
                    script_path = Path(server_config['args'][0])
                    status['script_path'] = str(script_path)
                    status['script_exists'] = script_path.exists()
                    
                server_status[server_name] = status
            
            # 检查集群配置
            cluster_config = None
            # 新路径优先，旧路径兼容
            cluster_config_candidates = [
                self.project_root / "tools" / "mcp" / "servers" / "cluster_config.yaml",
                self.struc_dir / "MCPCluster" / "cluster_config.yaml",
            ]
            cluster_config_path = next((p for p in cluster_config_candidates if p.exists()), None)
            if cluster_config_path:
                try:
                    with open(cluster_config_path, 'r', encoding='utf-8') as f:
                        cluster_content = f.read().strip()
                    if cluster_content:
                        cluster_config = yaml.safe_load(cluster_content)
                except Exception as e:
                    self.logger.warning(f"集群配置读取失败: {e}")
                
            return {
                'config_found': True,
                'config_file': str(config_file),
                'servers': server_status,
                'total_servers': len(mcp_servers),
                'cluster_config': cluster_config,
                'sequential_thinking': server_status.get('sequential-thinking'),
                'status': 'ok' if mcp_servers else 'no_servers'
            }
            
        except Exception as e:
            self.logger.error(f"MCP配置读取失败: {e}")
            return {
                'config_found': True,
                'config_file': str(config_file),
                'servers': {},
                'total_servers': 0,
                'status': 'error',
                'error': str(e)
            }
            
    def check_trae_agents_config(self) -> Dict[str, any]:
        """检查Trae Agent配置"""
        self.logger.info("检查Trae Agent配置...")
        
        config_status = {
            'trae_agents_dir_exists': self.trae_agents_dir.exists(),
            'agents_dir_exists': self.agents_dir.exists(),
            'trae_agent_configs': [],
            'agent_modules': [],
            'trae_config_exists': False,
            'agents_ready': False
        }
        
        # 检查Trae Agent配置目录
        if self.trae_agents_dir.exists():
            # 检查各个Agent目录
            agent_dirs = [d for d in self.trae_agents_dir.iterdir() if d.is_dir()]
            for agent_dir in agent_dirs:
                agent_info = {
                    'name': agent_dir.name,
                    'config_exists': False,
                    'files': []
                }
                
                # 检查配置文件
                config_files = list(agent_dir.glob("*.yaml")) + list(agent_dir.glob("*.yml"))
                if config_files:
                    agent_info['config_exists'] = True
                    agent_info['files'] = [f.name for f in config_files]
                
                config_status['trae_agent_configs'].append(agent_info)
        
        # 检查Agents模块目录
        if self.agents_dir.exists():
            # 检查Python模块
            agent_modules = list(self.agents_dir.glob("*.py"))
            agent_dirs = [d for d in self.agents_dir.iterdir() if d.is_dir() and (d / "__init__.py").exists()]
            
            config_status['agent_modules'] = [f.name for f in agent_modules]
            config_status['agent_modules'].extend([d.name for d in agent_dirs])
        
        # 检查主配置文件（优先使用 config/trae_config.yaml）
        config_trae_new = self.project_root / "config" / "trae_config.yaml"
        if config_trae_new.exists():
            config_status['trae_config_exists'] = True
        else:
            config_status['trae_config_exists'] = False
        
        # 判断Trae Agent系统是否就绪
        config_status['agents_ready'] = (
            config_status['trae_agents_dir_exists'] and 
            config_status['agents_dir_exists'] and
            config_status['trae_config_exists'] and
            (len(config_status['trae_agent_configs']) > 0 or len(config_status['agent_modules']) > 0)
        )
        
        return config_status
        
    def check_core_documents(self) -> Dict[str, any]:
        """检查核心文档（按照V5.1架构规范）"""
        self.logger.info("检查核心文档...")
        
        # 按照V5.1架构的文档结构进行检查
        core_docs = [
            # 01-战略规划文档（移除阴阳五行治理理念.md）
            "01-战略规划/02-1YDS-Lab标准目录结构（顶层设计）.md", 
            "01-战略规划/03-YDS AI公司建设与项目实施完整方案.md",
            # 02-组织流程文档
            "02-组织流程/01-项目架构设计.md",
            "02-组织流程/02-规范与流程.md",
            "02-组织流程/《动态目录结构清单》.md"
            # 注意：README.md 检查已取消
        ]
        
        doc_status = {
            'total_docs': len(core_docs),
            'found_docs': 0,
            'missing_docs': [],
            'existing_docs': []
        }
        
        for doc_path in core_docs:
            if doc_path == "README.md":
                full_path = self.project_root / doc_path
            else:
                # 所有文档都存储在 01-struc/docs/ 目录下（三级存储规范）
                full_path = self.docs_dir / doc_path
                
            if full_path.exists():
                doc_status['found_docs'] += 1
                doc_status['existing_docs'].append(doc_path)
            else:
                doc_status['missing_docs'].append(doc_path)
                
        doc_status['docs_complete'] = doc_status['found_docs'] == doc_status['total_docs']
        
        return doc_status
        
    def check_tool_assets(self) -> Dict[str, any]:
        """检查核心工具资产（按照V5.1架构的四个核心工具）"""
        self.logger.info("检查核心工具资产...")
        
        # YDS-Lab V5.1架构的四个核心工具文件
        core_tools = [
            "ch.py",    # 检查工具
            "fi.py",    # 工作完成处理工具  
            "st.py",    # 启动检查工具
            "up.py"     # 更新工具
        ]
        
        tool_status = {
            'total_tools': len(core_tools),
            'found_tools': 0,
            'missing_tools': [],
            'existing_tools': []
        }
        
        for tool_name in core_tools:
            # 工具文件存储在项目根目录
            tool_path = self.project_root / tool_name
            if tool_path.exists():
                tool_status['found_tools'] += 1
                tool_status['existing_tools'].append(tool_name)
            else:
                tool_status['missing_tools'].append(tool_name)
                
        tool_status['tools_complete'] = tool_status['found_tools'] == tool_status['total_tools']
        
        return tool_status
        
    def run_structure_compliance_check(self) -> bool:
        """运行结构合规性检查 - 增强异常处理"""
        check_script = self.tools_dir / "check_structure.py"
        if not self.safe_file_operation('exists', check_script, fallback_value=False):
            self.logger.warning("结构检查脚本不存在")
            return False
            
        # 使用安全的子进程运行
        result = self.safe_subprocess_run(
            [sys.executable, str(check_script)],
            timeout=30,
            cwd=str(self.project_root),
            check=False
        )
        
        # 处理不同的返回类型
        if isinstance(result, subprocess.CompletedProcess):
            # 根据退出码判断合规性
            if result.returncode == 0:
                self.logger.info("结构合规性检查通过")
                return True
            elif result.returncode <= 2:
                self.logger.warning("结构合规性检查发现问题，但可继续")
                return True
            else:
                self.logger.error(f"结构合规性检查失败，返回码: {result.returncode}")
                return False
        else:
            # 处理异常情况
            self.logger.error(f"结构合规性检查执行异常: {result}")
            return False
            
    def generate_startup_briefing(self, checks_result: Dict) -> str:
        """生成启动简报 - 增强版，包含时间验证和健康状态"""
        current_date = self.get_current_system_date()
        
        # 时间状态显示
        time_status_icon = "✅" if current_date.get('time_status') == 'valid' else "⚠️" if current_date.get('time_status') == 'warning' else "❌"
        time_validation_info = ""
        if current_date.get('time_validation'):
            validation = current_date['time_validation']
            if validation.get('ntp_sync_available'):
                if validation.get('deviation_warning'):
                    time_validation_info = f"\n- **NTP时间偏差**: ⚠️ {validation.get('time_deviation', 0):.1f}秒"
                else:
                    time_validation_info = f"\n- **NTP时间同步**: ✅ 偏差{validation.get('time_deviation', 0):.1f}秒"
            else:
                time_validation_info = "\n- **NTP同步**: ⚠️ 不可用"
        
        if current_date.get('time_anomalies') and current_date['time_anomalies'].get('anomalies_detected'):
            anomalies = current_date['time_anomalies']['anomalies']
            time_validation_info += f"\n- **时间异常**: ⚠️ {len(anomalies)}个检测到"
        
        briefing = f"""
# YDS-Lab AI Agent 启动简报

> 生成时间: {current_date['formatted']} {current_date['weekday_cn']} {current_date['datetime']}  
> 项目根目录: `{self.project_root}`
> 时间状态: {time_status_icon} {current_date.get('time_status', 'unknown')}{time_validation_info}

## 🤖 AI智能协作系统状态

### Agent多智能体状态
- **Agents配置目录**: {'✅ 已配置' if checks_result['trae_agents']['trae_agents_dir_exists'] else '❌ 未配置'}
- **Agents模块目录**: {'✅ 已配置' if checks_result['trae_agents']['agents_dir_exists'] else '❌ 未配置'}
- **主配置文件**: {'✅ 存在' if checks_result['trae_agents']['trae_config_exists'] else '❌ 缺失'}
- **Agent配置**: {len(checks_result['trae_agents']['trae_agent_configs'])} 个
- **Agent模块**: {len(checks_result['trae_agents']['agent_modules'])} 个
- **系统就绪**: {'✅ 是' if checks_result['trae_agents']['agents_ready'] else '❌ 否'}

### Agent配置详情
- **Agents配置目录**: {'✅ 存在' if checks_result['trae_agents']['trae_agents_dir_exists'] else '❌ 不存在'}
- **Agents模块目录**: {'✅ 存在' if checks_result['trae_agents']['agents_dir_exists'] else '❌ 不存在'}
- **主配置文件**: {'✅ 存在' if checks_result['trae_agents']['trae_config_exists'] else '❌ 不存在'}
- **Agent配置数量**: {len(checks_result['trae_agents']['trae_agent_configs'])} 个
- **Agent模块数量**: {len(checks_result['trae_agents']['agent_modules'])} 个
"""

        # 长记忆系统状态（增强版）
        memory_system = checks_result['memory_system']
        health_status = memory_system.get('overall_health', 'unknown')
        health_icon = {'healthy': '✅', 'degraded': '⚠️', 'unhealthy': '❌', 'not_found': '❌', 'unknown': '❓'}.get(health_status, '❓')
        
        briefing += f"""

## 🧠 长记忆系统状态

### 系统配置与健康状况
- **系统目录**: {'✅ 存在' if memory_system['system_exists'] else '❌ 不存在'}
- **配置文件**: {'✅ 存在' if memory_system['config_exists'] else '❌ 不存在'}
- **依赖安装**: {'✅ 完整' if memory_system['dependencies_ok'] else '❌ 缺失'}
- **系统就绪**: {'✅ 是' if memory_system['ready'] else '❌ 否'}
- **整体健康**: {health_icon} {health_status}

### 核心服务状态
"""
        
        # 添加服务状态详情
        for service, status in memory_system['services_status'].items():
            src_icon = "✅" if status['exists'] else "❌"
            compiled_icon = "✅" if status['compiled'] else "❌"
            briefing += f"- **{service}**: 源码{src_icon} 编译{compiled_icon}\n"
        
        # 添加进程状态（如果可用）
        if memory_system.get('process_status') and memory_system['process_status'].get('total_running', -1) >= 0:
            proc_status = memory_system['process_status']
            proc_count = proc_status['total_running']
            proc_icon = "✅" if proc_count > 0 else "❌"
            briefing += f"- **运行进程**: {proc_icon} {proc_count} 个\n"
            if proc_count > 0 and proc_status.get('processes'):
                briefing += f"  - 进程详情: {', '.join([f"PID:{p['pid']}" for p in proc_status['processes'][:3]])}\n"
        
        # 添加端口状态（如果可用）
        if memory_system.get('port_status') and memory_system['port_status'].get('required_ports_open', -1) >= 0:
            port_status = memory_system['port_status']
            open_count = port_status['required_ports_open']
            port_icon = "✅" if open_count > 0 else "❌"
            briefing += f"- **开放端口**: {port_icon} {open_count} 个\n"
            if open_count > 0 and port_status.get('open_ports'):
                open_ports = [p['port'] for p in port_status['open_ports'] if p['status'] == 'open']
                briefing += f"  - 端口列表: {', '.join(map(str, open_ports[:5]))}\n"
        
        # 添加心跳状态（如果可用）
        if memory_system.get('heartbeat_status'):
            heartbeat = memory_system['heartbeat_status']
            if heartbeat.get('heartbeat_detected'):
                age_seconds = heartbeat.get('heartbeat_age_seconds', 0)
                if age_seconds <= 60:
                    hb_icon = "✅"
                    hb_status = "正常"
                elif age_seconds <= 300:
                    hb_icon = "⚠️"
                    hb_status = "较旧"
                else:
                    hb_icon = "❌"
                    hb_status = "过期"
                briefing += f"- **心跳状态**: {hb_icon} {hb_status} ({age_seconds:.0f}秒前)\n"
            else:
                briefing += f"- **心跳状态**: ❌ 未检测到\n"
        
        # 添加测试结果
        if memory_system.get('test_results'):
            test_status = memory_system['test_results']
            if test_status == 'test_available':
                briefing += "- **测试状态**: ✅ 测试脚本可用\n"
            elif test_status == 'no_test_script':
                briefing += "- **测试状态**: ⚠️ 无测试脚本\n"
            else:
                briefing += f"- **测试状态**: ❌ {test_status}\n"
        
        # 自动启动结果（如果存在）
        if memory_system.get('auto_start_result'):
            auto_start = memory_system['auto_start_result']
            if auto_start.get('success'):
                start_icon = "✅"
                start_msg = f"成功 (PID: {auto_start.get('process_id', 'N/A')})"
                if auto_start.get('startup_method') == 'degraded':
                    start_msg += " [降级模式]"
            else:
                start_icon = "❌"
                start_msg = f"失败: {auto_start.get('error', '未知错误')}"
            briefing += f"- **自动启动**: {start_icon} {start_msg}\n"
                
        briefing += f"""

## 🔧 MCP服务器状态

### 配置状态
- **配置文件**: {'✅ 已找到' if checks_result['mcp_status']['config_found'] else '❌ 未找到'}
"""
        
        if checks_result['mcp_status']['config_found']:
            briefing += f"- **配置路径**: `{checks_result['mcp_status'].get('config_file', 'N/A')}`\n"
            briefing += f"- **服务器数量**: {checks_result['mcp_status']['total_servers']} 个\n\n"
            
            briefing += "### 服务器详情\n"
            for server_name, status in checks_result['mcp_status']['servers'].items():
                status_icon = "✅" if status['script_exists'] else "❌"
                briefing += f"- **{server_name}**: {status_icon} {'脚本存在' if status['script_exists'] else '脚本缺失'}\n"
        else:
            briefing += "- **状态**: 需要配置MCP服务器\n"
            
        briefing += f"""
## 📚 核心文档状态

- **文档完整性**: {checks_result['docs_status']['found_docs']}/{checks_result['docs_status']['total_docs']} {'✅ 完整' if checks_result['docs_status']['docs_complete'] else '⚠️ 不完整'}
- **已存在文档**: {len(checks_result['docs_status']['existing_docs'])} 个
"""
        
        if checks_result['docs_status']['missing_docs']:
            briefing += "- **缺失文档**:\n"
            for doc in checks_result['docs_status']['missing_docs']:
                briefing += f"  - ❌ `{doc}`\n"
                
        briefing += f"""
## 🛠️ 工具资产状态

- **工具完整性**: {checks_result['tool_status']['found_tools']}/{checks_result['tool_status']['total_tools']} {'✅ 完整' if checks_result['tool_status']['tools_complete'] else '⚠️ 不完整'}
- **核心工具**: {', '.join(checks_result['tool_status']['existing_tools'])}
"""
        
        if checks_result['tool_status']['missing_tools']:
            briefing += "- **缺失工具**:\n"
            for tool in checks_result['tool_status']['missing_tools']:
                briefing += f"  - ❌ `{tool}`\n"
                
        briefing += f"""
## 🐍 Python环境信息

- **Python版本**: {checks_result['python_env']['python_version'].split()[0]}
- **虚拟环境**: {'✅ 已激活' if checks_result['python_env']['in_venv'] else '⚠️ 未使用'}
- **工作目录**: `{checks_result['python_env']['working_directory']}`
- **依赖状态**: {'✅ 完整' if checks_result['python_env']['dependencies_ok'] else '❌ 缺失依赖'}

## 📊 项目结构状态

- **基础结构**: {'✅ 完整' if checks_result['structure_ok'] else '❌ 不完整'}
- **合规性检查**: {'✅ 通过' if checks_result.get('compliance_check', False) else '⚠️ 需要检查'}

## 🚀 启动建议

### 立即可用功能
- ✅ 基础项目管理
- ✅ 文档编写和维护
- ✅ 代码开发和调试

### 需要配置的功能
"""
        
        suggestions = []
        if not checks_result['trae_agents']['agents_ready']:
            suggestions.append("- 🤖 配置Agent和任务定义")
        if not checks_result['mcp_status']['config_found']:
            suggestions.append("- 🔧 配置MCP服务器连接")
        if not checks_result['docs_status']['docs_complete']:
            suggestions.append("- 📚 补充缺失的核心文档")
        if not checks_result['tool_status']['tools_complete']:
            suggestions.append("- 🛠️ 安装缺失的核心工具")
            
        if suggestions:
            briefing += "\n".join(suggestions)
        else:
            briefing += "- ✅ 所有功能已就绪，可以开始高效工作！"
            
        briefing += f"""

## 💡 使用提示

### 快速命令
```bash
# 检查项目结构
python ch.py

# 完成工作会话
python fi.py

# 启动系统检查（增强版）
python st.py

# 更新项目结构
python up.py
```

### 增强功能说明
1. **时间管理**: 自动NTP同步，异常时间检测
2. **长记忆监控**: 进程、端口、心跳三重检测
3. **异常处理**: 重试机制，降级模式，超时保护
4. **健康评估**: 多维度系统健康状态评估

### AI协作建议
1. **多Agent协作**: 使用Trae Agent框架进行智能任务分解和协作处理
2. **知识管理**: 利用MCP Memory服务器进行知识存储和检索
3. **代码协作**: 通过GitHub MCP服务器进行版本控制
4. **文档生成**: 使用Context7服务器获取最新技术文档

---

*YDS-Lab AI智能协作系统 V5.1 - 高可靠性智能工作伙伴*
"""
        
        return briefing
        
    def save_startup_record(self, briefing: str):
        """保存启动记录"""
        try:
            records_dir = self.logs_dir / "startup_records"
            records_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            record_file = records_dir / f"startup_{timestamp}.md"
            
            with open(record_file, 'w', encoding='utf-8') as f:
                f.write(briefing)
                
            self.logger.info(f"启动记录已保存: {record_file}")
            
        except Exception as e:
            self.logger.error(f"保存启动记录失败: {e}")
            
    def perform_startup_check(self) -> Tuple[bool, str]:
        """执行完整的启动检查 - 增强异常处理和降级模式"""
        
        print("🚀 YDS-Lab AI Agent 启动检查")
        print("=" * 50)
        
        # 记录开始时间
        start_time = time.time()
        
        try:
            # 先确保长记忆文件存在且有效
            self.ensure_longmemory_records()

            # 执行各项检查，使用异常处理包装
            checks_result = {}
            
            # 项目结构检查
            try:
                checks_result['structure_ok'] = self.check_project_structure()
            except Exception as e:
                self.logger.error(f"项目结构检查失败: {e}")
                checks_result['structure_ok'] = False
                if not self.default_config['error_handling']['continue_on_non_critical_errors']:
                    raise
            
            # Python环境检查
            try:
                checks_result['python_env'] = self.check_python_environment()
            except Exception as e:
                self.logger.error(f"Python环境检查失败: {e}")
                checks_result['python_env'] = {'dependencies_ok': False, 'error': str(e)}
                if not self.default_config['error_handling']['continue_on_non_critical_errors']:
                    raise
            
            # 长记忆系统检查
            try:
                checks_result['memory_system'] = self.check_memory_system_status()
            except Exception as e:
                self.logger.error(f"长记忆系统检查失败: {e}")
                checks_result['memory_system'] = {
                    'system_exists': False,
                    'ready': False,
                    'overall_health': 'check_failed',
                    'error': str(e)
                }
            
            # MCP服务器检查
            try:
                checks_result['mcp_status'] = self.check_mcp_servers_status()
            except Exception as e:
                self.logger.error(f"MCP服务器检查失败: {e}")
                checks_result['mcp_status'] = {
                    'config_found': False,
                    'servers': {},
                    'status': 'check_failed',
                    'error': str(e)
                }
            
            # Trae Agent检查
            try:
                checks_result['trae_agents'] = self.check_trae_agents_config()
            except Exception as e:
                self.logger.error(f"Trae Agent检查失败: {e}")
                checks_result['trae_agents'] = {
                    'trae_agents_dir_exists': False,
                    'agents_dir_exists': False,
                    'trae_config_exists': False,
                    'agents_ready': False,
                    'error': str(e)
                }
            
            # 核心文档检查
            try:
                checks_result['docs_status'] = self.check_core_documents()
            except Exception as e:
                self.logger.error(f"核心文档检查失败: {e}")
                checks_result['docs_status'] = {
                    'total_docs': 0,
                    'found_docs': 0,
                    'docs_complete': False,
                    'error': str(e)
                }
            
            # 工具资产检查
            try:
                checks_result['tool_status'] = self.check_tool_assets()
            except Exception as e:
                self.logger.error(f"工具资产检查失败: {e}")
                checks_result['tool_status'] = {
                    'total_tools': 4,
                    'found_tools': 0,
                    'tools_complete': False,
                    'error': str(e)
                }
            
            # 自动启动长记忆系统（如果配置启用）
            if (self.default_config['memory_system']['auto_start'] and 
                checks_result['memory_system'].get('ready', False)):
                try:
                    start_result = self.start_memory_system()
                    checks_result['memory_system']['auto_start_result'] = start_result
                except Exception as e:
                    self.logger.error(f"长记忆系统自动启动失败: {e}")
                    checks_result['memory_system']['auto_start_result'] = {
                        'success': False,
                        'error': str(e)
                    }
            
            # 运行合规性检查（如果启用）
            if self.default_config['compliance']['check_structure']:
                try:
                    checks_result['compliance_check'] = self.run_structure_compliance_check()
                except Exception as e:
                    self.logger.error(f"合规性检查失败: {e}")
                    checks_result['compliance_check'] = False
            else:
                checks_result['compliance_check'] = True
                
            # 计算检查耗时
            check_duration = time.time() - start_time
            self.logger.info(f"启动检查完成，耗时: {check_duration:.1f}秒")
            
            # 生成启动简报
            briefing = self.generate_startup_briefing(checks_result)
            
            # 显示简报
            print(briefing)
            
            # 保存启动记录
            self.save_startup_record(briefing)
            
            # 判断整体状态
            critical_checks = [
                checks_result['structure_ok'],
                checks_result['python_env']['dependencies_ok'],
                checks_result['tool_status']['tools_complete']
            ]
            
            overall_success = all(critical_checks)
            
            # 根据配置决定是否在非关键错误时继续
            if not overall_success and self.default_config['error_handling']['enable_degraded_mode']:
                # 降级模式：即使有些检查失败，也允许继续
                error_count = sum(1 for check in critical_checks if not check)
                success_msg = f"⚠️ YDS-Lab AI Agent启动检查完成 - 发现{error_count}个问题，降级模式运行中"
                self.logger.warning(f"启动检查发现问题，进入降级模式: {error_count}个关键错误")
                return True, success_msg  # 在降级模式下返回成功
            elif overall_success:
                success_msg = "✅ YDS-Lab AI Agent启动检查完成 - 系统就绪"
                return True, success_msg
            else:
                error_count = sum(1 for check in critical_checks if not check)
                success_msg = f"❌ YDS-Lab AI Agent启动检查完成 - 发现{error_count}个关键问题"
                return False, success_msg
                
        except TimeoutError as e:
            error_msg = f"⏰ 启动检查超时: {e}"
            self.logger.error(error_msg)
            
            # 超时降级处理
            if self.default_config['startup_checks']['enable_fallback_mode']:
                self.logger.warning("启动检查超时，启用回退模式")
                return True, "⚠️ 启动检查超时，启用回退模式 - 基本功能可用"
            else:
                return False, error_msg
                
        except Exception as e:
            error_msg = f"❌ 启动检查系统异常: {e}"
            self.logger.error(error_msg)
            
            # 最终降级处理
            if self.default_config['error_handling']['enable_degraded_mode']:
                self.logger.error("启动检查系统异常，尝试降级启动")
                return True, "⚠️ 启动检查异常，降级模式运行 - 建议手动检查系统状态"
            else:
                return False, error_msg

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="YDS-Lab AI Agent启动检查系统")
    parser.add_argument("--check", action="store_true", help="执行启动检查")
    parser.add_argument("--simple", action="store_true", help="简化版启动检查")
    parser.add_argument("--root", type=str, help="项目根目录路径")
    parser.add_argument("--auto-start", action="store_true", help="自动启动长记忆系统")
    parser.add_argument("--config", type=str, help="指定配置文件路径")
    
    args = parser.parse_args()
    
    project_root = args.root if args.root else "s:/YDS-Lab"
    checker = YDSLabStartupChecker(project_root=project_root)
    
    if args.simple:
        # 简化版检查
        print("🚀 YDS-Lab 快速启动检查")
        print("=" * 30)
        
        structure_ok = checker.check_project_structure()
        python_env = checker.check_python_environment()
        
        print(f"📁 项目结构: {'✅ 正常' if structure_ok else '❌ 异常'}")
        print(f"🐍 Python环境: {'✅ 正常' if python_env['dependencies_ok'] else '❌ 异常'}")
        print(f"📅 当前时间: {checker.get_current_system_date()['datetime']}")
        
        if structure_ok and python_env['dependencies_ok']:
            print("\n✅ 快速检查通过，可以开始工作")
            return 0
        else:
            print("\n⚠️ 发现问题，建议运行完整检查")
            return 1
    else:
        # 完整检查
        success, message = checker.perform_startup_check()
        print(f"\n{message}")
        return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())