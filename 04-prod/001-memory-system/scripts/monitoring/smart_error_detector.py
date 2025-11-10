#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能错误检测系统
主动监控开发过程中的错误模式，并提供实时预警和建议
"""

import json
import os
import time
import threading
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import hashlib

# 文件锁用于避免并发读写导致的 JSON 文件损坏
try:
    from file_lock import FileLock
except Exception:
    try:
        from .file_lock import FileLock
    except Exception:
        FileLock = None

class ErrorPattern:
    """错误模式类"""
    def __init__(self, pattern_id: str, name: str, triggers: List[str], 
                 suggestion: str, severity: str = "medium"):
        self.pattern_id = pattern_id
        self.name = name
        self.triggers = triggers
        self.suggestion = suggestion
        self.severity = severity
        self.occurrence_count = 0
        self.last_occurrence = None

class CodeAnalyzer:
    """代码分析器"""
    
    def __init__(self):
        self.common_errors = [
            r"SyntaxError",
            r"IndentationError", 
            r"NameError",
            r"TypeError",
            r"AttributeError",
            r"ImportError",
            r"KeyError",
            r"ValueError"
        ]
        
        self.suspicious_patterns = [
            r"print\s*\(",  # 调试print语句
            r"TODO|FIXME|HACK",  # 待办事项标记
            r"import\s+\*",  # 危险的import *
            r"eval\s*\(",  # 危险的eval函数
            r"exec\s*\(",  # 危险的exec函数
        ]
    
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """分析单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            issues = []
            
            # 检查常见错误模式
            for error_pattern in self.common_errors:
                matches = re.findall(error_pattern, content, re.IGNORECASE)
                if matches:
                    issues.append({
                        "type": "potential_error",
                        "pattern": error_pattern,
                        "count": len(matches),
                        "severity": "high"
                    })
            
            # 检查可疑模式
            for suspicious_pattern in self.suspicious_patterns:
                matches = re.findall(suspicious_pattern, content, re.IGNORECASE)
                if matches:
                    issues.append({
                        "type": "suspicious_code",
                        "pattern": suspicious_pattern,
                        "count": len(matches),
                        "severity": "medium"
                    })
            
            return {
                "file_path": file_path,
                "analysis_time": datetime.now().isoformat(),
                "issues": issues,
                "file_hash": hashlib.md5(content.encode()).hexdigest()
            }
            
        except Exception as e:
            return {
                "file_path": file_path,
                "analysis_time": datetime.now().isoformat(),
                "error": str(e),
                "issues": []
            }

class BehaviorMonitor:
    """行为模式监控器"""
    
    def __init__(self):
        self.file_modifications = {}
        self.error_sequences = []
        self.suspicious_behaviors = []
    
    def track_file_modification(self, file_path: str):
        """跟踪文件修改"""
        now = datetime.now()
        
        if file_path not in self.file_modifications:
            self.file_modifications[file_path] = []
        
        self.file_modifications[file_path].append(now)
        
        # 检查频繁修改模式（5分钟内修改超过5次）
        recent_modifications = [
            mod_time for mod_time in self.file_modifications[file_path]
            if now - mod_time < timedelta(minutes=5)
        ]
        
        if len(recent_modifications) > 5:
            self.suspicious_behaviors.append({
                "type": "frequent_modification",
                "file_path": file_path,
                "count": len(recent_modifications),
                "time_window": "5_minutes",
                "timestamp": now.isoformat(),
                "severity": "medium"
            })
    
    def track_error_sequence(self, error_type: str, context: Dict[str, Any]):
        """跟踪错误序列"""
        error_event = {
            "error_type": error_type,
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
        
        self.error_sequences.append(error_event)
        
        # 保持最近100个错误记录
        if len(self.error_sequences) > 100:
            self.error_sequences = self.error_sequences[-100:]
        
        # 检查重复错误模式
        self._detect_repeated_errors()
    
    def _detect_repeated_errors(self):
        """检测重复错误模式"""
        if len(self.error_sequences) < 3:
            return
        
        recent_errors = self.error_sequences[-10:]  # 最近10个错误
        error_types = [error["error_type"] for error in recent_errors]
        
        # 检查是否有相同错误类型重复出现
        for error_type in set(error_types):
            count = error_types.count(error_type)
            if count >= 3:
                self.suspicious_behaviors.append({
                    "type": "repeated_error",
                    "error_type": error_type,
                    "count": count,
                    "timestamp": datetime.now().isoformat(),
                    "severity": "high"
                })

class SmartErrorDetector:
    """智能错误检测器主类"""
    
    def __init__(self, config_path: str = None):
        # 统一为仓库内 tools/LongMemory 下的配置；memory_path 由上层服务注入
        self.config_path = config_path or "tools/LongMemory/smart_detector_config.json"
        # 优先环境变量，其次公司级规范路径（避免误写到仓库根 logs/longmemory）
        self.memory_path = os.environ.get("YDS_LONGMEMORY_STORAGE_PATH") or \
                           os.environ.get("LONGMEMORY_PATH") or \
                           "01-struc/logs/longmemory/lm_records.json"
        self.patterns_path = "tools/LongMemory/error_patterns.json"
        
        self.code_analyzer = CodeAnalyzer()
        self.behavior_monitor = BehaviorMonitor()
        self.error_patterns = []
        self.active_alerts = []
        
        self.load_config()
        self.load_error_patterns()
        
        self.monitoring = False
        self.monitor_thread = None
    
    def load_config(self):
        """加载配置"""
        default_config = {
            "enabled": True,
            "real_time_detection": True,
            "notification_methods": ["console", "file"],
            "monitoring_interval": 30,
            "project_root": "s:/3AI",
            "monitored_extensions": [".py", ".js", ".ts", ".json", ".md"],
            "alert_thresholds": {
                "frequent_modification": 5,
                "repeated_error": 3,
                "suspicious_code": 2
            }
        }
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            else:
                self.config = default_config
                self.save_config()
        except Exception as e:
            print(f"❌ 配置加载失败，使用默认配置: {e}")
            self.config = default_config
    
    def save_config(self):
        """保存配置"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ 配置保存失败: {e}")
    
    def load_error_patterns(self):
        """加载错误模式"""
        default_patterns = [
            {
                "pattern_id": "frequent_file_modification",
                "name": "频繁文件修改",
                "triggers": ["file_modification_count > 5", "time_window < 5_minutes"],
                "suggestion": "频繁修改同一文件可能表明设计存在问题，建议重新审视代码结构",
                "severity": "medium"
            },
            {
                "pattern_id": "repeated_same_error",
                "name": "重复相同错误",
                "triggers": ["same_error_type", "occurrence_count >= 3"],
                "suggestion": "重复出现相同错误，建议查看历史解决方案或寻求帮助",
                "severity": "high"
            },
            {
                "pattern_id": "suspicious_code_patterns",
                "name": "可疑代码模式",
                "triggers": ["debug_prints", "todo_comments", "dangerous_functions"],
                "suggestion": "发现可疑代码模式，建议进行代码审查",
                "severity": "low"
            }
        ]
        
        try:
            if os.path.exists(self.patterns_path):
                with open(self.patterns_path, 'r', encoding='utf-8') as f:
                    patterns_data = json.load(f)
            else:
                patterns_data = {"patterns": default_patterns}
                self.save_error_patterns(patterns_data)
            
            self.error_patterns = []
            for pattern_data in patterns_data.get("patterns", []):
                pattern = ErrorPattern(
                    pattern_data["pattern_id"],
                    pattern_data["name"],
                    pattern_data["triggers"],
                    pattern_data["suggestion"],
                    pattern_data.get("severity", "medium")
                )
                self.error_patterns.append(pattern)
                
        except Exception as e:
            print(f"❌ 错误模式加载失败: {e}")
    
    def save_error_patterns(self, patterns_data: Dict[str, Any]):
        """保存错误模式"""
        try:
            with open(self.patterns_path, 'w', encoding='utf-8') as f:
                json.dump(patterns_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ 错误模式保存失败: {e}")
    
    def start_monitoring(self):
        """开始监控"""
        if self.monitoring:
            print("⚠️ 监控已在运行中")
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        print("🚀 智能错误检测系统已启动")
        print(f"📁 项目根目录: {self.config['project_root']}")
        print(f"⏱️ 监控间隔: {self.config['monitoring_interval']}秒")
        print(f"📋 监控文件类型: {', '.join(self.config['monitored_extensions'])}")
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        print("🛑 智能错误检测系统已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            try:
                self._scan_project_files()
                self._analyze_behavior_patterns()
                self._check_alert_conditions()
                time.sleep(self.config['monitoring_interval'])
            except Exception as e:
                print(f"❌ 监控循环错误: {e}")
                time.sleep(5)
    
    def _scan_project_files(self):
        """扫描项目文件"""
        project_root = Path(self.config['project_root'])
        monitored_extensions = self.config['monitored_extensions']
        
        for ext in monitored_extensions:
            for file_path in project_root.rglob(f"*{ext}"):
                if file_path.is_file() and not self._should_ignore_file(str(file_path)):
                    # 检查文件是否最近被修改
                    if self._is_recently_modified(file_path):
                        self.behavior_monitor.track_file_modification(str(file_path))
                        
                        # 分析代码质量
                        if ext == '.py':
                            analysis = self.code_analyzer.analyze_file(str(file_path))
                            if analysis.get('issues'):
                                self._handle_code_issues(analysis)
    
    def _should_ignore_file(self, file_path: str) -> bool:
        """判断是否应该忽略文件"""
        ignore_patterns = [
            r'\\\.git\\',
            r'\\__pycache__\\',
            r'\\node_modules\\',
            r'\\\.venv\\',
            r'\\logs\\',
            r'\\\.pytest_cache\\'
        ]
        
        for pattern in ignore_patterns:
            if re.search(pattern, file_path):
                return True
        return False
    
    def _is_recently_modified(self, file_path: Path) -> bool:
        """检查文件是否最近被修改"""
        try:
            mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            return datetime.now() - mod_time < timedelta(minutes=5)
        except:
            return False
    
    def _handle_code_issues(self, analysis: Dict[str, Any]):
        """处理代码问题"""
        for issue in analysis.get('issues', []):
            if issue['severity'] == 'high':
                self._create_alert(
                    "代码质量警告",
                    f"在文件 {analysis['file_path']} 中发现 {issue['type']}: {issue['pattern']}",
                    "high",
                    {
                        "file_path": analysis['file_path'],
                        "issue_type": issue['type'],
                        "pattern": issue['pattern']
                    }
                )
    
    def _analyze_behavior_patterns(self):
        """分析行为模式"""
        # 检查可疑行为
        for behavior in self.behavior_monitor.suspicious_behaviors:
            if behavior['type'] == 'frequent_modification':
                self._create_alert(
                    "频繁文件修改警告",
                    f"文件 {behavior['file_path']} 在5分钟内被修改了 {behavior['count']} 次",
                    behavior['severity'],
                    behavior
                )
            elif behavior['type'] == 'repeated_error':
                self._create_alert(
                    "重复错误警告",
                    f"错误类型 {behavior['error_type']} 重复出现了 {behavior['count']} 次",
                    behavior['severity'],
                    behavior
                )
        
        # 清空已处理的可疑行为
        self.behavior_monitor.suspicious_behaviors = []
    
    def _check_alert_conditions(self):
        """检查警报条件"""
        # 这里可以添加更复杂的警报逻辑
        pass
    
    def _create_alert(self, title: str, message: str, severity: str, context: Dict[str, Any]):
        """创建警报"""
        alert = {
            "id": hashlib.md5(f"{title}{message}{datetime.now()}".encode()).hexdigest()[:8],
            "title": title,
            "message": message,
            "severity": severity,
            "context": context,
            "timestamp": datetime.now().isoformat(),
            "acknowledged": False
        }
        
        self.active_alerts.append(alert)
        self._send_notification(alert)
        self._log_alert(alert)
    
    def _send_notification(self, alert: Dict[str, Any]):
        """发送通知"""
        methods = self.config.get('notification_methods', ['console'])
        
        if 'console' in methods:
            severity_icon = {"low": "ℹ️", "medium": "⚠️", "high": "🚨"}
            icon = severity_icon.get(alert['severity'], "⚠️")
            print(f"\n{icon} 【智能错误检测】{alert['title']}")
            print(f"   📄 {alert['message']}")
            print(f"   ⏰ {alert['timestamp']}")
            print(f"   🆔 警报ID: {alert['id']}")
    
    def _log_alert(self, alert: Dict[str, Any]):
        """记录警报到长记忆系统"""
        try:
            if FileLock:
                with FileLock(self.memory_path):
                    # 读取现有记忆数据
                    if os.path.exists(self.memory_path):
                        with open(self.memory_path, 'r', encoding='utf-8') as f:
                            memory_data = json.load(f)
                    else:
                        memory_data = {"general": {}, "memories": []}
                    
                    # 添加警报记录
                    alert_key = f"smart_alert_{int(datetime.now().timestamp())}"
                    memory_data["general"][alert_key] = {
                        "timestamp": alert['timestamp'],
                        "type": "smart_error_alert",
                        "data": alert
                    }

                    # 同步追加到 memories 数组（TraeLM 兼容结构）
                    try:
                        sev = str(alert.get('severity', 'medium')).lower()
                        importance_map = {"low": 0.4, "medium": 0.6, "high": 0.8}
                        importance = importance_map.get(sev, 0.6)
                        content = f"[Alert][{sev}] {alert.get('title','')} - {alert.get('message','')}"
                        memory_entry = {
                            "id": f"mem_{int(datetime.now().timestamp()*1000)}",
                            "content": content,
                            "summary": alert.get('message', ''),
                            "type": "episodic",  # 警报属于情景事件
                            "importance": importance,
                            "tags": ["smart_error_alert", sev],
                            "context": alert.get('context', {}),
                            "metadata": {
                                "source": "SmartErrorDetector",
                                "alertId": alert.get('id'),
                                "severity": sev
                            },
                            "createdAt": alert.get('timestamp', datetime.now().isoformat()),
                            "updatedAt": alert.get('timestamp', datetime.now().isoformat())
                        }
                        if "memories" not in memory_data or not isinstance(memory_data.get("memories"), list):
                            memory_data["memories"] = []
                        memory_data["memories"].append(memory_entry)
                    except Exception:
                        pass

                    # 确保目录存在并原子写入
                    os.makedirs(os.path.dirname(self.memory_path), exist_ok=True)
                    tmp_path = f"{self.memory_path}.tmp"
                    with open(tmp_path, 'w', encoding='utf-8') as f:
                        json.dump(memory_data, f, ensure_ascii=False, indent=2)
                    os.replace(tmp_path, self.memory_path)
            else:
                if os.path.exists(self.memory_path):
                    with open(self.memory_path, 'r', encoding='utf-8') as f:
                        memory_data = json.load(f)
                else:
                    memory_data = {"general": {}, "memories": []}
                
                # 添加警报记录
                alert_key = f"smart_alert_{int(datetime.now().timestamp())}"
                memory_data["general"][alert_key] = {
                    "timestamp": alert['timestamp'],
                    "type": "smart_error_alert",
                    "data": alert
                }
                # 同步追加到 memories 数组
                try:
                    sev = str(alert.get('severity', 'medium')).lower()
                    importance_map = {"low": 0.4, "medium": 0.6, "high": 0.8}
                    importance = importance_map.get(sev, 0.6)
                    content = f"[Alert][{sev}] {alert.get('title','')} - {alert.get('message','')}"
                    memory_entry = {
                        "id": f"mem_{int(datetime.now().timestamp()*1000)}",
                        "content": content,
                        "summary": alert.get('message', ''),
                        "type": "episodic",
                        "importance": importance,
                        "tags": ["smart_error_alert", sev],
                        "context": alert.get('context', {}),
                        "metadata": {
                            "source": "SmartErrorDetector",
                            "alertId": alert.get('id'),
                            "severity": sev
                        },
                        "createdAt": alert.get('timestamp', datetime.now().isoformat()),
                        "updatedAt": alert.get('timestamp', datetime.now().isoformat())
                    }
                    if "memories" not in memory_data or not isinstance(memory_data.get("memories"), list):
                        memory_data["memories"] = []
                    memory_data["memories"].append(memory_entry)
                except Exception:
                    pass
                
                os.makedirs(os.path.dirname(self.memory_path), exist_ok=True)
                with open(self.memory_path, 'w', encoding='utf-8') as f:
                    json.dump(memory_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"❌ 警报记录失败: {e}")
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """获取活跃警报"""
        return [alert for alert in self.active_alerts if not alert['acknowledged']]
    
    def acknowledge_alert(self, alert_id: str):
        """确认警报"""
        for alert in self.active_alerts:
            if alert['id'] == alert_id:
                alert['acknowledged'] = True
                print(f"✅ 警报 {alert_id} 已确认")
                return True
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_alerts": len(self.active_alerts),
            "active_alerts": len(self.get_active_alerts()),
            "alert_by_severity": {
                "high": len([a for a in self.active_alerts if a['severity'] == 'high']),
                "medium": len([a for a in self.active_alerts if a['severity'] == 'medium']),
                "low": len([a for a in self.active_alerts if a['severity'] == 'low'])
            },
            "monitoring_status": "running" if self.monitoring else "stopped"
        }

def main():
    """主函数"""
    print("🧠 智能错误检测系统")
    print("=" * 50)
    
    detector = SmartErrorDetector()
    
    try:
        detector.start_monitoring()
        
        # 运行一段时间进行测试
        print("🔍 开始监控，按 Ctrl+C 停止...")
        while True:
            time.sleep(10)
            stats = detector.get_statistics()
            if stats['active_alerts'] > 0:
                print(f"📊 当前活跃警报: {stats['active_alerts']} 个")
                
    except KeyboardInterrupt:
        print("\n🛑 收到停止信号")
    finally:
        detector.stop_monitoring()
        print("👋 智能错误检测系统已退出")

if __name__ == "__main__":
    main()