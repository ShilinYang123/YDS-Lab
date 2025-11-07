#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能监控系统
集成错误检测和主动提醒功能，提供全面的开发过程监控和指导
"""

import json
import os
import time
import threading
import signal
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

# 文件锁用于避免并发读写导致的 JSON 文件损坏
try:
    from file_lock import FileLock
except Exception:
    try:
        from .file_lock import FileLock
    except Exception:
        FileLock = None

# 导入自定义模块
try:
    from smart_error_detector import SmartErrorDetector
    from proactive_reminder import ProactiveReminder
except ImportError:
    print("❌ 无法导入依赖模块，请确保 smart_error_detector.py 和 proactive_reminder.py 在同一目录")
    sys.exit(1)

class LearningEngine:
    """学习引擎 - 从历史数据中学习并改进检测能力"""
    
    def __init__(self, memory_path: str):
        self.memory_path = memory_path
        self.learned_patterns = {}
        self.success_patterns = {}
        self.failure_patterns = {}
        
        self.load_learning_data()
    
    def load_learning_data(self):
        """加载学习数据"""
        try:
            if os.path.exists(self.memory_path):
                if FileLock:
                    with FileLock(self.memory_path):
                        with open(self.memory_path, 'r', encoding='utf-8') as f:
                            memory_data = json.load(f)
                else:
                    with open(self.memory_path, 'r', encoding='utf-8') as f:
                        memory_data = json.load(f)
                
                # 分析历史数据，提取模式
                self._analyze_historical_data(memory_data)
        except Exception as e:
            print(f"❌ 学习数据加载失败: {e}")
    
    def _analyze_historical_data(self, memory_data: Dict[str, Any]):
        """分析历史数据"""
        general_data = memory_data.get("general", {})
        
        # 分析错误模式
        error_records = [
            (key, value) for key, value in general_data.items()
            if value.get("type") in ["error_record", "smart_error_alert"]
        ]
        
        # 分析成功模式
        success_records = [
            (key, value) for key, value in general_data.items()
            if value.get("type") == "task_completion"
        ]
        
        # 提取模式
        self._extract_error_patterns(error_records)
        self._extract_success_patterns(success_records)
    
    def _extract_error_patterns(self, error_records: List[tuple]):
        """提取错误模式"""
        for key, record in error_records:
            error_data = record.get("data", {})
            error_type = error_data.get("error_type") or error_data.get("title", "unknown")
            
            if error_type not in self.failure_patterns:
                self.failure_patterns[error_type] = {
                    "count": 0,
                    "contexts": [],
                    "solutions": []
                }
            
            self.failure_patterns[error_type]["count"] += 1
            self.failure_patterns[error_type]["contexts"].append(error_data.get("context", {}))
    
    def _extract_success_patterns(self, success_records: List[tuple]):
        """提取成功模式"""
        for key, record in success_records:
            success_data = record.get("data", {})
            task_type = success_data.get("task_type", "unknown")
            
            if task_type not in self.success_patterns:
                self.success_patterns[task_type] = {
                    "count": 0,
                    "approaches": [],
                    "duration": []
                }
            
            self.success_patterns[task_type]["count"] += 1
            self.success_patterns[task_type]["approaches"].append(success_data.get("approach", ""))
    
    def predict_error_likelihood(self, current_context: Dict[str, Any]) -> Dict[str, float]:
        """预测错误可能性"""
        predictions = {}
        
        for error_type, pattern in self.failure_patterns.items():
            # 简单的相似度计算
            similarity = self._calculate_context_similarity(
                current_context, 
                pattern["contexts"]
            )
            
            # 基于历史频率和相似度计算概率
            frequency_weight = min(pattern["count"] / 10, 1.0)  # 归一化频率
            predictions[error_type] = similarity * frequency_weight
        
        return predictions
    
    def suggest_best_approach(self, task_type: str) -> Optional[str]:
        """建议最佳方法"""
        if task_type in self.success_patterns:
            pattern = self.success_patterns[task_type]
            if pattern["approaches"]:
                # 返回最常用的方法
                approach_counts = {}
                for approach in pattern["approaches"]:
                    approach_counts[approach] = approach_counts.get(approach, 0) + 1
                
                best_approach = max(approach_counts.items(), key=lambda x: x[1])
                return best_approach[0]
        
        return None
    
    def _calculate_context_similarity(self, current_context: Dict[str, Any], 
                                    historical_contexts: List[Dict[str, Any]]) -> float:
        """计算上下文相似度"""
        if not historical_contexts:
            return 0.0
        
        similarities = []
        for hist_context in historical_contexts:
            similarity = 0.0
            total_keys = set(current_context.keys()) | set(hist_context.keys())
            
            if total_keys:
                matching_keys = set(current_context.keys()) & set(hist_context.keys())
                similarity = len(matching_keys) / len(total_keys)
            
            similarities.append(similarity)
        
        return max(similarities) if similarities else 0.0
    
    def learn_from_outcome(self, context: Dict[str, Any], outcome: str, details: Dict[str, Any]):
        """从结果中学习"""
        learning_record = {
            "context": context,
            "outcome": outcome,  # "success" or "failure"
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        
        # 更新学习数据
        if outcome == "success":
            task_type = details.get("task_type", "unknown")
            if task_type not in self.success_patterns:
                self.success_patterns[task_type] = {
                    "count": 0,
                    "approaches": [],
                    "duration": []
                }
            self.success_patterns[task_type]["count"] += 1
            self.success_patterns[task_type]["approaches"].append(details.get("approach", ""))
        
        elif outcome == "failure":
            error_type = details.get("error_type", "unknown")
            if error_type not in self.failure_patterns:
                self.failure_patterns[error_type] = {
                    "count": 0,
                    "contexts": [],
                    "solutions": []
                }
            self.failure_patterns[error_type]["count"] += 1
            self.failure_patterns[error_type]["contexts"].append(context)

class IntelligentMonitor:
    """智能监控系统主类"""
    
    def __init__(self, config_path: str = None):
        # 统一为仓库内 tools/LongMemory 下的配置；memory_path 由上层服务注入，默认为仓库日志路径
        self.config_path = config_path or "tools/LongMemory/intelligent_monitor_config.json"
        self.memory_path = "logs/longmemory/lm_records.json"
        
        # 初始化子系统
        self.error_detector = SmartErrorDetector()
        self.proactive_reminder = ProactiveReminder()
        self.learning_engine = LearningEngine(self.memory_path)
        
        self.load_config()
        
        self.monitoring = False
        self.monitor_thread = None
        
        # 设置信号处理（仅在主线程中注册，避免通过 HTTP 启动时报错）
        try:
            if threading.current_thread() is threading.main_thread():
                signal.signal(signal.SIGINT, self._signal_handler)
                signal.signal(signal.SIGTERM, self._signal_handler)
            else:
                # 非主线程环境跳过信号注册，不影响组件运行
                pass
        except Exception as e:
            # 兼容性处理：在非交互或子线程环境下，signal 可能不可用
            print(f"⚠️ 信号注册跳过: {e}")
    
    def load_config(self):
        """加载配置"""
        default_config = {
            "enabled": True,
            "integration_mode": "full",  # "full", "detection_only", "reminder_only"
            "learning_enabled": True,
            "auto_intervention": True,
            "intervention_threshold": 0.7,  # 错误概率阈值
            "monitoring_interval": 30,
            "log_level": "info",
            "features": {
                "smart_error_detection": True,
                "proactive_reminders": True,
                "learning_engine": True,
                "auto_correction": False  # 自动修正功能（未来实现）
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
            print(f"❌ 配置加载失败: {e}")
            self.config = default_config
    
    def save_config(self):
        """保存配置"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ 配置保存失败: {e}")
    
    def start_monitoring(self):
        """启动智能监控"""
        if self.monitoring:
            print("⚠️ 智能监控系统已在运行中")
            return
        
        print("🧠 启动智能监控系统...")
        print("=" * 60)
        
        # 启动子系统
        if self.config["features"]["smart_error_detection"]:
            self.error_detector.start_monitoring()
            print("✅ 智能错误检测已启动")
        
        if self.config["features"]["proactive_reminders"]:
            self.proactive_reminder.start_monitoring()
            print("✅ 主动提醒系统已启动")
        
        # 启动主监控循环
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._intelligent_monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        print("✅ 智能监控主循环已启动")
        print(f"⚙️ 集成模式: {self.config['integration_mode']}")
        print(f"🧠 学习引擎: {'启用' if self.config['learning_enabled'] else '禁用'}")
        print(f"🤖 自动干预: {'启用' if self.config['auto_intervention'] else '禁用'}")
        print("=" * 60)
    
    def stop_monitoring(self):
        """停止智能监控"""
        print("\n🛑 正在停止智能监控系统...")
        
        self.monitoring = False
        
        # 停止子系统
        if hasattr(self.error_detector, 'stop_monitoring'):
            self.error_detector.stop_monitoring()
        
        if hasattr(self.proactive_reminder, 'stop_monitoring'):
            self.proactive_reminder.stop_monitoring()
        
        # 等待主线程结束
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        print("✅ 智能监控系统已完全停止")
    
    def _intelligent_monitor_loop(self):
        """智能监控主循环"""
        while self.monitoring:
            try:
                # 获取当前状态
                current_context = self._get_current_context()
                
                # 预测错误可能性
                if self.config["learning_enabled"]:
                    error_predictions = self.learning_engine.predict_error_likelihood(current_context)
                    self._handle_error_predictions(error_predictions, current_context)
                
                # 协调子系统
                self._coordinate_subsystems()
                
                # 生成智能建议
                self._generate_intelligent_suggestions(current_context)
                
                time.sleep(self.config["monitoring_interval"])
                
            except Exception as e:
                print(f"❌ 智能监控循环错误: {e}")
                time.sleep(5)
    
    def _get_current_context(self) -> Dict[str, Any]:
        """获取当前上下文"""
        context = {
            "timestamp": datetime.now().isoformat(),
            "active_alerts": len(self.error_detector.get_active_alerts()),
            "active_reminders": len(self.proactive_reminder.get_active_reminders()),
            "recent_activities": []
        }
        
        # 从子系统获取更多上下文信息
        if hasattr(self.proactive_reminder, 'context_analyzer'):
            situation = self.proactive_reminder.context_analyzer.analyze_current_situation()
            context.update(situation)
        
        return context
    
    def _handle_error_predictions(self, predictions: Dict[str, float], context: Dict[str, Any]):
        """处理错误预测"""
        high_risk_errors = {
            error_type: probability 
            for error_type, probability in predictions.items()
            if probability > self.config["intervention_threshold"]
        }
        
        if high_risk_errors and self.config["auto_intervention"]:
            for error_type, probability in high_risk_errors.items():
                self._trigger_intervention(error_type, probability, context)
    
    def _trigger_intervention(self, error_type: str, probability: float, context: Dict[str, Any]):
        """触发干预措施"""
        intervention_message = f"⚠️ 高风险预警：检测到 {error_type} 错误的高概率 ({probability:.2%})"
        
        # 获取建议的解决方案
        suggestions = self.learning_engine.failure_patterns.get(error_type, {}).get("solutions", [])
        if not suggestions:
            suggestions = ["检查相关代码", "查看错误日志", "参考历史解决方案"]
        
        print(f"\n🚨 【智能干预】{intervention_message}")
        print("💡 建议采取以下措施:")
        for i, suggestion in enumerate(suggestions[:3], 1):
            print(f"   {i}. {suggestion}")
        
        # 记录干预行为
        self._log_intervention(error_type, probability, context, suggestions)
    
    def _coordinate_subsystems(self):
        """协调子系统"""
        # 获取错误检测器的警报
        error_alerts = self.error_detector.get_active_alerts()
        
        # 将错误信息传递给提醒系统
        for alert in error_alerts:
            if not alert.get("processed_by_reminder"):
                self.proactive_reminder.report_error(
                    alert.get("title", "unknown"),
                    alert.get("message", ""),
                    alert.get("context", {})
                )
                alert["processed_by_reminder"] = True
        
        # 获取提醒系统的活动信息
        reminders = self.proactive_reminder.get_active_reminders()
        
        # 基于提醒调整错误检测敏感度
        if len(reminders) > 3:
            # 如果提醒过多，降低检测敏感度
            pass  # 这里可以实现动态调整逻辑
    
    def _generate_intelligent_suggestions(self, context: Dict[str, Any]):
        """生成智能建议"""
        current_focus = context.get("current_focus", "unknown")
        
        if current_focus == "debugging":
            # 在调试模式下提供特定建议
            suggestion = self.learning_engine.suggest_best_approach("debugging")
            if suggestion:
                print(f"💡 智能建议：{suggestion}")
        
        elif current_focus == "coding":
            # 在编码模式下检查最佳实践
            pass  # 由主动提醒系统处理
    
    def _log_intervention(self, error_type: str, probability: float, 
                         context: Dict[str, Any], suggestions: List[str]):
        """记录干预行为"""
        try:
            if FileLock:
                with FileLock(self.memory_path):
                    if os.path.exists(self.memory_path):
                        with open(self.memory_path, 'r', encoding='utf-8') as f:
                            memory_data = json.load(f)
                    else:
                        memory_data = {"general": {}, "memories": []}

                    # 添加干预记录
                    intervention_key = f"intelligent_intervention_{int(datetime.now().timestamp())}"
                    memory_data["general"][intervention_key] = {
                        "timestamp": datetime.now().isoformat(),
                        "type": "intelligent_intervention",
                        "data": {
                            "error_type": error_type,
                            "probability": probability,
                            "context": context,
                            "suggestions": suggestions
                        }
                    }

                    # 同步追加到 memories 数组（TraeLM 兼容结构）
                    try:
                        imp = probability
                        try:
                            imp = float(probability)
                        except Exception:
                            imp = 0.5
                        # 夹逼到 [0,1]
                        importance = max(0.0, min(1.0, imp))
                        content = (
                            f"[Intervention] Predicted {error_type} with p={importance:.2f}. "
                            + (f"Suggestions: {', '.join(suggestions[:3])}" if suggestions else "")
                        )
                        memory_entry = {
                            "id": f"mem_{int(datetime.now().timestamp()*1000)}",
                            "content": content,
                            "summary": f"Intervention for {error_type}",
                            "type": "episodic",  # 干预记录为情景事件
                            "importance": importance,
                            "tags": ["intelligent_intervention", error_type],
                            "context": context or {},
                            "metadata": {
                                "source": "IntelligentMonitor",
                                "probability": probability,
                                "suggestions": suggestions
                            },
                            "createdAt": datetime.now().isoformat(),
                            "updatedAt": datetime.now().isoformat()
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
                
                # 添加干预记录
                intervention_key = f"intelligent_intervention_{int(datetime.now().timestamp())}"
                memory_data["general"][intervention_key] = {
                    "timestamp": datetime.now().isoformat(),
                    "type": "intelligent_intervention",
                    "data": {
                        "error_type": error_type,
                        "probability": probability,
                        "context": context,
                        "suggestions": suggestions
                    }
                }
                # 同步追加到 memories 数组
                try:
                    imp = probability
                    try:
                        imp = float(probability)
                    except Exception:
                        imp = 0.5
                    importance = max(0.0, min(1.0, imp))
                    content = (
                        f"[Intervention] Predicted {error_type} with p={importance:.2f}. "
                        + (f"Suggestions: {', '.join(suggestions[:3])}" if suggestions else "")
                    )
                    memory_entry = {
                        "id": f"mem_{int(datetime.now().timestamp()*1000)}",
                        "content": content,
                        "summary": f"Intervention for {error_type}",
                        "type": "episodic",
                        "importance": importance,
                        "tags": ["intelligent_intervention", error_type],
                        "context": context or {},
                        "metadata": {
                            "source": "IntelligentMonitor",
                            "probability": probability,
                            "suggestions": suggestions
                        },
                        "createdAt": datetime.now().isoformat(),
                        "updatedAt": datetime.now().isoformat()
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
            print(f"❌ 干预记录失败: {e}")
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        print(f"\n🔔 收到信号 {signum}，正在优雅关闭...")
        self.stop_monitoring()
        sys.exit(0)
    
    def report_task_outcome(self, task_type: str, outcome: str, details: Dict[str, Any]):
        """报告任务结果（供外部调用）"""
        if self.config["learning_enabled"]:
            context = self._get_current_context()
            self.learning_engine.learn_from_outcome(context, outcome, details)
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            "monitoring_active": self.monitoring,
            "error_detector_status": self.error_detector.get_statistics(),
            "reminder_system_status": self.proactive_reminder.get_statistics(),
            "learning_patterns": {
                "success_patterns": len(self.learning_engine.success_patterns),
                "failure_patterns": len(self.learning_engine.failure_patterns)
            },
            "config": self.config
        }
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取仪表板数据"""
        status = self.get_system_status()
        
        return {
            "system_health": "healthy" if self.monitoring else "stopped",
            "active_alerts": status["error_detector_status"]["active_alerts"],
            "active_reminders": status["reminder_system_status"]["active_reminders"],
            "learning_progress": {
                "patterns_learned": (
                    status["learning_patterns"]["success_patterns"] + 
                    status["learning_patterns"]["failure_patterns"]
                ),
                "success_rate": self._calculate_success_rate()
            },
            "recent_interventions": self._get_recent_interventions()
        }
    
    def _calculate_success_rate(self) -> float:
        """计算成功率"""
        success_count = sum(pattern["count"] for pattern in self.learning_engine.success_patterns.values())
        failure_count = sum(pattern["count"] for pattern in self.learning_engine.failure_patterns.values())
        
        total = success_count + failure_count
        return (success_count / total * 100) if total > 0 else 0.0
    
    def _get_recent_interventions(self) -> List[Dict[str, Any]]:
        """获取最近的干预记录"""
        try:
            if os.path.exists(self.memory_path):
                with open(self.memory_path, 'r', encoding='utf-8') as f:
                    memory_data = json.load(f)
                
                interventions = [
                    value["data"] for key, value in memory_data.get("general", {}).items()
                    if value.get("type") == "intelligent_intervention"
                ]
                
                # 按时间排序，返回最近5个
                interventions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
                return interventions[:5]
        except:
            pass
        
        return []

def main():
    """主函数"""
    print("🧠 智能监控系统 v1.0")
    print("集成错误检测、主动提醒和学习引擎")
    print("=" * 60)
    
    monitor = IntelligentMonitor()
    
    try:
        monitor.start_monitoring()
        
        # 显示系统状态
        print("\n📊 系统状态:")
        status = monitor.get_system_status()
        print(f"   错误检测器: {'运行中' if status['monitoring_active'] else '已停止'}")
        print(f"   提醒系统: {'运行中' if status['monitoring_active'] else '已停止'}")
        print(f"   学习引擎: {'启用' if monitor.config['learning_enabled'] else '禁用'}")
        
        print("\n🔍 开始智能监控，按 Ctrl+C 停止...")
        
        # 主循环
        while True:
            time.sleep(30)
            dashboard = monitor.get_dashboard_data()
            
            if dashboard["active_alerts"] > 0 or dashboard["active_reminders"] > 0:
                print(f"\n📈 系统活动: 警报 {dashboard['active_alerts']} 个, 提醒 {dashboard['active_reminders']} 个")
                print(f"   成功率: {dashboard['learning_progress']['success_rate']:.1f}%")
                
    except KeyboardInterrupt:
        print("\n🛑 收到停止信号")
    except Exception as e:
        print(f"\n❌ 系统错误: {e}")
    finally:
        monitor.stop_monitoring()
        print("👋 智能监控系统已退出")

if __name__ == "__main__":
    main()