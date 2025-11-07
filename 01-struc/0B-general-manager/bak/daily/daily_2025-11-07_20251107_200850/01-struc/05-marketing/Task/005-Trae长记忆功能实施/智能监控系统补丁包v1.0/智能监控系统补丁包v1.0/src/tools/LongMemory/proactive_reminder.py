#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主动提醒系统
基于历史经验和最佳实践，在开发过程中主动提供建议和提醒
"""

import json
import os
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import re
import hashlib

class KnowledgeBase:
    """知识库类"""
    
    def __init__(self):
        self.best_practices = {}
        self.common_mistakes = {}
        self.solution_patterns = {}
        self.load_knowledge()
    
    def load_knowledge(self):
        """加载知识库"""
        self.best_practices = {
            "python": [
                {
                    "trigger": r"def\s+\w+\([^)]*\):",
                    "suggestion": "建议为函数添加类型注解和文档字符串",
                    "example": "def function_name(param: str) -> str:\n    \"\"\"函数说明\"\"\""
                },
                {
                    "trigger": r"print\s*\(",
                    "suggestion": "生产代码中避免使用print，建议使用logging模块",
                    "example": "import logging\nlogging.info('信息内容')"
                },
                {
                    "trigger": r"except\s*:",
                    "suggestion": "避免使用裸露的except，应指定具体的异常类型",
                    "example": "except ValueError as e:"
                }
            ],
            "javascript": [
                {
                    "trigger": r"var\s+\w+",
                    "suggestion": "建议使用let或const替代var",
                    "example": "const variableName = value;"
                },
                {
                    "trigger": r"==\s*",
                    "suggestion": "建议使用===进行严格比较",
                    "example": "if (value === expectedValue)"
                }
            ]
        }
        
        self.common_mistakes = {
            "indentation_error": {
                "pattern": r"IndentationError",
                "suggestion": "Python缩进错误，检查代码块的缩进是否一致",
                "prevention": "使用IDE的自动格式化功能，设置显示空白字符"
            },
            "name_error": {
                "pattern": r"NameError.*'(\w+)'.*not defined",
                "suggestion": "变量未定义错误，检查变量名拼写和作用域",
                "prevention": "声明变量前先检查是否已定义，使用IDE的变量检查功能"
            },
            "import_error": {
                "pattern": r"ImportError|ModuleNotFoundError",
                "suggestion": "模块导入错误，检查模块是否已安装或路径是否正确",
                "prevention": "使用虚拟环境管理依赖，定期更新requirements.txt"
            }
        }
        
        self.solution_patterns = {
            "file_not_found": [
                "检查文件路径是否正确",
                "确认文件是否存在",
                "使用os.path.exists()验证文件存在性",
                "考虑使用相对路径或绝对路径"
            ],
            "permission_denied": [
                "检查文件权限设置",
                "确认当前用户是否有访问权限",
                "尝试以管理员身份运行",
                "检查文件是否被其他程序占用"
            ],
            "connection_error": [
                "检查网络连接",
                "验证URL或端点是否正确",
                "检查防火墙设置",
                "添加重试机制和超时设置"
            ]
        }

class ContextAnalyzer:
    """上下文分析器"""
    
    def __init__(self):
        self.current_context = {}
        self.recent_activities = []
        self.error_history = []
    
    def update_context(self, activity_type: str, details: Dict[str, Any]):
        """更新当前上下文"""
        activity = {
            "type": activity_type,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        
        self.recent_activities.append(activity)
        
        # 保持最近50个活动记录
        if len(self.recent_activities) > 50:
            self.recent_activities = self.recent_activities[-50:]
        
        # 更新当前上下文
        self.current_context[activity_type] = details
    
    def add_error(self, error_type: str, error_message: str, context: Dict[str, Any]):
        """添加错误记录"""
        error_record = {
            "error_type": error_type,
            "error_message": error_message,
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
        
        self.error_history.append(error_record)
        
        # 保持最近100个错误记录
        if len(self.error_history) > 100:
            self.error_history = self.error_history[-100:]
    
    def get_similar_errors(self, error_type: str, limit: int = 5) -> List[Dict[str, Any]]:
        """获取相似的历史错误"""
        similar_errors = [
            error for error in self.error_history
            if error['error_type'] == error_type
        ]
        
        # 按时间倒序排列，返回最近的错误
        similar_errors.sort(key=lambda x: x['timestamp'], reverse=True)
        return similar_errors[:limit]
    
    def analyze_current_situation(self) -> Dict[str, Any]:
        """分析当前情况"""
        recent_errors = [
            activity for activity in self.recent_activities[-10:]
            if activity['type'] == 'error'
        ]
        
        recent_files = [
            activity['details'].get('file_path')
            for activity in self.recent_activities[-10:]
            if activity['type'] == 'file_modification' and 'file_path' in activity['details']
        ]
        
        return {
            "recent_error_count": len(recent_errors),
            "recent_error_types": [error['details'].get('error_type') for error in recent_errors],
            "active_files": list(set(recent_files)),
            "current_focus": self._determine_current_focus()
        }
    
    def _determine_current_focus(self) -> str:
        """确定当前关注点"""
        recent_activities = self.recent_activities[-5:]
        
        if not recent_activities:
            return "unknown"
        
        activity_types = [activity['type'] for activity in recent_activities]
        
        if 'error' in activity_types:
            return "debugging"
        elif 'file_modification' in activity_types:
            return "coding"
        elif 'test_run' in activity_types:
            return "testing"
        else:
            return "general"

class ProactiveReminder:
    """主动提醒系统主类"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or "s:/3AI/tools/LongMemory/reminder_config.json"
        self.memory_path = "s:/3AI/docs/02-开发/memory.json"
        
        self.knowledge_base = KnowledgeBase()
        self.context_analyzer = ContextAnalyzer()
        
        self.active_reminders = []
        self.reminder_history = []
        
        self.load_config()
        self.load_memory_data()
        
        self.monitoring = False
        self.monitor_thread = None
    
    def load_config(self):
        """加载配置"""
        default_config = {
            "enabled": True,
            "reminder_interval": 60,  # 秒
            "max_active_reminders": 5,
            "reminder_types": {
                "best_practice": True,
                "error_prevention": True,
                "historical_solution": True,
                "code_quality": True
            },
            "notification_methods": ["console", "popup"],
            "learning_mode": True
        }
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            else:
                self.config = default_config
                self.save_config()
        except Exception as e:
            print(f"❌ 配置加载失败: {e}")
            self.config = default_config
    
    def save_config(self):
        """保存配置"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ 配置保存失败: {e}")
    
    def load_memory_data(self):
        """加载记忆数据"""
        try:
            if os.path.exists(self.memory_path):
                with open(self.memory_path, 'r', encoding='utf-8') as f:
                    memory_data = json.load(f)
                
                # 从记忆中加载历史错误和解决方案
                for key, value in memory_data.get("general", {}).items():
                    if value.get("type") == "error_record":
                        self.context_analyzer.add_error(
                            value["data"]["error_type"],
                            value["data"]["error_message"],
                            value["data"]["context"]
                        )
        except Exception as e:
            print(f"❌ 记忆数据加载失败: {e}")
    
    def start_monitoring(self):
        """开始监控"""
        if self.monitoring:
            print("⚠️ 主动提醒系统已在运行中")
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        print("🤖 主动提醒系统已启动")
        print(f"⏱️ 提醒间隔: {self.config['reminder_interval']}秒")
        print(f"📋 启用的提醒类型: {[k for k, v in self.config['reminder_types'].items() if v]}")
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        print("🛑 主动提醒系统已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            try:
                self._analyze_and_remind()
                time.sleep(self.config['reminder_interval'])
            except Exception as e:
                print(f"❌ 监控循环错误: {e}")
                time.sleep(5)
    
    def _analyze_and_remind(self):
        """分析并提醒"""
        situation = self.context_analyzer.analyze_current_situation()
        
        # 根据当前情况生成提醒
        if situation['current_focus'] == 'debugging':
            self._generate_debugging_reminders(situation)
        elif situation['current_focus'] == 'coding':
            self._generate_coding_reminders(situation)
        elif situation['recent_error_count'] > 0:
            self._generate_error_prevention_reminders(situation)
        
        # 清理过期的提醒
        self._cleanup_expired_reminders()
    
    def _generate_debugging_reminders(self, situation: Dict[str, Any]):
        """生成调试相关提醒"""
        if not self.config['reminder_types']['historical_solution']:
            return
        
        for error_type in situation['recent_error_types']:
            if error_type:
                similar_errors = self.context_analyzer.get_similar_errors(error_type)
                if similar_errors:
                    self._create_reminder(
                        "历史解决方案",
                        f"检测到 {error_type} 错误，您之前遇到过 {len(similar_errors)} 次类似问题",
                        "historical_solution",
                        {
                            "error_type": error_type,
                            "similar_count": len(similar_errors),
                            "suggestions": self._get_error_solutions(error_type)
                        }
                    )
    
    def _generate_coding_reminders(self, situation: Dict[str, Any]):
        """生成编码相关提醒"""
        if not self.config['reminder_types']['best_practice']:
            return
        
        for file_path in situation['active_files']:
            if file_path and file_path.endswith('.py'):
                self._check_python_best_practices(file_path)
    
    def _generate_error_prevention_reminders(self, situation: Dict[str, Any]):
        """生成错误预防提醒"""
        if not self.config['reminder_types']['error_prevention']:
            return
        
        error_types = situation['recent_error_types']
        common_errors = [error for error in error_types if error in self.knowledge_base.common_mistakes]
        
        for error_type in common_errors:
            mistake_info = self.knowledge_base.common_mistakes[error_type]
            self._create_reminder(
                "错误预防建议",
                f"最近出现了 {error_type}，{mistake_info['suggestion']}",
                "error_prevention",
                {
                    "error_type": error_type,
                    "prevention_tip": mistake_info['prevention']
                }
            )
    
    def _check_python_best_practices(self, file_path: str):
        """检查Python最佳实践"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for practice in self.knowledge_base.best_practices.get('python', []):
                if re.search(practice['trigger'], content):
                    self._create_reminder(
                        "最佳实践建议",
                        f"在 {os.path.basename(file_path)} 中：{practice['suggestion']}",
                        "best_practice",
                        {
                            "file_path": file_path,
                            "suggestion": practice['suggestion'],
                            "example": practice['example']
                        }
                    )
        except Exception as e:
            pass  # 忽略文件读取错误
    
    def _get_error_solutions(self, error_type: str) -> List[str]:
        """获取错误解决方案"""
        # 从知识库中获取解决方案
        for pattern_key, solutions in self.knowledge_base.solution_patterns.items():
            if pattern_key.lower() in error_type.lower():
                return solutions
        
        # 默认通用建议
        return [
            "检查错误信息的详细描述",
            "查看相关文档或搜索解决方案",
            "尝试简化问题，逐步调试",
            "考虑回滚到上一个工作版本"
        ]
    
    def _create_reminder(self, title: str, message: str, reminder_type: str, context: Dict[str, Any]):
        """创建提醒"""
        # 检查是否已存在相似提醒
        if self._has_similar_reminder(title, message):
            return
        
        # 检查活跃提醒数量限制
        if len(self.active_reminders) >= self.config['max_active_reminders']:
            # 移除最旧的提醒
            self.active_reminders.pop(0)
        
        reminder = {
            "id": hashlib.md5(f"{title}{message}{datetime.now()}".encode()).hexdigest()[:8],
            "title": title,
            "message": message,
            "type": reminder_type,
            "context": context,
            "timestamp": datetime.now().isoformat(),
            "acknowledged": False,
            "expires_at": (datetime.now() + timedelta(hours=1)).isoformat()
        }
        
        self.active_reminders.append(reminder)
        self._send_notification(reminder)
        self._log_reminder(reminder)
    
    def _has_similar_reminder(self, title: str, message: str) -> bool:
        """检查是否存在相似提醒"""
        for reminder in self.active_reminders:
            if reminder['title'] == title and reminder['message'] == message:
                return True
        return False
    
    def _cleanup_expired_reminders(self):
        """清理过期提醒"""
        now = datetime.now()
        self.active_reminders = [
            reminder for reminder in self.active_reminders
            if datetime.fromisoformat(reminder['expires_at']) > now
        ]
    
    def _send_notification(self, reminder: Dict[str, Any]):
        """发送通知"""
        methods = self.config.get('notification_methods', ['console'])
        
        if 'console' in methods:
            print(f"\n💡 【主动提醒】{reminder['title']}")
            print(f"   📝 {reminder['message']}")
            print(f"   ⏰ {reminder['timestamp']}")
            print(f"   🆔 提醒ID: {reminder['id']}")
            
            # 显示上下文信息
            if reminder['context']:
                if 'suggestions' in reminder['context']:
                    print("   💭 建议解决方案:")
                    for i, suggestion in enumerate(reminder['context']['suggestions'][:3], 1):
                        print(f"      {i}. {suggestion}")
                
                if 'example' in reminder['context']:
                    print(f"   📋 示例: {reminder['context']['example']}")
    
    def _log_reminder(self, reminder: Dict[str, Any]):
        """记录提醒到记忆系统"""
        try:
            if os.path.exists(self.memory_path):
                with open(self.memory_path, 'r', encoding='utf-8') as f:
                    memory_data = json.load(f)
            else:
                memory_data = {"general": {}, "memories": []}
            
            # 添加提醒记录
            reminder_key = f"proactive_reminder_{int(datetime.now().timestamp())}"
            memory_data["general"][reminder_key] = {
                "timestamp": reminder['timestamp'],
                "type": "proactive_reminder",
                "data": reminder
            }
            
            # 保存记忆数据
            with open(self.memory_path, 'w', encoding='utf-8') as f:
                json.dump(memory_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"❌ 提醒记录失败: {e}")
    
    def report_activity(self, activity_type: str, details: Dict[str, Any]):
        """报告活动（供外部调用）"""
        self.context_analyzer.update_context(activity_type, details)
    
    def report_error(self, error_type: str, error_message: str, context: Dict[str, Any]):
        """报告错误（供外部调用）"""
        self.context_analyzer.add_error(error_type, error_message, context)
    
    def get_active_reminders(self) -> List[Dict[str, Any]]:
        """获取活跃提醒"""
        return [reminder for reminder in self.active_reminders if not reminder['acknowledged']]
    
    def acknowledge_reminder(self, reminder_id: str):
        """确认提醒"""
        for reminder in self.active_reminders:
            if reminder['id'] == reminder_id:
                reminder['acknowledged'] = True
                print(f"✅ 提醒 {reminder_id} 已确认")
                return True
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_reminders": len(self.active_reminders),
            "active_reminders": len(self.get_active_reminders()),
            "reminder_by_type": {
                reminder_type: len([r for r in self.active_reminders if r['type'] == reminder_type])
                for reminder_type in self.config['reminder_types'].keys()
            },
            "monitoring_status": "running" if self.monitoring else "stopped"
        }

def main():
    """主函数"""
    print("🤖 主动提醒系统")
    print("=" * 50)
    
    reminder = ProactiveReminder()
    
    try:
        reminder.start_monitoring()
        
        # 模拟一些活动
        print("🔍 模拟开发活动...")
        reminder.report_activity("file_modification", {"file_path": "s:/3AI/test.py"})
        reminder.report_error("NameError", "name 'variable' is not defined", {"file": "test.py", "line": 10})
        
        print("🔍 开始监控，按 Ctrl+C 停止...")
        while True:
            time.sleep(10)
            stats = reminder.get_statistics()
            if stats['active_reminders'] > 0:
                print(f"📊 当前活跃提醒: {stats['active_reminders']} 个")
                
    except KeyboardInterrupt:
        print("\n🛑 收到停止信号")
    finally:
        reminder.stop_monitoring()
        print("👋 主动提醒系统已退出")

if __name__ == "__main__":
    main()