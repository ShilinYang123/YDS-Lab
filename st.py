#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YDS-Lab AI Agent 启动检查系统

功能：
- AI Agent合规性检查
- MCP服务器状态验证
- 项目环境预检
- 工作流程启动
- 监控系统管理

适配YDS-Lab项目和CrewAI多智能体协作需求
"""

import os
import sys
import json
import time
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Optional, Tuple
import yaml

class YDSLabStartupChecker:
    """YDS-Lab AI Agent启动检查器"""
    
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
        # 新标准：04-prod/001-memory-system（不再使用 03-proc/** 旧路径）
        self.memory_system_dir = self.project_root / "04-prod" / "001-memory-system"
        # 日志目录修订：公司级机器日志统一为 01-struc/logs，可被环境变量覆盖
        # 优先使用 YDS_COMPANY_LOGS_ROOT，其次默认到 01-struc/logs
        env_company_logs = os.environ.get('YDS_COMPANY_LOGS_ROOT')
        self.logs_dir = Path(env_company_logs) if env_company_logs else (self.struc_dir / "logs")
        
        # 设置日志
        self.setup_logging()
        
        # 配置文件路径（迁移到 0B-general-manager/config）
        self.config_file = self.struc_dir / "0B-general-manager" / "config" / "startup_config.yaml"
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
                'required_services': ['MemoryService', 'ContentProcessor', 'IntelligentFilter'],
                'test_on_startup': True
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
                'check_memory_system': True
            }
        }
        
        self.load_config()

    def ensure_longmemory_records(self) -> bool:
        """确保长记忆文件存在且为有效JSON，如损坏则尝试自动修复"""
        try:
            # 统一长记忆持久化目录到公司级 01-struc/logs/longmemory（支持环境变量覆盖）
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
            
    def get_current_system_date(self) -> Dict[str, str]:
        """获取当前系统日期信息"""
        now = datetime.now()
        weekdays_cn = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        
        return {
            'date': now.strftime('%Y-%m-%d'),
            'datetime': now.strftime('%Y-%m-%d %H:%M:%S'),
            'formatted': now.strftime('%Y年%m月%d日'),
            'weekday_cn': weekdays_cn[now.weekday()],
            'timestamp': now.timestamp()
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
        """检查长记忆系统状态"""
        self.logger.info("检查长记忆系统状态...")
        
        memory_status = {
            'system_exists': False,
            'config_exists': False,
            'dependencies_ok': False,
            'services_status': {},
            'test_results': None,
            'ready': False
        }
        
        # 检查系统目录
        if self.memory_system_dir.exists():
            memory_status['system_exists'] = True
            
            # 检查配置文件
            config_file = self.memory_system_dir / "memory-config.yaml"
            if config_file.exists():
                memory_status['config_exists'] = True
                
            # 检查package.json和依赖
            package_file = self.memory_system_dir / "package.json"
            if package_file.exists():
                try:
                    # 检查node_modules
                    node_modules = self.memory_system_dir / "node_modules"
                    memory_status['dependencies_ok'] = node_modules.exists()
                except Exception as e:
                    self.logger.warning(f"检查依赖失败: {e}")
                    
            # 检查核心服务文件
            required_services = self.default_config['memory_system']['required_services']
            for service in required_services:
                service_status = {'exists': False, 'compiled': False}
                
                # 检查源码
                src_path = self.memory_system_dir / "src" / "services" / f"{service}.ts"
                if src_path.exists():
                    service_status['exists'] = True
                    
                # 检查编译后的文件
                dist_path = self.memory_system_dir / "dist" / "src" / "services" / f"{service}.js"
                if dist_path.exists():
                    service_status['compiled'] = True
                    
                memory_status['services_status'][service] = service_status
                
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
                    
            # 判断系统是否就绪
            memory_status['ready'] = (
                memory_status['system_exists'] and 
                memory_status['config_exists'] and
                memory_status['dependencies_ok'] and
                all(service['exists'] for service in memory_status['services_status'].values())
            )
        else:
            self.logger.warning("长记忆系统目录不存在")
            
        return memory_status
        
    def start_memory_system(self) -> Dict[str, any]:
        """启动长记忆系统"""
        self.logger.info("尝试启动长记忆系统...")
        
        start_result = {
            'attempted': False,
            'success': False,
            'process_id': None,
            'error': None,
            'message': ''
        }
        
        try:
            # 检查系统状态
            memory_status = self.check_memory_system_status()
            
            if not memory_status['ready']:
                start_result['error'] = "系统未就绪，无法启动"
                start_result['message'] = "请先确保长记忆系统配置正确且依赖已安装"
                return start_result
                
            # 检查是否已经在运行
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['cmdline'] and any('test-memory-system.js' in cmd for cmd in proc.info['cmdline']):
                        start_result['message'] = f"长记忆系统已在运行 (PID: {proc.info['pid']})"
                        start_result['success'] = True
                        start_result['process_id'] = proc.info['pid']
                        return start_result
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # 启动系统
            import subprocess
            import os
            
            start_result['attempted'] = True
            
            # 切换到memory-system目录并启动
            cmd = ['node', 'test-memory-system.js']
            process = subprocess.Popen(
                cmd,
                cwd=str(self.memory_system_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            )
            
            start_result['success'] = True
            start_result['process_id'] = process.pid
            start_result['message'] = f"长记忆系统启动成功 (PID: {process.pid})"
            
            self.logger.info(f"长记忆系统启动成功，进程ID: {process.pid}")
            
        except ImportError:
            start_result['error'] = "缺少psutil依赖包"
            start_result['message'] = "请安装psutil: pip install psutil"
        except Exception as e:
            start_result['error'] = str(e)
            start_result['message'] = f"启动失败: {e}"
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
        
        # 检查主配置文件（优先使用 config/trae_config.yaml，兼容旧路径 01-struc/trae_config.yaml）
        config_trae_new = self.project_root / "config" / "trae_config.yaml"
        config_trae_old = self.struc_dir / "trae_config.yaml"
        if config_trae_new.exists():
            config_status['trae_config_exists'] = True
        elif config_trae_old.exists():
            self.logger.warning("检测到旧版配置文件位置 01-struc/trae_config.yaml，建议迁移到 config/trae_config.yaml")
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
        """检查核心文档"""
        self.logger.info("检查核心文档...")
        
        core_docs = [
            "YDS-AI-组织与流程/《动态目录结构清单》.md",
            "YDS-AI-组织与流程/项目架构设计.md",
            "YDS-AI-组织与流程/YDS AI公司建设与项目实施完整方案（V1.0）.md",
            "README.md",
            "project_structure.md"
        ]
        
        doc_status = {
            'total_docs': len(core_docs),
            'found_docs': 0,
            'missing_docs': [],
            'existing_docs': []
        }
        
        for doc_path in core_docs:
            if doc_path in ["README.md", "project_structure.md"]:
                if doc_path == "README.md":
                    full_path = self.project_root / doc_path
                else:
                    full_path = self.struc_dir / doc_path
            else:
                full_path = self.docs_dir / doc_path
                
            if full_path.exists():
                doc_status['found_docs'] += 1
                doc_status['existing_docs'].append(doc_path)
            else:
                doc_status['missing_docs'].append(doc_path)
                
        doc_status['docs_complete'] = doc_status['found_docs'] == doc_status['total_docs']
        
        return doc_status
        
    def check_tool_assets(self) -> Dict[str, any]:
        """检查工具资产"""
        self.logger.info("检查工具资产...")
        
        core_tools = [
            "update_structure.py",
            "check_structure.py", 
            "start.py",
            "finish.py"
        ]
        
        tool_status = {
            'total_tools': len(core_tools),
            'found_tools': 0,
            'missing_tools': [],
            'existing_tools': []
        }
        
        for tool_name in core_tools:
            tool_path = self.tools_dir / tool_name
            if tool_path.exists():
                tool_status['found_tools'] += 1
                tool_status['existing_tools'].append(tool_name)
            else:
                tool_status['missing_tools'].append(tool_name)
                
        tool_status['tools_complete'] = tool_status['found_tools'] == tool_status['total_tools']
        
        return tool_status
        
    def run_structure_compliance_check(self) -> bool:
        """运行结构合规性检查"""
        try:
            check_script = self.tools_dir / "check_structure.py"
            if not check_script.exists():
                self.logger.warning("结构检查脚本不存在")
                return False
                
            result = subprocess.run(
                [sys.executable, str(check_script)],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=30
            )
            
            # 根据退出码判断合规性
            if result.returncode == 0:
                self.logger.info("结构合规性检查通过")
                return True
            elif result.returncode <= 2:
                self.logger.warning("结构合规性检查发现问题，但可继续")
                return True
            else:
                self.logger.error("结构合规性检查失败")
                return False
                
        except Exception as e:
            self.logger.error(f"结构合规性检查执行失败: {e}")
            return False
            
    def generate_startup_briefing(self, checks_result: Dict) -> str:
        """生成启动简报"""
        current_date = self.get_current_system_date()
        
        briefing = f"""
# YDS-Lab AI Agent 启动简报

> 生成时间: {current_date['formatted']} {current_date['weekday_cn']} {current_date['datetime']}  
> 项目根目录: `{self.project_root}`

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

        briefing += f"""

## 🧠 长记忆系统状态

### 系统配置
- **系统目录**: {'✅ 存在' if checks_result['memory_system']['system_exists'] else '❌ 不存在'}
- **配置文件**: {'✅ 存在' if checks_result['memory_system']['config_exists'] else '❌ 不存在'}
- **依赖安装**: {'✅ 完整' if checks_result['memory_system']['dependencies_ok'] else '❌ 缺失'}
- **系统就绪**: {'✅ 是' if checks_result['memory_system']['ready'] else '❌ 否'}

### 核心服务状态
"""
        
        # 添加服务状态详情
        for service, status in checks_result['memory_system']['services_status'].items():
            src_icon = "✅" if status['exists'] else "❌"
            compiled_icon = "✅" if status['compiled'] else "❌"
            briefing += f"- **{service}**: 源码{src_icon} 编译{compiled_icon}\n"
            
        # 添加测试结果
        if checks_result['memory_system']['test_results']:
            test_status = checks_result['memory_system']['test_results']
            if test_status == 'test_available':
                briefing += "- **测试状态**: ✅ 测试脚本可用\n"
            elif test_status == 'no_test_script':
                briefing += "- **测试状态**: ⚠️ 无测试脚本\n"
            else:
                briefing += f"- **测试状态**: ❌ {test_status}\n"
                
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
# 更新项目结构
python tools/update_structure.py

# 检查结构合规性
python tools/check_structure.py

# 完成工作会话
python fi.py
```

### AI协作建议
1. **多Agent协作**: 使用Trae Agent框架进行智能任务分解和协作处理
2. **知识管理**: 利用MCP Memory服务器进行知识存储和检索
3. **代码协作**: 通过GitHub MCP服务器进行版本控制
4. **文档生成**: 使用Context7服务器获取最新技术文档

---

*YDS-Lab AI智能协作系统 - 让AI成为您最得力的工作伙伴*
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
        """执行完整的启动检查"""
        try:
            print("🚀 YDS-Lab AI Agent 启动检查")
            print("=" * 50)

            # 先确保长记忆文件存在且有效
            self.ensure_longmemory_records()

            # 执行各项检查
            checks_result = {
                'structure_ok': self.check_project_structure(),
                'python_env': self.check_python_environment(),
                'memory_system': self.check_memory_system_status(),
                'mcp_status': self.check_mcp_servers_status(),
                'trae_agents': self.check_trae_agents_config(),
                'docs_status': self.check_core_documents(),
                'tool_status': self.check_tool_assets()
            }
            
            # 自动启动长记忆系统（如果配置启用）
            if (self.default_config['memory_system']['auto_start'] and 
                checks_result['memory_system'].get('ready', False)):
                start_result = self.start_memory_system()
                checks_result['memory_system']['auto_start_result'] = start_result
            
            # 运行合规性检查（如果启用）
            if self.default_config['compliance']['check_structure']:
                checks_result['compliance_check'] = self.run_structure_compliance_check()
            else:
                checks_result['compliance_check'] = True
                
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
            
            if overall_success:
                success_msg = "✅ YDS-Lab AI Agent启动检查完成 - 系统就绪"
            else:
                success_msg = "⚠️ YDS-Lab AI Agent启动检查完成 - 发现问题，但可继续工作"
                
            return overall_success, success_msg
            
        except Exception as e:
            error_msg = f"❌ 启动检查失败: {e}"
            self.logger.error(error_msg)
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