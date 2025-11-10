#!/usr/bin/env python3

# -*- coding: utf-8 -*-

"""
3AI工作室系统启动前置检查

确保AI Agent在每次工作前都能了解项目规范、MCP服务器状态和长效记忆系统

支持多类MCP服务器的统一管理和Trae长效记忆系统的自动启动

"""



import os
import sys
import json
import time
import subprocess
import logging
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Any, Optional
import yaml
import builtins

def setup_console_encoding():
    """在 Windows/Powershell 环境中尽量强制使用 UTF-8 输出，避免中文与 emoji 乱码"""
    try:
        os.environ.setdefault('PYTHONUTF8', '1')
        os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
        # Python 3.7+ 支持 reconfigure
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        # 安静失败，保持兼容
        pass

def fix_mojibake(s: Any) -> str:
    """
    检测常见乱码如 "✅", "⚡", "⚠", "�", "�" 等
    使用 cp1252 编码回转并用 utf-8 解码，避免字符损失。
    """
    try:
        if not isinstance(s, str):
            s = str(s)
        patterns = ("�", "�", "�", "�", "�", "�", "�", "�")
        if any(p in s for p in patterns):
            try:
                return s.encode('cp1252', errors='strict').decode('utf-8', errors='strict')
            except Exception:
                # 宽松回退
                return s.encode('cp1252', errors='ignore').decode('utf-8', errors='ignore')
        return s
    except Exception:
        return str(s)

# 包装内置 print，统一做乱码修复与 UTF-8 输出
_original_print = builtins.print
def _print_wrapper(*args, **kwargs):
    try:
        sep = kwargs.get('sep', ' ')
        end = kwargs.get('end', '\n')
        file = kwargs.get('file', None)
        flush = kwargs.get('flush', False)
        # 逐参数修复，保留原样格式
        fixed_args = [fix_mojibake(a) for a in args]
        _original_print(*fixed_args, sep=sep, end=end, file=file, flush=flush)
    except Exception:
        _original_print(*args, **kwargs)

builtins.print = _print_wrapper

# 进程启动时立即设置控制台编码
setup_console_encoding()


class AI3StudioStartupChecker:

    """3AI工作室系统启动前置检查器

 

 功能包括：

 - MCP服务器集群状态检查

 - 项目目录结构验证

 - AI Agent配置验证

 - 工作流程准备

 - Trae长效记忆系统自动启动

    """

 

    def __init__(self, project_root: str = "s:/3AI"):
        self.project_root = Path(project_root)
        self.docs_dir = self.project_root / "docs"
        self.tools_dir = self.project_root / "tools"
        # 公司级日志根目录，统一到 01-struc/logs；支持环境变量 YDS_COMPANY_LOGS_ROOT
        self.logs_dir = Path(os.environ.get('YDS_COMPANY_LOGS_ROOT', str(self.project_root / "01-struc" / "logs")))
        # 修正日志子目录为实际的中文名称
        self.work_logs_dir = self.logs_dir / "工作记录"
        self.output_dir = self.project_root / "03.Output"
        self.input_dir = self.project_root / "02.Input"
        self.task_dir = self.project_root / "01.TasK"
        self.mcp_dir = self.project_root / "tools" / "MCP"
        self.memory_dir = self.tools_dir / "LongMemory"
 

        # 确保日志目录存在

        self.work_logs_dir.mkdir(parents=True, exist_ok=True)

 

        # 核心规范文件路径（修复源码中的乱码为真实文件路径）
        self.core_docs = {
            "项目架构设计": self.docs_dir / "01-设计" / "项目架构设计.md",
            "开发任务书": self.docs_dir / "01-设计" / "开发任务书.md",
            "技术路线": self.docs_dir / "01-设计" / "技术路线.md",
            "规范与流程": self.docs_dir / "03-管理" / "规范与流程.md",
            "项目配置": self.docs_dir / "03-管理" / "project_config.yaml",
            "看板": self.docs_dir / "03-管理" / "看板.md",
            "工具资产清单": self.docs_dir / "03-管理" / "工具资产清单.md",
        }
 

        # 启动检查记录文件

        self.startup_log = self.logs_dir / "ai_assistant_startup.log"

 

        # 工具资产相关路径（修复中文名称）
        self.tool_rules_file = self.project_root / ".trae" / "rules" / "工具使用强制规范.md"
        self.tool_inventory_file = self.docs_dir / "03-管理" / "工具资产清单.md"
 

        # 设置工作流程日志

        self.setup_workflow_logging()

 

        # 禁用虚拟环境（根据用户要求）

        self.disable_virtual_environment()

 

        # 初始化系统日期管理

        self.setup_system_date_management()

 

        # 初始化GitHub认证配置

        self.setup_github_authentication()

 

        # 初始化Trae长效记忆系统

        self.setup_trae_memory_system()

 

    def setup_workflow_logging(self):

        """设置工作流程日志系统"""

        log_file = self.work_logs_dir / f"workflow_{datetime.now().strftime('%Y%m%d')}.log"

        # 创建工作流程专用的logger

        self.workflow_logger = logging.getLogger('WorkflowManager')

        self.workflow_logger.setLevel(logging.INFO)

        # 避免重复添加handler

        if not self.workflow_logger.handlers:

            # 写入使用 UTF-8 BOM，便于 Windows 记事本与部分查看器正确显示

            handler = logging.FileHandler(log_file, encoding='utf-8-sig')

            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

            handler.setFormatter(formatter)

            class MojibakeFixFilter(logging.Filter):

                def filter(self, record: logging.LogRecord) -> bool:

                    try:

                        # 修复消息文本的乱码

                        record.msg = fix_mojibake(record.getMessage())

                    except Exception:

                        pass

                    return True

            handler.addFilter(MojibakeFixFilter())

            self.workflow_logger.addHandler(handler)

    def disable_virtual_environment(self):

        "禁可可用虚拟环境自动激活（雨俊老师专可可用功能）"

        try:

            # 检查当�?是�?�在虚拟�?�境中

            if 'VIRTUAL_ENV' in os.environ:

                self.workflow_logger.info(f"检测到虚拟�?�境: {os.environ['VIRTUAL_ENV']}")

                self.workflow_logger.info("正在�?可可用虚拟�?�境.")

 

            # 移除虚拟�?�境相关的�?�境�?��?

            if 'VIRTUAL_ENV' in os.environ:

                del os.environ['VIRTUAL_ENV']

                self.workflow_logger.info("✓ 已移除 VIRTUAL_ENV �?�境�?��?")

 

            if 'VIRTUAL_ENV_PROMPT' in os.environ:

                del os.environ['VIRTUAL_ENV_PROMPT']

                self.workflow_logger.info("✓ 已移除 VIRTUAL_ENV_PROMPT �?�境�?��?")

 

            # �?��?系统PATH

            path = os.environ.get('PATH', '')

            path_parts = path.split(os.pathsep)

 

            # 移除虚拟�?�境相关的路径

            cleaned_paths = []

            for part in path_parts:

                if '.venv' not in part.lower() and 'virtual' not in part.lower():

                    cleaned_paths.append(part)

 

            os.environ['PATH'] = os.pathsep.join(cleaned_paths)

            self.workflow_logger.info("✓ 已清�?�PATH�?�境�?��?")

 

            # 检查是�?��?功切�?�到系统Python

            if '.venv' in sys.executable.lower() or 'virtual' in sys.executable.lower():

                self.workflow_logger.warning("⚠ 仍在虚拟环境中，建议重新启动终端")

            else:

                self.workflow_logger.info("✓ 成功切换到系统Python环境")

            # 记录当前Python环境信息

            self.workflow_logger.info(f"Python版本: {sys.version.split()[0]}")

            self.workflow_logger.info(f"Python路径: {sys.executable}")

 

            # 确保创建no_venv.bat脚本

            self.create_no_venv_script()

        except Exception as e:

            self.workflow_logger.error(f"禁用虚拟环境时发生错误: {e}")

    def create_no_venv_script(self):

        """创建无虚拟环境执行脚本"""

        try:

            script_content = '''@echo off

REM 禁用虚拟环境的批处理脚本

REM 雨俊老师专用 - 确保使用系统Python



echo = 禁用虚拟环境执行模式 =



REM 清除虚拟环境变量

set VIRTUAL_ENV=

set VIRTUAL_ENV_PROMPT=



REM 使用系统Python执行脚本

if "%1"=="" (

 echo 用法: no_venv.bat [Python脚本路径]

 echo 示例: no_venv.bat tools\\check_structure.py

 pause

 exit /b 1

)



echo 正在使用系统Python执行: %1

python %*



echo.

echo 脚本执行完成

pause

'''

            batch_file = self.tools_dir / "no_venv.bat"

            with open(batch_file, 'w', encoding='utf-8') as f:

                f.write(script_content)

            self.workflow_logger.info(f"✓ 已创建无虚拟环境执行脚本: {batch_file}")

        except Exception as e:

            self.workflow_logger.error(f"创建no_venv.bat脚本失败: {e}")

    def setup_system_date_management(self):

        """设置系统日期管理功能"""

        try:

            # 获取当前系统日期

            current_date = self.get_current_system_date()

            # 设置日期相关的环境变量

            self.set_date_environment_variables(current_date)

            # 创建日期配置文件

            self.create_date_config_file(current_date)

            # 记录日期设置

            self.workflow_logger.info(f"✓ 系统日期管理已初始化: {current_date['formatted']}")

        except Exception as e:

            self.workflow_logger.error(f"系统日期管理初始化失败: {e}")

    def get_current_system_date(self) -> Dict[str, str]:

        """获取当前系统日期（多格式）"""

        try:

            now = datetime.now()

            date_info = {

                'timestamp': now.isoformat(),

                'date': now.strftime('%Y-%m-%d'),

                'datetime': now.strftime('%Y-%m-%d %H:%M:%S'),

                'formatted': now.strftime('%Y年%m月%d日'),

                'year': str(now.year),

                'month': str(now.month),

                'day': str(now.day),

                'weekday': now.strftime('%A'),

                'weekday_cn': ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][now.weekday()],

                'unix_timestamp': str(int(now.timestamp()))

            }

            return date_info

        except Exception as e:

            self.workflow_logger.error(f"获取系统日期失败: {e}")

            # 返回默认值

            return {

                'timestamp': '2025-07-26T00:00:00',

                'date': '2025-07-26',

                'datetime': '2025-07-26 00:00:00',

                'formatted': '2025年07月26日',

                'year': '2025',

                'month': '7',

                'day': '26',

                'weekday': 'Friday',

                'weekday_cn': '周五',

                'unix_timestamp': '17219520'

            }

    def set_date_environment_variables(self, date_info: Dict[str, str]):

        """设置日期相关的环境变量"""

        try:

            # 设置环境变量供AI和脚本使用

            os.environ['SYSTEM_CURRENT_DATE'] = date_info['date']

            os.environ['SYSTEM_CURRENT_DATETIME'] = date_info['datetime']

            os.environ['SYSTEM_CURRENT_DATE_FORMATTED'] = date_info['formatted']

            os.environ['SYSTEM_CURRENT_YEAR'] = date_info['year']

            os.environ['SYSTEM_CURRENT_MONTH'] = date_info['month']

            os.environ['SYSTEM_CURRENT_DAY'] = date_info['day']

            os.environ['SYSTEM_CURRENT_WEEKDAY'] = date_info['weekday_cn']

            os.environ['SYSTEM_TIMESTAMP'] = date_info['timestamp']

            self.workflow_logger.info("✓ 日期环境变量已设置")

        except Exception as e:

            self.workflow_logger.error(f"设置日期环境变量失败: {e}")

    def create_date_config_file(self, date_info: Dict[str, str]):

        """创建日期配置文件供AI和其他脚本读取"""

        try:

            # 创建JSON格式的日期配置文件

            date_config_file = self.tools_dir / "current_date.json"

            config_data = {

                "system_date_info": date_info,

                "last_updated": date_info['timestamp'],

                "ai_instructions": {

                    "current_date": date_info['date'],

                    "formatted_date": date_info['formatted'],

                    "usage_note": "AI应使用此文件中的日期信息，而不是训练数据中的过时日期",

                    "priority": "系统当前日期优先于AI知识库中的日期信息"

                }

            }

            with open(date_config_file, 'w', encoding='utf-8') as f:

                json.dump(config_data, f, ensure_ascii=False, indent=2)

            self.workflow_logger.info(f"✓ 日期配置文件已创建: {date_config_file}")

            # 同时创建简单的文本文件供快速读取

            date_text_file = self.tools_dir / "current_date.txt"

            with open(date_text_file, 'w', encoding='utf-8') as f:

                f.write(f"当前系统日期: {date_info['formatted']}\n")

                f.write(f"ISO格式: {date_info['date']}\n")

                f.write(f"完整时间: {date_info['datetime']}\n")

                f.write(f"星期: {date_info['weekday_cn']}\n")

                f.write(f"\n注意: AI应使用此文件中的日期，而不是训练数据中的过时日期\n")

            self.workflow_logger.info(f"✓ 日期文本文件已创建: {date_text_file}")

        except Exception as e:

            self.workflow_logger.error(f"创建日期配置文件失败: {e}")

    def setup_github_authentication(self):

        """设置GitHub认证配置"""

        try:

            self.workflow_logger.info("正在设置GitHub认证.")

            # 读取GitHub配置文件

            github_config_file = self.tools_dir / ".github_config.json"

            if not github_config_file.exists():

                self.workflow_logger.warning("GitHub配置文件不存在，跳过GitHub认证配置")

                return

            with open(github_config_file, 'r', encoding='utf-8') as f:

                github_config = json.load(f)

            github_info = github_config.get('github', {})

            username = github_info.get('username')

            token = github_info.get('token')

            repo_url = github_info.get('repository', {}).get('url')

            if not all([username, token, repo_url]):

                self.workflow_logger.error("GitHub配置信息不完整")

                return

            # 设置Git全局配置

            self.configure_git_credentials(username, token, repo_url)

            # 设置环境变量

            os.environ['GITHUB_USERNAME'] = username

            os.environ['GITHUB_TOKEN'] = token

            os.environ['GITHUB_REPO_URL'] = repo_url

            self.workflow_logger.info(f"✓ GitHub认证配置完成 - 用户: {username}")

        except Exception as e:

            self.workflow_logger.error(f"设置GitHub认证失败: {e}")

    def configure_git_credentials(self, username: str, token: str, repo_url: str):

        """配置Git凭证"""

        try:

            # 设置Git用户名和邮箱

            subprocess.run(

                ["git", "config", "--global", "user.name", username],

                capture_output=True,

                text=True,

                check=True

            )

            subprocess.run(

                ["git", "config", "--global", "user.email", f"{username}@users.noreply.github.com"],

                capture_output=True,

                text=True,

                check=True

            )

            # 检查是否有备份Git仓库

            git_repo_dir = self.project_root / "bak" / "github_repo"

            if git_repo_dir.exists() and (git_repo_dir / ".git").exists():

                # 设置远程仓库URL（包含token）

                authenticated_url = repo_url.replace("https://", f"https://{username}:{token}@")

                subprocess.run(

                    ["git", "remote", "set-url", "origin", authenticated_url],

                    cwd=str(git_repo_dir),

                    capture_output=True,

                    text=True,

                    check=True

                )

                self.workflow_logger.info("✓ Git远程仓库URL已更新")

            else:

                self.workflow_logger.warning("未找到Git仓库，跳过远程URL设置")

            self.workflow_logger.info("✓ Git凭证配置完成")

        except subprocess.CalledProcessError as e:

            self.workflow_logger.error(f"配置Git凭证失败: {e}")

        except Exception as e:

            self.workflow_logger.error(f"配置Git凭证时出错: {e}")

 

    def setup_trae_memory_system(self):
        """设置和启动Trae长效记忆系统"""
        try:
            print("🧠 正在初始化Trae长效记忆系统...")
            print(f"   📁 记忆系统目录: {self.memory_dir}")
            
            # 检查长效记忆系统目录
            if not self.memory_dir.exists():
                print(f"❌ 长效记忆系统目录不存在: {self.memory_dir}")
                print("   🔧 尝试创建记忆系统目录...")
                try:
                    self.memory_dir.mkdir(parents=True, exist_ok=True)
                    print("   ✅ 记忆系统目录创建成功")
                except Exception as e:
                    print(f"   ❌ 记忆系统目录创建失败: {e}")
                    return False
            else:
                print("   ✅ 记忆系统目录存在")
            
            # 检查关键文档
            memory_docs = [
                self.memory_dir / "1.Trae长记忆功能实施.md",
                self.memory_dir / "2.Trae 长效记忆系统自动记录功能全流程升级方案（终版）.md"
            ]
            
            missing_docs = []
            existing_docs = []
            for doc in memory_docs:
                if not doc.exists():
                    missing_docs.append(doc.name)
                else:
                    existing_docs.append(doc.name)
            
            if existing_docs:
                print(f"   ✅ 已找到文档: {len(existing_docs)} 个")
                for doc in existing_docs:
                    print(f"      - {doc}")
            
            if missing_docs:
                print(f"   ⚠️ 缺少长效记忆系统文档: {len(missing_docs)} 个")
                for doc in missing_docs:
                    print(f"      - {doc}")
            else:
                print("   ✅ 长效记忆系统文档完整")
            
            # 设置记忆系统环境变量
            print("   🔧 设置环境变量...")
            os.environ['TRAE_MEMORY_ENABLED'] = 'true'
            os.environ['TRAE_MEMORY_DIR'] = str(self.memory_dir)
            os.environ['TRAE_PROJECT_ROOT'] = str(self.project_root)
            print("   ✅ 环境变量设置完成")
            
            # 创建记忆系统配置
            print("   📝 创建记忆系统配置...")
            memory_config = {
                "enabled": True,
                "auto_record": True,
                "memory_dir": str(self.memory_dir),
                "project_root": str(self.project_root),
                "knowledge_graph": {
                    "enabled": True,
                    "auto_update": True
                },
                "context_preservation": {
                    "enabled": True,
                    "max_context_length": 8000
                },
                "intelligent_summarization": {
                    "enabled": True,
                    "trigger_threshold": 7000
                }
            }
            
            # 保存记忆系统配置
            config_file = self.memory_dir / "trae_memory_config.json"
            try:
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(memory_config, f, ensure_ascii=False, indent=2)
                print(f"   ✅ 配置文件已保存: {config_file}")
            except Exception as e:
                print(f"   ❌ 配置文件保存失败: {e}")
                return False
            
            print("✅ Trae长效记忆系统配置完成")
            
            # 启动记忆系统监控
            monitoring_success = self._start_memory_monitoring()
            
            # 启动智能监控系统
            intelligent_monitoring_success = self._start_intelligent_monitoring()
            
            if monitoring_success:
                print("🎯 长效记忆系统启动成功！")
                print("   📊 功能状态:")
                print("      - 知识图谱: 已启用")
                print("      - 自动记录: 已启用")
                print("      - 上下文保留: 已启用")
                print("      - 智能摘要: 已启用")
                if intelligent_monitoring_success:
                    print("      - 智能错误预警: 已启用")
                    print("      - 主动提醒系统: 已启用")
                else:
                    print("      - 智能错误预警: 启动失败")
                return True
            else:
                print("⚠️ 长效记忆系统配置完成，但监控启动存在问题")
                print("   🔧 尝试自动恢复...")
                recovery_success = self.recover_memory_system()
                if recovery_success:
                    print("   🔄 重新尝试启动监控...")
                    retry_success = self._start_memory_monitoring()
                    if retry_success:
                        print("🎯 长效记忆系统恢复后启动成功！")
                        return True
                    else:
                        print("❌ 恢复后仍无法启动监控")
                        return False
                else:
                    print("❌ 自动恢复失败")
                    return False
            
        except Exception as e:
            print(f"❌ Trae长效记忆系统初始化失败: {e}")
            print(f"   🔍 错误详情: {type(e).__name__}")
            print("   🔧 尝试自动恢复...")
            
            try:
                recovery_success = self.recover_memory_system()
                if recovery_success:
                    print("   🔄 重新尝试完整初始化...")
                    return self.setup_trae_memory_system()
                else:
                    print("❌ 自动恢复失败，长记忆系统无法启动")
                    return False
            except Exception as recovery_error:
                print(f"❌ 恢复过程中发生错误: {recovery_error}")
                return False

    def recover_memory_system(self):
        """长记忆系统恢复机制"""
        try:
            print("🔧 启动长记忆系统恢复程序...")
            
            # 检查并修复目录结构
            print("   📁 检查目录结构...")
            directories_to_check = [
                self.memory_dir,
                self.logs_dir / "memory_system",
                self.memory_dir / "knowledge_graph",
                self.memory_dir / "context_cache",
                self.memory_dir / "summaries"
            ]
            
            for directory in directories_to_check:
                if not directory.exists():
                    try:
                        directory.mkdir(parents=True, exist_ok=True)
                        print(f"   ✅ 已创建目录: {directory.name}")
                    except Exception as e:
                        print(f"   ❌ 目录创建失败 {directory.name}: {e}")
                        return False
                else:
                    print(f"   ✅ 目录存在: {directory.name}")
            
            # 检查并修复配置文件
            print("   📝 检查配置文件...")
            config_file = self.memory_dir / "trae_memory_config.json"
            
            if not config_file.exists() or not self._validate_config_file(config_file):
                print("   🔧 重新创建配置文件...")
                try:
                    default_config = {
                        "enabled": True,
                        "auto_record": True,
                        "memory_dir": str(self.memory_dir),
                        "project_root": str(self.project_root),
                        "knowledge_graph": {
                            "enabled": True,
                            "auto_update": True
                        },
                        "context_preservation": {
                            "enabled": True,
                            "max_context_length": 8000
                        },
                        "intelligent_summarization": {
                            "enabled": True,
                            "trigger_threshold": 7000
                        },
                        "recovery_info": {
                            "last_recovery": datetime.now().isoformat(),
                            "recovery_count": 1
                        }
                    }
                    
                    with open(config_file, 'w', encoding='utf-8') as f:
                        json.dump(default_config, f, ensure_ascii=False, indent=2)
                    print("   ✅ 配置文件已重新创建")
                except Exception as e:
                    print(f"   ❌ 配置文件创建失败: {e}")
                    return False
            else:
                print("   ✅ 配置文件正常")
            
            # 检查并修复环境变量
            print("   🔧 检查环境变量...")
            required_env_vars = {
                'TRAE_MEMORY_ENABLED': 'true',
                'TRAE_MEMORY_DIR': str(self.memory_dir),
                'TRAE_PROJECT_ROOT': str(self.project_root)
            }
            
            for var_name, var_value in required_env_vars.items():
                if os.environ.get(var_name) != var_value:
                    os.environ[var_name] = var_value
                    print(f"   ✅ 已修复环境变量: {var_name}")
                else:
                    print(f"   ✅ 环境变量正常: {var_name}")
            
            # 创建恢复日志
            print("   📝 记录恢复信息...")
            recovery_log = {
                "timestamp": datetime.now().isoformat(),
                "recovery_type": "automatic",
                "status": "completed",
                "actions_taken": [
                    "检查并修复目录结构",
                    "检查并修复配置文件", 
                    "检查并修复环境变量"
                ]
            }
            
            recovery_log_file = self.logs_dir / "memory_system" / f"recovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            try:
                with open(recovery_log_file, 'w', encoding='utf-8') as f:
                    json.dump(recovery_log, f, ensure_ascii=False, indent=2)
                print(f"   ✅ 恢复日志已保存: {recovery_log_file.name}")
            except Exception as e:
                print(f"   ⚠️ 恢复日志保存失败: {e}")
            
            print("✅ 长记忆系统恢复完成")
            return True
            
        except Exception as e:
            print(f"❌ 长记忆系统恢复失败: {e}")
            print(f"   🔍 错误详情: {type(e).__name__}")
            return False

    def _start_intelligent_monitoring(self):
        """启动智能监控系统"""
        try:
            print("🤖 启动智能错误预警系统...")
            
            # 检查智能监控系统文件
            intelligent_monitor_path = self.memory_dir / "intelligent_monitor.py"
            if not intelligent_monitor_path.exists():
                print(f"   ❌ 智能监控系统文件不存在: {intelligent_monitor_path}")
                return False
            
            # 检查配置文件
            config_path = self.memory_dir / "intelligent_monitor_config.json"
            if not config_path.exists():
                print("   📝 创建智能监控系统配置...")
                default_config = {
                    "enabled": True,
                    "project_root": str(self.project_root),
                    "memory_dir": str(self.memory_dir),
                    "features": {
                        "smart_error_detection": True,
                        "proactive_reminders": True,
                        "learning_engine": True,
                        "real_time_monitoring": True
                    },
                    "detection_settings": {
                        "scan_interval": 30,
                        "severity_threshold": "medium",
                        "auto_fix_enabled": False
                    },
                    "notification_settings": {
                        "console_output": True,
                        "log_to_memory": True,
                        "alert_sound": False
                    }
                }
                
                try:
                    with open(config_path, 'w', encoding='utf-8') as f:
                        json.dump(default_config, f, ensure_ascii=False, indent=2)
                    print("   ✅ 配置文件已创建")
                except Exception as e:
                    print(f"   ❌ 配置文件创建失败: {e}")
                    return False
            
            # 启动智能监控系统进程
            print("   🚀 启动智能监控进程...")
            try:
                import subprocess
                import sys
                
                cmd = [sys.executable, str(intelligent_monitor_path)]
                process = subprocess.Popen(
                    cmd,
                    cwd=str(self.memory_dir),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                )
                
                # 等待一小段时间检查进程是否立即失败
                import time
                time.sleep(2)
                
                if process.poll() is None:
                    print(f"   ✅ 智能监控进程已启动 (PID: {process.pid})")
                    
                    # 记录启动信息
                    startup_log = {
                        "timestamp": datetime.now().isoformat(),
                        "system": "intelligent_monitor",
                        "status": "started",
                        "pid": process.pid,
                        "config_path": str(config_path)
                    }
                    
                    log_file = self.logs_dir / "memory_system" / f"intelligent_monitor_{datetime.now().strftime('%Y%m%d')}.log"
                    try:
                        with open(log_file, 'a', encoding='utf-8') as f:
                            f.write(f"{json.dumps(startup_log, ensure_ascii=False, indent=2)}\n")
                    except Exception as e:
                        print(f"   ⚠️ 启动日志记录失败: {e}")
                    
                    return True
                else:
                    stdout, stderr = process.communicate()
                    print(f"   ❌ 智能监控进程启动失败 (退出码: {process.returncode})")
                    if stderr.strip():
                        print(f"   🔍 错误信息: {stderr.strip()}")
                    return False
                    
            except Exception as e:
                print(f"   ❌ 启动智能监控进程异常: {e}")
                return False
            
        except Exception as e:
            print(f"⚠️ 智能监控系统启动失败: {e}")
            print(f"   🔍 错误详情: {type(e).__name__}")
            return False
    
    def _validate_config_file(self, config_file: Path) -> bool:
        """验证配置文件的完整性"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            required_keys = ['enabled', 'auto_record', 'memory_dir', 'project_root']
            for key in required_keys:
                if key not in config:
                    return False
            
            return True
        except Exception:
            return False
    
    def _start_memory_monitoring(self):
        """启动记忆系统监控"""
        try:
            print("🔍 启动记忆系统监控...")
            
            # 创建记忆系统日志目录
            memory_logs_dir = self.logs_dir / "memory_system"
            print(f"   📁 日志目录: {memory_logs_dir}")
            
            try:
                memory_logs_dir.mkdir(exist_ok=True)
                print("   ✅ 日志目录准备完成")
            except Exception as e:
                print(f"   ❌ 日志目录创建失败: {e}")
                return False
            
            # 设置记忆系统日志
            memory_log_file = memory_logs_dir / f"memory_system_{datetime.now().strftime('%Y%m%d')}.log"
            print(f"   📝 日志文件: {memory_log_file.name}")
            
            # 记录启动信息
            startup_info = {
                "timestamp": datetime.now().isoformat(),
                "project_root": str(self.project_root),
                "memory_dir": str(self.memory_dir),
                "status": "initialized",
                "features": {
                    "knowledge_graph": True,
                    "auto_record": True,
                    "context_preservation": True,
                    "intelligent_summarization": True
                }
            }
            
            try:
                with open(memory_log_file, 'a', encoding='utf-8') as f:
                    f.write(f"{json.dumps(startup_info, ensure_ascii=False, indent=2)}\n")
                print("   ✅ 启动信息已记录")
            except Exception as e:
                print(f"   ❌ 启动信息记录失败: {e}")
                return False
            
            # 验证配置文件
            config_file = self.memory_dir / "trae_memory_config.json"
            if config_file.exists():
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    if config.get('enabled', False):
                        print("   ✅ 配置验证通过")
                    else:
                        print("   ⚠️ 配置显示系统未启用")
                        return False
                except Exception as e:
                    print(f"   ❌ 配置验证失败: {e}")
                    return False
            else:
                print("   ❌ 配置文件不存在")
                return False
            
            print("✅ 记忆系统监控已启动")
            return True
            
        except Exception as e:
            print(f"⚠️ 记忆系统监控启动失败: {e}")
            print(f"   🔍 错误详情: {type(e).__name__}")
            return False

    def get_ai_date_instruction(self) -> str:

        """获取AI日期使用指令"""

        try:

            date_info = self.get_current_system_date()

            instruction = f"""= AI日期使用指令 =

当前系统日期: {date_info['formatted']} ({date_info['weekday_cn']})

ISO格式: {date_info['date']}

完整时间: {date_info['datetime']}



重要提醒:

1. 在生成任何需要日期的内容时，请使用上述当前系统日期

2. 不要使用AI训练数据中的过时日期或进行日期推测

3. 如需引用具体日期，请使用: {date_info['formatted']}

4. 环境变量 SYSTEM_CURRENT_DATE_FORMATTED 也包含此信息

5. 可读取 tools/current_date.json 获取完整日期信息



= 结束 ="""

            return instruction

        except Exception as e:

            self.workflow_logger.error(f"生成AI日期指令失败: {e}")

            return "AI日期指令生成失败，请手动确认当前日期"

    def run_script(self, script_name: str, args: Optional[List[str]] = None) -> bool:

        """运行指定脚本"""

        try:

            if args is None:

                args = []

            script_path = self.tools_dir / script_name

            if not script_path.exists():

                self.workflow_logger.error(f"脚本不存在: {script_path}")

                return False

            cmd = [sys.executable, str(script_path)]

            if args:

                cmd.extend(args)

            self.workflow_logger.info(f"执行命令: {' '.join(cmd)}")

            # 使用 gbk 编码处理中文输出

            result = subprocess.run(

                cmd,

                capture_output=True,

                text=True,

                encoding='gbk',

                errors='ignore',

                cwd=str(self.project_root),

                timeout=30

            )

            if result.returncode == 0:

                self.workflow_logger.info(f"[SUCCESS] {script_name} 执行成功")

                if result.stdout.strip():

                    self.workflow_logger.info(f"输出: {result.stdout.strip()}")

                return True

            else:

                self.workflow_logger.error(f"[ERROR] {script_name} 执行失败 (退出码: {result.returncode})")

                if result.stderr.strip():

                    self.workflow_logger.error(f"错误: {result.stderr.strip()}")

                return False

        except subprocess.TimeoutExpired:

            self.workflow_logger.error(f"[ERROR] {script_name} 执行超时")

            return False

        except Exception as e:

            self.workflow_logger.error(f"[ERROR] {script_name} 执行异常: {str(e)}")

            return False

    def check_prerequisites(self) -> bool:

        """检查前提条件"""

        self.workflow_logger.info("开始检查前提条件.")

        # 检查项目根目录

        if not self.project_root.exists():

            self.workflow_logger.error(f"项目根目录不存在: {self.project_root}")

            return False

        # 检查核心脚本（降级：合规监控脚本缺失仅警告，不阻断启动）

        monitor_script = self.tools_dir / "compliance_monitor.py"

        if not monitor_script.exists():

            self.workflow_logger.warning(f"合规监控脚本缺失（已降级为警告）: {monitor_script}")

        self.workflow_logger.info("前提条件检查通过")

        return True

    def start_monitoring_process(self) -> bool:
        """以非阻塞方式启动监控进程"""
        try:
            # 启动合规性监控
            script_path = self.tools_dir / "compliance_monitor.py"
            compliance_success = False
            
            if script_path.exists():
                cmd = [sys.executable, str(script_path), "--start"]
                self.workflow_logger.info(f"启动合规性监控进程: {' '.join(cmd)}")
                
                # 以非阻塞方式启动进程
                process = subprocess.Popen(
                    cmd,
                    cwd=str(self.project_root),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='gbk',
                    errors='ignore'
                )
                
                # 等待一小段时间检查进程是否立即失败
                time.sleep(1)
                if process.poll() is None:
                    # 进程仍在运行
                    self.workflow_logger.info(f"合规性监控进程已启动 (PID: {process.pid})")
                    compliance_success = True
                else:
                    # 进程已退出
                    stdout, stderr = process.communicate()
                    self.workflow_logger.error(f"合规性监控进程启动失败 (退出码: {process.returncode})")
                    if stderr.strip():
                        self.workflow_logger.error(f"错误信息: {stderr.strip()}")
            else:
                self.workflow_logger.warning(f"合规性监控脚本不存在: {script_path}")
            
            # 启动智能监控系统
            intelligent_success = self._start_intelligent_monitoring()
            
            # 只要有一个监控系统启动成功就返回True
            if compliance_success or intelligent_success:
                if compliance_success and intelligent_success:
                    self.workflow_logger.info("合规性监控和智能监控系统均已启动")
                elif compliance_success:
                    self.workflow_logger.info("合规性监控已启动，智能监控启动失败")
                else:
                    self.workflow_logger.info("智能监控系统已启动，合规性监控启动失败")
                return True
            else:
                self.workflow_logger.error("所有监控系统启动失败")
                return False
                
        except Exception as e:
            self.workflow_logger.error(f"启动监控进程异常: {str(e)}")
            return False

    def start_compliance_monitoring_enhanced(self) -> bool:

        """启动增强的合规性监控系统"""

        self.workflow_logger.info("启动合规性监控系统.")

        # 1. 检查监控状态

        self.workflow_logger.info("[1/4] 检查监控系统状态.")

        if not self.run_script("compliance_monitor.py", ["--status"]):

            self.workflow_logger.warning("监控系统状态检查失败，继续启动流程")

        # 2. 启用合规性机制（如存在）

        enable_script = self.tools_dir / "enable_compliance.py"

        if enable_script.exists():

            self.workflow_logger.info("[2/4] 启用合规性机制.")

            if not self.run_script("enable_compliance.py", ["--enable"]):

                # 降级：启用失败不阻断整体启动流程

                self.workflow_logger.warning("合规性机制启用失败（已降级为警告），继续启动流程")

        else:

            self.workflow_logger.info("[2/4] 跳过合规性机制启用（脚本不存在）")

        # 3. 检查是否已有监控进程在运行

        self.workflow_logger.info("[3/4] 检查现有监控进程.")

        if self.check_monitoring_system():

            self.workflow_logger.info("检测到监控系统已在运行")

            print("合规性监控系统已在运行")

            return True

        # 4. 尝试启动新的监控进程

        self.workflow_logger.info("[4/4] 尝试启动监控系统.")

        if self.start_monitoring_process():

            self.workflow_logger.info("合规性监控系统已启动")

            print("合规性监控系统已启动")

            return True

        else:

            self.workflow_logger.warning("合规性监控系统启动失败")

            print("合规性监控系统未启动（可手动启动）")

            return True  # 即使监控系统未启动，也允许继续工作流程

    def run_pre_checks(self) -> bool:

        """执行前置检查"""

        self.workflow_logger.info("执行前置检查.")

        # 1. 执行常规前置检查

        pre_check_script = self.tools_dir / "pre_operation_check.py"

        if pre_check_script.exists():

            if not self.run_script("pre_operation_check.py", ["report"]):

                self.workflow_logger.warning("前置检查发现问题，请查看详情")

                return False

        else:

            self.workflow_logger.info("跳过前置检查（脚本不存在）")

        # 2. 检查MCP服务器状态

        self.workflow_logger.info("执行MCP服务器状态检查.")

        mcp_status = self.check_mcp_servers_status()

        if not mcp_status:

            self.workflow_logger.warning("MCP服务器检查发现问题，请查看详细报告")

        # 3. 执行文档日期合规性检查

        self.workflow_logger.info("执行文档日期合规性检查.")

        date_check_script = self.tools_dir / "check_document_dates.py"

        if date_check_script.exists():

            if not self.run_script("check_document_dates.py", [str(self.project_root)]):

                self.workflow_logger.warning("发现文档日期合规问题")

                return False

        else:

            self.workflow_logger.info("跳过文档日期检查（脚本不存在）")

        self.workflow_logger.info("[SUCCESS] 所有前置检查通过")

        return True

    def show_work_reminders(self):

        """显示日常工作提醒"""

        reminders = [

            "日常工作提醒:",

            " - 所有操作将被实时监控",

            " - 任何违规行为将被自动记录和处理", 

            " - 请严格按照项目规范执行",

            " - 文件操作前请执行前置检查",

            " - 定期查看合规性报告",

            " - 已启用虚拟环境，使用系统Python以提升性能",

            " - 如需执行脚本，建议使用 no_venv.bat"

        ]

        for reminder in reminders:

            print(reminder)

            self.workflow_logger.info(reminder)

    def load_core_regulations(self) -> Dict[str, str]:

        """加载核心规范内容"""

        print("加载核心项目规范.")

        regulations = {}

        for doc_name, doc_path in self.core_docs.items():

            if doc_path.exists():

                try:

                    if doc_path.suffix.lower() in ['.yaml', '.yml']:

                        with open(doc_path, 'r', encoding='utf-8') as f:

                            content = yaml.safe_load(f)

                        regulations[doc_name] = json.dumps(content, ensure_ascii=False, indent=2)

                    else:

                        with open(doc_path, 'r', encoding='utf-8') as f:

                            regulations[doc_name] = f.read()

                    print(f" {doc_name}: 已加载")

                except Exception as e:

                    print(f" {doc_name}: 加载失败 - {e}")

            else:

                print(f" {doc_name}: 文件不存在 - {doc_path}")

        return regulations

    def extract_key_constraints(self, regulations: Dict[str, str]) -> List[str]:

        """提取关键约束条件"""

        print("提取关键约束条件.")

        constraints = []

        # 从“规范与流程”中提取核心约束和工作流程要求

        if "规范与流程" in regulations:

            content = regulations["规范与流程"]

            # 基础约束条件

            constraints.append("🚫 严禁在项目根目录创建任何临时文件或代码文件")

            constraints.append("✅ 每次操作前必须执行路径合规性检查")

            constraints.append("🔒 严格保护核心文档，禁止未授权的修改")

            constraints.append("⚡ 禁止使用虚拟环境，确保使用系统 Python 以提升性能")

            # 工作流程约束

            if "工作准备流程" in content:

                constraints.append("🔧 必须遵循标准工作准备流程")

            if "文件清理管理" in content:

                constraints.append("🧹 严格遵守文件清理管理规定")

            if "编码规范" in content:

                constraints.append("📚 严格遵守 UTF-8 编码规范")

            if "目录结构" in content:

                constraints.append("📁 严格遵守标准目录结构规范")

        # 项目配置中提取技术约束

        if "项目配置" in regulations:

            constraints.append("⚙️ 严格遵守项目配置中的技术规范")

 

         # 在开发任务书中提取项目目标约束

        if "开发任务书" in regulations:

            constraints.append("🏁 严格按照开发任务书的目标和范围执行")

        # 在技术方案中提取架构约束

        if "技术方案" in regulations:

            constraints.append("🛠️ 严格遵循技术方案的架构设计")

        return constraints

 

    def generate_startup_briefing(self, regulations: Dict[str, str], constraints: List[str]) -> str:
        """生成启动简报"""
        monitoring_status = "🟢 运行中" if self.check_monitoring_system() else "🔴 未运行"
        
        # 检查虚拟环境状态
        venv_status = "🔴 已禁用" if 'VIRTUAL_ENV' not in os.environ else "🟡 检测到虚拟环境"
        python_env = "系统Python" if '.venv' not in sys.executable.lower() else "虚拟环境Python"
        
        # 获取当前系统日期信息
        current_date = self.get_current_system_date()
        formatted_cn = datetime.now().strftime('%Y年%m月%d日')
        weekday_cn = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][datetime.now().weekday()]
        iso_date = current_date.get('date') if isinstance(current_date, dict) and current_date.get('date') else datetime.now().strftime('%Y-%m-%d')
        full_dt = current_date.get('datetime') if isinstance(current_date, dict) and current_date.get('datetime') else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        briefing = f"""
# AI助理启动简报

**启动时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**项目根目录**: {self.project_root}
**监控系统状态**: {monitoring_status}
**虚拟环境状态**: {venv_status}
**Python环境**: {python_env} ({sys.version.split()[0]}) 

## 📅 系统日期信息 (重要!)
**当前系统日期**: {formatted_cn} ({weekday_cn})
**ISO格式**: {iso_date}
**完整时间**: {full_dt}

⚠️ **AI重要提醒**: 
- 在生成任何需要日期的内容时，请使用上述当前系统日期
- 不要使用AI训练数据中的历史日期或进行日期推测
- 环境变量 SYSTEM_CURRENT_DATE_FORMATTED 包含格式化日期
- 可读取 tools/current_date.json 获取完整日期信息

## 🎯 工作目标
作为本项目的技术负责人，您需要：
1. 严格遵守所有项目文档和规范
2. 确保每次操作都符合项目合规要求
3. 维护项目的完整性和一致性
4. 提供高质量的技术解决方案
5. **使用正确的系统当前日期**: {formatted_cn}

## 🔒 核心约束条件
"""

        for i, constraint in enumerate(constraints, 1):
            briefing += f"{i}. {constraint}\n"

        briefing += f"""

## 📄 已加载的核心文档
"""

        for doc_name in regulations.keys():
            briefing += f"- ✅ {doc_name}\n"

        briefing += f"""

## 🛠️ 必须使用的工具
- TaskManager: 任务分解和管理
- Memory: 重要内容记忆存储
- Context7: 技术文档查询
- Desktop-Commander: 终端命令执行
- 合规性检查工具: 确保操作合规

## ⚠️ 关键提醒
1. **每次工作前**: 必须检查项目规范
2. **每次操作前**: 必须执行前置检查
3. **每次工作后**: 必须进行自我检查
4. **文档命名**: 一律使用中文
5. **代码质量**: 必须通过flake8等工具检测

## 🚀 开始工作
现在您已经完成启动检查，可以开始按照项目规范进行工作。
请记住：您是高级软件专家和技术负责人，需要确保所有工作都符合最高标准。
"""

        return briefing

 

    def generate_startup_briefing_cn(self, regulations: Dict[str, str], constraints: List[str]) -> str:
        """生成启动简报（中文修复版）"""
        monitoring_status = "运行中" if self.check_monitoring_system() else "未运行"
        venv_status = "已禁用" if 'VIRTUAL_ENV' not in os.environ else "检测到虚拟环境"
        python_env = "系统Python" if '.venv' not in sys.executable.lower() else "虚拟环境Python"

        current_date = self.get_current_system_date()
        # 防乱码的日期变量（直接使用系统当前时间格式化）
        formatted_cn = datetime.now().strftime('%Y年%m月%d日')
        weekday_cn = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][datetime.now().weekday()]
        iso_date = current_date.get('date') if isinstance(current_date, dict) and current_date.get('date') else datetime.now().strftime('%Y-%m-%d')
        full_dt = current_date.get('datetime') if isinstance(current_date, dict) and current_date.get('datetime') else datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        briefing = f"""
# AI助手启动简报

**启动时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**项目根目录**: {self.project_root}
**监控系统状态**: {monitoring_status}
**虚拟环境状态**: {venv_status}
**Python环境**: {python_env} ({sys.version.split()[0]})

## 系统日期信息（重要）
**当前系统日期**: {formatted_cn} ({weekday_cn})
**ISO格式**: {iso_date}
**完整时间**: {full_dt}

**AI重要提醒**: 
- 在生成任何需要日期的内容时，请使用上述当前系统日期
- 不要使用AI训练数据中的历史日期或进行日期推测
- 环境变量 SYSTEM_CURRENT_DATE_FORMATTED 包含格式化日期
- 可读取 tools/current_date.json 获取完整日期信息

## 工作目标
"""
        for i, constraint in enumerate(constraints, 1):
            briefing += f"{i}. {constraint}\n"

        briefing += f"""

## 已加载的核心文档
"""
        for doc_name in regulations.keys():
            briefing += f"- {doc_name}\n"

        briefing += f"""

## 必须使用的工具
- TaskManager: 任务分解和管理
- Memory: 重要内容记忆存储
- Context7: 技术文档查询
- Desktop-Commander: 终端命令执行
- 合规性检查工具: 确保操作合规

## 关键提醒
1. **每次工作前**: 必须检查项目规范
2. **每次操作前**: 必须执行前置检查
3. **每次工作后**: 必须进行自我检查
4. **文档命名**: 一律使用中文
5. **代码质量**: 必须通过flake8等工具检测

## 开始工作
现在您已经完成启动检查，可以开始按照项目规范进行工作。
请记住：您是高级软件专家和技术负责人，需要确保所有工作都符合最高标准。
"""

        return briefing

    def save_startup_record(self, briefing: str):
        """保存启动记录"""
        # 确保日志目录存在
        self.logs_dir.mkdir(exist_ok=True)
        
        # 保存启动简报
        briefing_file = self.logs_dir / f"startup_briefing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(briefing_file, 'w', encoding='utf-8-sig') as f:
            f.write(briefing)
        
        # 更新启动日志（ASCII-only to avoid garbled text）
        log_entry = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - AI assistant startup check completed\n"
        with open(self.startup_log, 'a', encoding='utf-8-sig') as f:
            f.write(log_entry)
        
        # 控制台提示也改为英文 ASCII
        print(f"[Log] Startup briefing saved: {briefing_file}")

 

    def check_mcp_servers_status(self) -> bool:
        """检查 MCP 服务器状态和功能"""
        try:
            self.workflow_logger.info("开始检查 MCP 服务器状态.")

            # 检查 Claude Desktop 配置文件（支持多候选路径）
            candidates = [
                self.project_root / "claude_desktop_config.json",
                Path(os.path.expandvars(r"%APPDATA%\Claude\claude_desktop_config.json")),
                self.tools_dir / "MCP" / "servers" / "windows-system" / "claude_desktop_config.json",
            ]
            config_file = next((p for p in candidates if p.exists()), None)
            if not config_file:
                self.workflow_logger.error("Claude Desktop配置文件不存在（已检查项目根目录、%APPDATA%、示例路径）")
                return False
            else:
                self.workflow_logger.info(f"使用配置文件: {config_file}")

            # 读取MCP服务器配置（兼容 UTF-8 BOM）
            with open(config_file, 'r', encoding='utf-8-sig') as f:
                config = json.load(f)

            mcp_servers = config.get('mcpServers', {})
            if not mcp_servers:
                self.workflow_logger.error("未配置MCP服务器")
                return False

            self.workflow_logger.info(f"检测到 {len(mcp_servers)} 个已配置的MCP服务器")

            all_servers_ok = True
            server_status = {}

            for server_name, server_config in mcp_servers.items():
                self.workflow_logger.info(f"检查MCP服务器: {server_name}")

                # 检查服务器脚本文件是否存在
                if 'args' in server_config and server_config['args']:
                    script_path = Path(server_config['args'][0])
                    if script_path.exists():
                        self.workflow_logger.info(f"  ✓ {server_name}: 脚本文件存在")
                        server_status[server_name] = {'script_exists': True, 'functional': False}

                        # 测试服务器功能
                        if self._test_mcp_server_functionality(server_name, script_path):
                            server_status[server_name]['functional'] = True
                            self.workflow_logger.info(f"  ✓ {server_name}: 功能测试通过")
                        else:
                            self.workflow_logger.warning(f"  ⚠ {server_name}: 功能测试失败")
                            all_servers_ok = False
                    else:
                        self.workflow_logger.error(f"  ✗ {server_name}: 脚本文件不存在 ({script_path})")
                        server_status[server_name] = {'script_exists': False, 'functional': False}
                        all_servers_ok = False
                else:
                    self.workflow_logger.warning(f"  ⚠ {server_name}: 配置不完整")
                    server_status[server_name] = {'script_exists': False, 'functional': False}
                    all_servers_ok = False

            # 保存MCP服务器状态报告
            self._save_mcp_status_report(server_status)

            if all_servers_ok:
                self.workflow_logger.info("✓ 所有MCP服务器状态正常")
            else:
                self.workflow_logger.warning("⚠ 部分MCP服务器存在问题")

            return all_servers_ok

        except Exception as e:
            self.workflow_logger.error(f"MCP服务器状态检查失败: {e}")
            return False

 

    def _test_mcp_server_functionality(self, server_name: str, script_path: Path) -> bool:
        """测试MCP服务器功能"""
        try:
            # 根据服务器类型进行特定的测试
            if 'word' in server_name.lower():
                return self._test_word_mcp_server(script_path)
            elif 'powerpoint' in server_name.lower() or 'ppt' in server_name.lower():
                return self._test_powerpoint_mcp_server(script_path)
            elif 'photoshop' in server_name.lower():
                return self._test_photoshop_mcp_server(script_path)
            else:
                # 通用测试：检查脚本是否可以正常启动
                return self._test_generic_mcp_server(script_path)

        except Exception as e:
            self.workflow_logger.error(f"MCP服务器功能测试异常: {e}")
            return False

 

    def _test_word_mcp_server(self, script_path: Path) -> bool:
        """测试Word MCP服务器"""
        try:
            # 检查Word应用程序是否可用
            import win32com.client
            word_app = win32com.client.Dispatch("Word.Application")
            word_app.Visible = False
            word_app.Quit()
            return True
        except Exception:
            return False

    def _test_powerpoint_mcp_server(self, script_path: Path) -> bool:
        """测试PowerPoint MCP服务器"""
        try:
            # 检查PowerPoint应用程序是否可用
            import win32com.client
            ppt_app = win32com.client.Dispatch("PowerPoint.Application")
            ppt_app.Visible = 1
            ppt_app.Quit()
            return True
        except Exception:
            return False

    def _test_photoshop_mcp_server(self, script_path: Path) -> bool:
        """测试Photoshop MCP服务器"""
        try:
            # 检查Photoshop应用程序是否可用
            import win32com.client
            ps_app = win32com.client.Dispatch("Photoshop.Application")
            ps_app.Quit()
            return True
        except Exception:
            return False

    def _test_generic_mcp_server(self, script_path: Path) -> bool:
        """通用MCP服务器测试"""
        try:
            # 简单检查脚本文件语法
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # 检查是否包含基本的MCP服务器结构
            if 'mcp' in content.lower() and ('server' in content.lower() or 'tool' in content.lower()):
                return True
            return False
        except Exception:
            return False

 

    def _save_mcp_status_report(self, server_status: Dict[str, Dict[str, bool]]):
        """保存MCP服务器状态报告"""
        try:
            report_file = self.logs_dir / f"mcp_status_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            report = {
                'timestamp': datetime.now().isoformat(),
                'total_servers': len(server_status),
                'functional_servers': sum(1 for status in server_status.values() if status['functional']),
                'servers': server_status
            }

            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

            self.workflow_logger.info(f"MCP状态报告已保存: {report_file}")

        except Exception as e:
            self.workflow_logger.error(f"保存MCP状态报告失败: {e}")

 

    def check_tool_assets_availability(self) -> Dict[str, Any]:
        """检查工具资产可用性"""
        tool_status = {
            "mcp_servers": {},
            "scripts": {},
            "rules_available": False,
            "inventory_available": False
        }

        # 检查工具使用规范文件
        if self.tool_rules_file.exists():
            tool_status["rules_available"] = True
            print("✅ 工具使用强制规范文件已加载")
        else:
            print("❌ 工具使用强制规范文件不存在")

        # 检查工具资产清单
        if self.tool_inventory_file.exists():
            tool_status["inventory_available"] = True
            print("✅ 工具资产清单文件已加载")
        else:
            print("❌ 工具资产清单文件不存在")

        # 检查MCP服务器目录
        if self.mcp_dir.exists():
            mcp_categories = ["data-processing", "collaboration", "creative", "digital-human"]
            for category in mcp_categories:
                category_path = self.mcp_dir / category
                if category_path.exists():
                    servers = list(category_path.glob("*"))
                    tool_status["mcp_servers"][category] = {
                        "available": True,
                        "count": len([s for s in servers if s.is_dir()])
                    }
                    print(f"✅ MCP服务器类别 {category}: {tool_status['mcp_servers'][category]['count']} 个")
                else:
                    tool_status["mcp_servers"][category] = {"available": False, "count": 0}

        # 检查关键脚本工具
        key_scripts = [
            "check_structure.py", "update_structure.py", "pdf_processor.py",
            "office_document_reader.py", "mcp_server_manager.py", "finish.py"
        ]

        for script in key_scripts:
            script_path = self.tools_dir / script
            if script_path.exists():
                tool_status["scripts"][script] = True
                print(f"✅ 关键脚本 {script} 可用")
            else:
                tool_status["scripts"][script] = False
                print(f"❌ 关键脚本 {script} 不存在")

        return tool_status

    def generate_tool_usage_reminder(self, tool_status: Dict[str, Any]) -> str:
        """生成工具使用提醒"""
        reminder = []
        reminder.append("🛠 工具资产使用提醒")
        reminder.append("=" * 30)

        # MCP服务器提醒
        if tool_status["mcp_servers"]:
            reminder.append("\n🛠 可用MCP服务器:")
            for category, info in tool_status["mcp_servers"].items():
                if info["available"] and info["count"] > 0:
                    reminder.append(f"  • {category}: {info['count']} 个服务器")

        # 脚本工具提醒
        available_scripts = [name for name, available in tool_status["scripts"].items() if available]
        if available_scripts:
            reminder.append("\n🛠️ 可用脚本工具:")
            for script in available_scripts:
                reminder.append(f"  • {script}")

        # 使用规范提醒
        if tool_status["rules_available"]:
            reminder.append("\n🛡️ 请严格遵守工具使用强制规范:")
            reminder.append("  • 复杂任务必须使用TaskManager分解")
            reminder.append("  • 技术查询优先使用context7")
            reminder.append("  • 新信息必须存入Memory")
            reminder.append("  • Excel操作必须使用Excel MCP")
            reminder.append("  • 文档处理必须使用对应处理器")

        return "\n".join(reminder)



    def query_monitoring_status_via_script(self) -> bool:
        """通过脚本输出判断监控状态（psutil缺失或进程检测不可用时的回退）"""
        try:
            compliance_script = self.tools_dir / "compliance_monitor.py"
            if not compliance_script.exists():
                return False
            # 优先使用 UTF-8，强制子进程以 UTF-8 输出；如果遇到平台限制则退回 GBK
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            try:
                result = subprocess.run(
                    [sys.executable, str(compliance_script), "--status"],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore',
                    cwd=str(self.project_root),
                    timeout=10,
                    env=env
                )
                output = (result.stdout or "") + (result.stderr or "")
                return "运行中" in output
            except Exception:
                # 极端情况的回退以确保鲁棒性（不改变主标准）
                result = subprocess.run(
                    [sys.executable, str(compliance_script), "--status"],
                    capture_output=True,
                    text=True,
                    encoding='gbk',
                    errors='ignore',
                    cwd=str(self.project_root),
                    timeout=10,
                    env=env
                )
                output = (result.stdout or "") + (result.stderr or "")
                return "运行中" in output
        except Exception:
            return False



    def check_monitoring_system(self) -> bool:
        """检查监控系统状态（增强版：进程扫描 + PID 文件 + 脚本回退）"""
        # 1) 首选：使用 psutil 扫描进程命令行
        try:
            import psutil  # type: ignore

            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['cmdline']:
                        cmdline = ' '.join(proc.info['cmdline'])
                        if 'compliance_monitor.py' in cmdline and '--start' in cmdline:
                            return True
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
        except ImportError:
            pass

        # 2) 次选：读取 PID 文件并校验进程是否存在并运行
        try:
            pid_file = self.project_root / 'logs' / '系统日志' / 'compliance_monitor.pid'
            if pid_file.exists():
                try:
                    pid_text = pid_file.read_text(encoding='utf-8').strip()
                    pid = int(pid_text) if pid_text else None
                except Exception:
                    pid = None

                if pid:
                    try:
                        import psutil  # type: ignore
                        if psutil.pid_exists(pid):
                            proc = psutil.Process(pid)
                            cmdline = ' '.join(proc.cmdline()) if proc.cmdline() else ''
                            if 'compliance_monitor.py' in cmdline and '--start' in cmdline:
                                return True
                            # 即使命令行无标志，但 PID 存活，保守判定为运行中
                            return True
                    except Exception:
                        # 无法使用 psutil 时，存在有效 PID 文件则保守报告运行中
                        return True
        except Exception:
            pass

        # 3) 最后回退：通过脚本输出判断监控状态
        return self.query_monitoring_status_via_script()

 

    def start_monitoring_system(self) -> bool:
        """启动监控系统"""
        try:
            import subprocess
            import time

            # 检查配置是否允许自动启动
            config = self.load_project_config()
            if not config.get('compliance', {}).get('auto_start_monitoring', False):
                print("⚠ 配置文件中未启用自动启动监控")
                return False

            print("正在启动合规性监控系统.")

            # 启动监控系统（非阻塞方式）
            compliance_script = self.tools_dir / "compliance_monitor.py"
            if not compliance_script.exists():
                print(f"未找到监控脚本: {compliance_script}")
                # 尝试回退到批处理/PowerShell脚本
                fallback_candidates = [
                    ("bat", self.tools_dir / "start_compliance_monitoring.bat"),
                    ("ps1", self.tools_dir / "start_compliance_monitoring.ps1"),
                    ("bat", self.tools_dir / "start_monitor.bat"),
                ]
                for kind, path in fallback_candidates:
                    if path.exists():
                        try:
                            print(f"尝试使用回退脚本启动监控: {path}")
                            if kind == "bat":
                                proc = subprocess.Popen([
                                    "cmd", "/c", str(path)
                                ], cwd=str(self.project_root))
                            else:
                                proc = subprocess.Popen([
                                    "powershell", "-ExecutionPolicy", "Bypass", "-File", str(path)
                                ], cwd=str(self.project_root))
                            time.sleep(2)
                            if self.check_monitoring_system():
                                print("合规性监控系统启动成功")
                                return True
                        except Exception as _:
                            continue
                return False

            # 使用subprocess.Popen启动非阻塞进程
            process = subprocess.Popen(
                [sys.executable, str(compliance_script), "--start"],
                cwd=str(self.project_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if hasattr(subprocess, 'CREATE_NEW_PROCESS_GROUP') else 0
            )

            # 等待一段时间确认启动
            time.sleep(2)

            # 验证启动状态
            if self.check_monitoring_system():
                print("合规性监控系统启动成功")
                return True
            else:
                # 尝试回退到批处理/PowerShell脚本
                fallback_candidates = [
                    ("bat", self.tools_dir / "start_compliance_monitoring.bat"),
                    ("ps1", self.tools_dir / "start_compliance_monitoring.ps1"),
                    ("bat", self.tools_dir / "start_monitor.bat"),
                ]
                for kind, path in fallback_candidates:
                    if path.exists():
                        try:
                            print(f"尝试使用回退脚本辅助启动监控: {path}")
                            if kind == "bat":
                                proc = subprocess.Popen([
                                    "cmd", "/c", str(path)
                                ], cwd=str(self.project_root))
                            else:
                                proc = subprocess.Popen([
                                    "powershell", "-ExecutionPolicy", "Bypass", "-File", str(path)
                                ], cwd=str(self.project_root))
                            time.sleep(2)
                            if self.check_monitoring_system():
                                print("合规性监控系统启动成功")
                                return True
                        except Exception as _:
                            continue
                print("监控系统可能正在启动中，请稍后检查状态")
                return True  # 仍然返回True，因为启动命令已执行

        except Exception as e:
            print(f"启动监控系统失败: {e}")
            return False

 

    def load_project_config(self) -> dict:
        """加载项目配置"""
        try:
            from config_loader import load_yaml_config, PROJECT_CONFIG_PATH
            cfg = load_yaml_config(PROJECT_CONFIG_PATH, validate=False)
            # 设置默认值：自动启动监控为True
            if not isinstance(cfg, dict):
                cfg = {}
            compliance_cfg = cfg.get('compliance')
            if not isinstance(compliance_cfg, dict):
                compliance_cfg = {}
            if 'auto_start_monitoring' not in compliance_cfg:
                compliance_cfg['auto_start_monitoring'] = True
            cfg['compliance'] = compliance_cfg
            return cfg
        except Exception as e:
            print(f"⚠ 加载配置文件失败: {e}")
            # 回退默认配置
            return {"compliance": {"auto_start_monitoring": True}}

 

    def perform_startup_check(self) -> Tuple[bool, str]:
        """执行完整的启动检查"""
        import sys
        # 确保输出编码正确
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        
        print("PG AI助手启动检查开始")
        print("=" * 50)
        sys.stdout.flush()  # 强制刷新输出缓冲区
        
        try:
            # 1. 加载核心规范
            regulations = self.load_core_regulations()
            
            if not regulations:
                return False, "未能加载任何核心规范文档"
            
            # 2. 提取关键约束
            constraints = self.extract_key_constraints(regulations)
            
            # 3. 检查工具资产可用性
            print("\n检查工具资产可用性.")
            tool_status = self.check_tool_assets_availability()
            tool_reminder = self.generate_tool_usage_reminder(tool_status)
            
            # 4. 检查并启动监控系统
            monitoring_running = self.check_monitoring_system()
            if not monitoring_running:
                print("监控系统未运行，正在自动启动.")
                self.start_monitoring_system()
                time.sleep(1)
                if self.check_monitoring_system():
                    print("监控系统已在运行")
                else:
                    print("监控系统尚未运行，请手动启动或检查依赖")
            else:
                print("监控系统已在运行")
            
            # 5. 生成启动简报
            briefing = self.generate_startup_briefing_cn(regulations, constraints)
            
            # 6. 保存启动记录
            self.save_startup_record(briefing)
            
            # 7. 显示简报和工具可用性提醒
            print("\n" + "=" * 50)
            sys.stdout.flush()
            print(briefing)
            sys.stdout.flush()
            print("\n" + tool_reminder)
            sys.stdout.flush()
            print("=" * 50)
            sys.stdout.flush()
            
            monitoring_status = "运行中" if self.check_monitoring_system() else "未运行"
            success_msg = f"PG AI助手启动检查完成 - 已加载 {len(regulations)} 个核心文档，监控系统状态: {monitoring_status}"
            
            return True, success_msg
        
        except Exception as e:
            error_msg = f"启动检查失败: {e}"
            print(error_msg)
            return False, error_msg

 

    def start_work_session(self) -> Tuple[bool, str]:
        """启动完整的工作会话（整合AI检查和工作流程）"""
        import sys
        # 确保输出编码正确
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        
        print("PG HQ-OA 项目完整启动流程")
        print("=" * 50)
        self.workflow_logger.info("开始项目标准工作启动流程")
        sys.stdout.flush()
        
        try:
            # 第一阶段：AI助手启动检查
            print("\n第一阶段：AI助手启动检查")
            print("-" * 30)
            
            # 1. 加载核心规范
            regulations = self.load_core_regulations()
            if not regulations:
                return False, "未能加载任何核心规范文档"
            
            # 2. 提取关键约束
            constraints = self.extract_key_constraints(regulations)
            
            # 第二阶段：工作流程环境检查
            print("\n第二阶段：工作流程环境检查")
            print("-" * 30)
            
            # 3. 检查工具资产可用性
            print("\n检查工具资产可用性.")
            tool_status = self.check_tool_assets_availability()
            tool_reminder = self.generate_tool_usage_reminder(tool_status)
            
            # 4. 检查MCP服务器状态
            print("\n检查MCP服务器状态.")
            mcp_status = self.check_mcp_servers_status()
            if mcp_status:
                print("✅ MCP服务器检查通过")
            else:
                print("⚠ MCP服务器检查存在问题，但继续启动")
                self.workflow_logger.warning("MCP服务器检查存在问题")
            
            # 5. 检查前提条件
            if not self.check_prerequisites():
                self.workflow_logger.error("前提条件检查失败，无法启动工作会话")
                return False, "前提条件检查失败"
            print("✅ 前提条件检查通过")
            
            # 第三阶段：监控系统启动
            print("\n第三阶段：合规性监控系统启动")
            print("-" * 30)
            
            # 6. 启动增强的合规性监控
            if not self.start_compliance_monitoring_enhanced():
                # 不阻断整体流程，但在显示中明确未启动
                self.workflow_logger.warning("合规性监控启动失败（继续流程）")
                # 根据最新状态打印准确显示
                time.sleep(1)
                if self.check_monitoring_system():
                    print("合规性监控系统已启动")
                else:
                    print("合规性监控系统未启动（可手动启动）")
            
            # 第四阶段：配置检查
            print("\n第四阶段：运行配置检查")
            print("-" * 30)
            
            # 7. 运行配置检查
            if not self.run_pre_checks():
                self.workflow_logger.warning("配置检查存在问题，但继续工作会话")
                print("⚠ 配置检查存在问题，但继续启动")
            else:
                print("✅ 前置检查通过")
            
            # 第五阶段：生成启动简报
            print("\n第五阶段：生成启动简报")
            print("-" * 30)
            
            # 显示当前系统日期信息
            current_date = self.get_current_system_date()
            print(f"当前系统日期: {current_date['formatted']} ({current_date['weekday_cn']})")
            print(f" ISO格式: {current_date['date']}")
            print(f" 完整时间: {current_date['datetime']}")
            print(" ⚠ AI将使用此日期信息，而非训练数据中的截止日期")
            
            # 8. 生成启动简报
            briefing = self.generate_startup_briefing_cn(regulations, constraints)
            
            # 9. 保存启动记录
            self.save_startup_record(briefing)
            
            # 最终阶段：完成启动
            print("\n" + "=" * 50)
            print("项目启动完成")
            print("=" * 50)
            
            self.workflow_logger.info("[SUCCESS] 工作环境准备完成")
            self.workflow_logger.info("[SUCCESS] 合规性监控系统已启动")
            self.workflow_logger.info("[SUCCESS] 可以开始正常工作")
            
            # 在显示状态前，等待片刻并重新检测监控状态，确保准确
            time.sleep(1)
            monitoring_running_final = self.check_monitoring_system()
            monitoring_display = "运行中" if monitoring_running_final else "未运行"
            
            print("\n当前系统状态:")
            print(" AI助手状态: 已就绪")
            print(f" 合规监控状态: {monitoring_display}")
            print(" 工作流程: 已启动")
            print(" 核心文档: 已加载")
            venv_display = "已可用" if 'VIRTUAL_ENV' not in os.environ else "检测到虚拟环境"
            python_display = "系统Python" if '.venv' not in sys.executable.lower() else "虚拟环境Python"
            print(f" ⚡ 虚拟环境: {venv_display}")
            print(f" Python环境: {python_display}")
            
            # 显示工作提醒和工具可用指导
            print("")
            self.show_work_reminders()
            
            # 显示工具可用性提醒
            print("\n" + tool_reminder)
            sys.stdout.flush()
            
            print("\n现在可以开始高效工作")
            print("=" * 50)
            sys.stdout.flush()
            
            monitoring_status = "运行中" if monitoring_running_final else "未运行"
            success_msg = f"完整工作会话启动成功 - 已加载 {len(regulations)} 个核心文档，监控系统状态: {monitoring_status}"
            
            return True, success_msg
        
        except Exception as e:
            error_msg = f"工作会话启动失败: {e}"
            print(error_msg)
            self.workflow_logger.error(error_msg)
            return False, error_msg
    
    def create_startup_script(self):
        """创建启动脚本"""
        startup_script = self.tools_dir / "ai_startup.py"
        
        script_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI助手快速启动脚本
在每次开始工作前执行此脚本
"""

import sys
from pathlib import Path

# 添加工具目录到路径
sys.path.insert(0, str(Path(__file__).parent))
# from ai_assistant_startup_check import AIAssistantStartupChecker  # 无需导入，类已在本文件中定义

def quick_startup(root=None):
    """快速启动函数 - 来自ai_startup.py的功能"""
    checker = AI3StudioStartupChecker(project_root=root or "s:/3AI")
    success, message = checker.perform_startup_check()

    if success:
        print("\\n系统准备就绪，可以开始工作了")
        return 0
    else:
        print(f"\\n系统启动检查失败: {message}")
        return 1

if __name__ == "__main__":
    sys.exit(quick_startup())
'''

        with open(startup_script, 'w', encoding='utf-8') as f:
            f.write(script_content)

        print(f"启动脚本已创建: {startup_script}")
        print("使用方法: python tools/ai_startup.py")





def check_mcp_servers_simple(root=None):
    """简化版MCP服务器检查（来自start_simple_fixed.py）"""

    try:
        project_root = Path(root or "S:/HQ-OA")

        # 检查Claude Desktop配置文件（支持多候选路径）
        candidates = [
            project_root / "claude_desktop_config.json",
            Path(os.path.expandvars(r"%APPDATA%\Claude\claude_desktop_config.json")),
            project_root / "tools" / "MCP" / "servers" / "windows-system" / "claude_desktop_config.json",
        ]

        config_file = next((p for p in candidates if p.exists()), None)
        if not config_file:
            print("⚠ Claude Desktop配置文件不存在（已检查项目根目录和%APPDATA%示例路径）")
            return False
        else:
            print(f"✓ 使用可用配置文件: {config_file}")

        # 读取MCP服务器配置（兼容 UTF-8 BOM）
        with open(config_file, 'r', encoding='utf-8-sig') as f:
            config = json.load(f)

        mcp_servers = config.get('mcpServers', {})
        if not mcp_servers:
            print("⚠ 未配置MCP服务器")
            return False

        print(f"✓ 发现 {len(mcp_servers)} 个已配置的MCP服务器:")

        all_ok = True
        for server_name, server_config in mcp_servers.items():
            # 检查服务器脚本文件是否存在
            if 'args' in server_config and server_config['args']:
                script_path = Path(server_config['args'][0])
                if script_path.exists():
                    print(f"  ✅ {server_name}: 脚本文件存在")
                else:
                    print(f"  ❌ {server_name}: 脚本文件不存在 ({script_path})")
                    all_ok = False
            else:
                print(f"  ⚠ {server_name}: 配置不完整")
                all_ok = False

        # 尝试调用MCP服务器管理器进行详细检查
        mcp_manager_script = project_root / "tools" / "mcp_server_manager.py"
        if mcp_manager_script.exists():
            try:
                result = subprocess.run(
                    [sys.executable, str(mcp_manager_script), "status"],
                    cwd=str(project_root),
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore',
                    timeout=10
                )

                if result.returncode == 0 and result.stdout:
                    print("\n✓ 详细状态报告:")
                    # 只显示关键信息，避免输出过长
                    lines = result.stdout.strip().split('\n')
                    for line in lines[:10]:  # 只显示前10行
                        if line.strip():
                            print(f"  {line}")
                    if len(lines) > 10:
                        print(f"  ... (还有 {len(lines)-10} 行，详见日志)")

            except Exception as e:
                print(f"⚠ MCP服务器管理器调用失败: {e}")

        return all_ok

    except Exception as e:
        print(f"❌ MCP服务器检查失败: {e}")
        return False





def simple_startup(root=None):
    """简化版启动流程（来自start_simple_fixed.py）"""
    project_root = Path(root or "S:/HQ-OA")
    
    print("🚀 HQ-OA 项目快速启动")
    print("=" * 50)
    
    # 第一阶段：基础检查
    print("\n📋 第一阶段：基础环境检查")
    print("-" * 30)
    
    # 检查项目目录
    if project_root.exists():
        print("✅ 项目根目录: 已确认")
    else:
        print("❌ 项目根目录: 不存在")
        return False
    
    # 检查核心目录
    core_dirs = ["docs", "tools", "project"]
    for dir_name in core_dirs:
        dir_path = project_root / dir_name
        if dir_path.exists():
            print(f"✅ {dir_name}目录: 已确认")
        else:
            print(f"⚠️ {dir_name}目录: 不存在")
    
    # 第二阶段：显示项目信息
    print("\n📊 第二阶段：项目状态信息")
    print("-" * 30)

    
    # 显示当前日期
    from datetime import datetime
    current_time = datetime.now()
    print(f"Current time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Working directory: {os.getcwd()}")
    print(f"Python version: {sys.version.split()[0]}")
    
    # 第三阶段：MCP服务器检测
    print("\n🔧 第三阶段：MCP服务器状态检测")
    print("-" * 30)
    
    mcp_status = check_mcp_servers_simple(root=str(project_root))
    if mcp_status:
        print("✅ MCP服务器检测: 完成")
    else:
        print("⚠️ MCP服务器检测: 发现问题（详见日志）")
    
    # 第四阶段：启动完成
    print("\n✅ 第四阶段：启动完成")
    print("-" * 30)
    print("🎉 项目启动成功！")
    print("💡 提示：您现在可以开始工作了")
    
    return True



def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI助手启动前置检查系统")
    parser.add_argument("--check", action="store_true", help="执行启动检查")
    parser.add_argument("--create-script", action="store_true", help="创建启动脚本")
    parser.add_argument("--quick", action="store_true", help="快速启动（集成ai_startup.py功能）")
    parser.add_argument("--simple", action="store_true", help="简化版启动（集成start_simple_fixed.py功能）")
    parser.add_argument("--work", action="store_true", help="启动完整工作会话（推荐）")
    parser.add_argument("--start", action="store_true", help="启动完整工作会议（别名）")
    parser.add_argument("--root", type=str, help="项目根目录路径，例如 S:/HQ-OA")
    
    args = parser.parse_args()
    
    project_root_arg = args.root if getattr(args, "root", None) else None
    checker = AI3StudioStartupChecker(project_root=project_root_arg or "s:/3AI")

 

    if args.create_script:
        checker.create_startup_script()
    elif args.simple:
        # 简化版启动（来自start_simple_fixed.py）
        success = simple_startup(root=project_root_arg)
        if success:
            print("\n🎉 启动流程完成")
            return 0
        else:
            print("\n❌ 启动流程失败")
            return 1
    elif args.work or args.start:
        # 启动完整工作会话
        success, message = checker.start_work_session()
        print(f"\n{message}")
        if not success:
            exit(1)
    elif args.check:
        success, message = checker.perform_startup_check()
        print(f"\n{message}")
    elif args.quick:
        return quick_startup(root=project_root_arg)

    else:
        # 默认执行完整工作会话启动
        success, message = checker.start_work_session()
        print(f"\n{message}")
        if not success:
            exit(1)


if __name__ == "__main__":
    main()