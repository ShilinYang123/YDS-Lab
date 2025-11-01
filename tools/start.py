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
        self.docs_dir = self.project_root / "Docs"
        self.ai_dir = self.project_root / "ai"
        self.logs_dir = self.project_root / "Struc" / "GeneralOffice" / "logs"
        
        # 设置日志
        self.setup_logging()
        
        # 配置文件路径
        self.config_file = self.project_root / "Struc" / "GeneralOffice" / "config" / "startup_config.yaml"
        self.mcp_config_candidates = [
            self.project_root / "claude_desktop_config.json",
            Path(os.path.expandvars(r"%APPDATA%\Claude\claude_desktop_config.json")),
            self.tools_dir / "MCP" / "claude_desktop_config.json",
        ]
        
        # 默认配置
        self.default_config = {
            'ai_agents': {
                'enable_crewai': True,
                'enable_monitoring': True,
                'auto_start_agents': False
            },
            'mcp_servers': {
                'required_servers': ['memory', 'github', 'context7'],
                'check_timeout': 10
            },
            'compliance': {
                'auto_start_monitoring': True,
                'check_structure': True,
                'validate_docs': True
            },
            'startup_checks': {
                'check_python_env': True,
                'check_dependencies': True,
                'check_git_config': True
            }
        }
        
        self.load_config()
        
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
            'Docs', 'ai', 'tools', 'projects', 'env', 'Struc/GeneralOffice/logs', 'logs'
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
            # 读取MCP配置
            with open(config_file, 'r', encoding='utf-8-sig') as f:
                config = json.load(f)
                
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
                
            return {
                'config_found': True,
                'config_file': str(config_file),
                'servers': server_status,
                'total_servers': len(mcp_servers),
                'status': 'ok' if mcp_servers else 'no_servers'
            }
            
        except Exception as e:
            self.logger.error(f"MCP配置读取失败: {e}")
            return {
                'config_found': True,
                'config_file': str(config_file),
                'servers': {},
                'status': 'error',
                'error': str(e)
            }
            
    def check_ai_agents_config(self) -> Dict[str, any]:
        """检查AI Agent配置"""
        self.logger.info("检查AI Agent配置...")
        
        agents_dir = self.ai_dir / "agents"
        tasks_dir = self.ai_dir / "tasks"
        tools_dir = self.ai_dir / "tools"
        memory_dir = self.ai_dir / "memory"
        
        config_status = {
            'agents_dir_exists': agents_dir.exists(),
            'tasks_dir_exists': tasks_dir.exists(),
            'tools_dir_exists': tools_dir.exists(),
            'memory_dir_exists': memory_dir.exists(),
            'agent_files': [],
            'task_files': [],
            'crewai_ready': False
        }
        
        # 检查Agent文件
        if agents_dir.exists():
            agent_files = list(agents_dir.glob("*.py"))
            config_status['agent_files'] = [f.name for f in agent_files]
            
        # 检查Task文件
        if tasks_dir.exists():
            task_files = list(tasks_dir.glob("*.py"))
            config_status['task_files'] = [f.name for f in task_files]
            
        # 检查CrewAI就绪状态
        config_status['crewai_ready'] = (
            config_status['agents_dir_exists'] and 
            config_status['tasks_dir_exists'] and
            len(config_status['agent_files']) > 0
        )
        
        return config_status
        
    def check_core_documents(self) -> Dict[str, any]:
        """检查核心文档"""
        self.logger.info("检查核心文档...")
        
        core_docs = [
            "YDS-AI-组织与流程/《动态目录结构清单》.md",
            "YDS-AI-组织与流程/项目架构设计.md",
            "YDS-AI-组织与流程/YDS AI公司建设与项目实施完整方案（V1.0）.md"
        ]
        
        doc_status = {
            'total_docs': len(core_docs),
            'found_docs': 0,
            'missing_docs': [],
            'existing_docs': []
        }
        
        for doc_path in core_docs:
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

### CrewAI多智能体状态
- **Agent目录**: {'✅ 已配置' if checks_result['ai_config']['agents_dir_exists'] else '❌ 未配置'}
- **Task目录**: {'✅ 已配置' if checks_result['ai_config']['tasks_dir_exists'] else '❌ 未配置'}
- **工具目录**: {'✅ 已配置' if checks_result['ai_config']['tools_dir_exists'] else '❌ 未配置'}
- **记忆存储**: {'✅ 已配置' if checks_result['ai_config']['memory_dir_exists'] else '❌ 未配置'}
- **Agent文件**: {len(checks_result['ai_config']['agent_files'])} 个
- **Task文件**: {len(checks_result['ai_config']['task_files'])} 个
- **系统就绪**: {'✅ 是' if checks_result['ai_config']['crewai_ready'] else '❌ 否'}

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
        if not checks_result['ai_config']['crewai_ready']:
            suggestions.append("- 🤖 配置AI Agent和任务定义")
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
python tools/finish.py
```

### AI协作建议
1. **多Agent协作**: 使用CrewAI框架进行任务分解和并行处理
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
            
            # 执行各项检查
            checks_result = {
                'structure_ok': self.check_project_structure(),
                'python_env': self.check_python_environment(),
                'mcp_status': self.check_mcp_servers_status(),
                'ai_config': self.check_ai_agents_config(),
                'docs_status': self.check_core_documents(),
                'tool_status': self.check_tool_assets()
            }
            
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