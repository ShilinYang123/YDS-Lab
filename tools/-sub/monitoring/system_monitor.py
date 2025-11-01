#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YDS-Lab 系统监控工具
提供系统资源监控、性能分析和告警功能
适配YDS-Lab项目结构和AI Agent协作需求
"""

import os
import sys
import json
import yaml
import time
import psutil
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import deque
import logging

@dataclass
class SystemMetrics:
    """系统指标数据类"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_used: int
    memory_total: int
    disk_percent: float
    disk_used: int
    disk_total: int
    network_sent: int
    network_recv: int
    process_count: int
    load_average: List[float] = None
    temperature: Dict[str, float] = None

@dataclass
class ProcessInfo:
    """进程信息数据类"""
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    memory_rss: int
    memory_vms: int
    status: str
    create_time: float
    cmdline: List[str]

@dataclass
class Alert:
    """告警数据类"""
    timestamp: str
    level: str  # info, warning, error, critical
    metric: str
    value: float
    threshold: float
    message: str
    resolved: bool = False
    resolved_time: str = None

class SystemMonitor:
    """系统监控器"""
    
    def __init__(self, project_root: str = None):
        """初始化系统监控器"""
        if project_root is None:
            self.project_root = Path(__file__).parent.parent.parent
        else:
            self.project_root = Path(project_root)
        
        self.config_dir = self.project_root / "Struc" / "GeneralOffice" / "config"
        self.logs_dir = self.project_root / "logs" / "monitoring"
        self.reports_dir = self.project_root / "reports" / "monitoring"
        
        # 创建目录
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # 监控配置
        self.config = self._load_config()
        
        # 监控数据
        self.metrics_history = deque(maxlen=self.config['history_size'])
        self.alerts = []
        self.active_alerts = {}
        
        # 监控状态
        self.monitoring = False
        self.monitor_thread = None
        
        # 回调函数
        self.alert_callbacks: List[Callable] = []
        
        # 设置日志
        self._setup_logging()
        
        # 网络基准值
        self.network_baseline = self._get_network_baseline()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载监控配置"""
        config_file = self.config_dir / "monitor_config.yaml"
        
        default_config = {
            'monitoring_interval': 5,  # 秒
            'history_size': 1000,
            'alert_thresholds': {
                'cpu_percent': {'warning': 80.0, 'critical': 95.0},
                'memory_percent': {'warning': 85.0, 'critical': 95.0},
                'disk_percent': {'warning': 85.0, 'critical': 95.0},
                'process_count': {'warning': 500, 'critical': 1000},
                'temperature': {'warning': 70.0, 'critical': 85.0}
            },
            'alert_cooldown': 300,  # 5分钟
            'log_level': 'INFO',
            'enable_email_alerts': False,
            'email_config': {
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'username': '',
                'password': '',
                'recipients': []
            },
            'monitored_processes': [
                'python',
                'node',
                'java',
                'docker',
                'nginx',
                'apache2'
            ],
            'network_monitoring': True,
            'temperature_monitoring': True,
            'auto_cleanup_logs': True,
            'log_retention_days': 30
        }
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f)
                    default_config.update(user_config)
            except Exception as e:
                print(f"⚠️ 加载监控配置失败: {e}")
        
        return default_config
    
    def _setup_logging(self):
        """设置日志"""
        log_file = self.logs_dir / f"monitor_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=getattr(logging, self.config['log_level']),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def _get_network_baseline(self) -> Dict[str, int]:
        """获取网络基准值"""
        try:
            net_io = psutil.net_io_counters()
            return {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv
            }
        except Exception:
            return {'bytes_sent': 0, 'bytes_recv': 0}
    
    def collect_metrics(self) -> SystemMetrics:
        """收集系统指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            
            # 磁盘使用情况
            disk = psutil.disk_usage('/')
            
            # 网络使用情况
            net_io = psutil.net_io_counters()
            network_sent = net_io.bytes_sent - self.network_baseline['bytes_sent']
            network_recv = net_io.bytes_recv - self.network_baseline['bytes_recv']
            
            # 进程数量
            process_count = len(psutil.pids())
            
            # 负载平均值（Linux/macOS）
            load_average = None
            try:
                if hasattr(os, 'getloadavg'):
                    load_average = list(os.getloadavg())
            except Exception:
                pass
            
            # 温度信息
            temperature = None
            if self.config['temperature_monitoring']:
                try:
                    temps = psutil.sensors_temperatures()
                    if temps:
                        temperature = {}
                        for name, entries in temps.items():
                            if entries:
                                temperature[name] = entries[0].current
                except Exception:
                    pass
            
            metrics = SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used=memory.used,
                memory_total=memory.total,
                disk_percent=disk.percent,
                disk_used=disk.used,
                disk_total=disk.total,
                network_sent=network_sent,
                network_recv=network_recv,
                process_count=process_count,
                load_average=load_average,
                temperature=temperature
            )
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"收集系统指标失败: {e}")
            return None
    
    def get_process_info(self, process_name: str = None) -> List[ProcessInfo]:
        """获取进程信息"""
        processes = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent',
                                           'memory_info', 'status', 'create_time', 'cmdline']):
                try:
                    pinfo = proc.info
                    
                    # 过滤进程
                    if process_name and process_name.lower() not in pinfo['name'].lower():
                        continue
                    
                    process_info = ProcessInfo(
                        pid=pinfo['pid'],
                        name=pinfo['name'],
                        cpu_percent=pinfo['cpu_percent'] or 0.0,
                        memory_percent=pinfo['memory_percent'] or 0.0,
                        memory_rss=pinfo['memory_info'].rss if pinfo['memory_info'] else 0,
                        memory_vms=pinfo['memory_info'].vms if pinfo['memory_info'] else 0,
                        status=pinfo['status'],
                        create_time=pinfo['create_time'],
                        cmdline=pinfo['cmdline'] or []
                    )
                    
                    processes.append(process_info)
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
        except Exception as e:
            self.logger.error(f"获取进程信息失败: {e}")
        
        return processes
    
    def check_alerts(self, metrics: SystemMetrics):
        """检查告警条件"""
        current_time = datetime.now()
        thresholds = self.config['alert_thresholds']
        
        # 检查各项指标
        checks = [
            ('cpu_percent', metrics.cpu_percent, '%'),
            ('memory_percent', metrics.memory_percent, '%'),
            ('disk_percent', metrics.disk_percent, '%'),
            ('process_count', metrics.process_count, '个')
        ]
        
        for metric_name, value, unit in checks:
            if metric_name in thresholds:
                metric_thresholds = thresholds[metric_name]
                
                # 检查临界告警
                if 'critical' in metric_thresholds and value >= metric_thresholds['critical']:
                    self._create_alert('critical', metric_name, value, 
                                     metric_thresholds['critical'], unit)
                
                # 检查警告告警
                elif 'warning' in metric_thresholds and value >= metric_thresholds['warning']:
                    self._create_alert('warning', metric_name, value, 
                                     metric_thresholds['warning'], unit)
                
                # 检查告警恢复
                else:
                    self._resolve_alert(metric_name)
        
        # 检查温度告警
        if metrics.temperature and 'temperature' in thresholds:
            temp_thresholds = thresholds['temperature']
            
            for sensor_name, temp_value in metrics.temperature.items():
                metric_key = f"temperature_{sensor_name}"
                
                if 'critical' in temp_thresholds and temp_value >= temp_thresholds['critical']:
                    self._create_alert('critical', metric_key, temp_value, 
                                     temp_thresholds['critical'], '°C')
                elif 'warning' in temp_thresholds and temp_value >= temp_thresholds['warning']:
                    self._create_alert('warning', metric_key, temp_value, 
                                     temp_thresholds['warning'], '°C')
                else:
                    self._resolve_alert(metric_key)
    
    def _create_alert(self, level: str, metric: str, value: float, threshold: float, unit: str):
        """创建告警"""
        current_time = datetime.now()
        
        # 检查冷却时间
        if metric in self.active_alerts:
            last_alert_time = datetime.fromisoformat(self.active_alerts[metric].timestamp)
            cooldown = timedelta(seconds=self.config['alert_cooldown'])
            
            if current_time - last_alert_time < cooldown:
                return
        
        # 创建告警
        alert = Alert(
            timestamp=current_time.isoformat(),
            level=level,
            metric=metric,
            value=value,
            threshold=threshold,
            message=f"{metric} 达到 {level} 阈值: {value}{unit} >= {threshold}{unit}"
        )
        
        self.alerts.append(alert)
        self.active_alerts[metric] = alert
        
        # 记录日志
        log_func = getattr(self.logger, level.lower(), self.logger.info)
        log_func(f"告警: {alert.message}")
        
        # 触发回调
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                self.logger.error(f"告警回调执行失败: {e}")
        
        # 发送邮件告警
        if self.config['enable_email_alerts']:
            self._send_email_alert(alert)
    
    def _resolve_alert(self, metric: str):
        """解决告警"""
        if metric in self.active_alerts:
            alert = self.active_alerts[metric]
            alert.resolved = True
            alert.resolved_time = datetime.now().isoformat()
            
            del self.active_alerts[metric]
            
            self.logger.info(f"告警已解决: {metric}")
    
    def _send_email_alert(self, alert: Alert):
        """发送邮件告警"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            email_config = self.config['email_config']
            
            if not email_config['username'] or not email_config['recipients']:
                return
            
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = email_config['username']
            msg['To'] = ', '.join(email_config['recipients'])
            msg['Subject'] = f"[{alert.level.upper()}] 系统监控告警 - {alert.metric}"
            
            body = f"""
系统监控告警通知

告警级别: {alert.level.upper()}
告警指标: {alert.metric}
当前值: {alert.value}
阈值: {alert.threshold}
告警时间: {alert.timestamp}
告警信息: {alert.message}

请及时处理相关问题。

---
YDS-Lab 系统监控
"""
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # 发送邮件
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            server.starttls()
            server.login(email_config['username'], email_config['password'])
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"邮件告警已发送: {alert.metric}")
            
        except Exception as e:
            self.logger.error(f"发送邮件告警失败: {e}")
    
    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """添加告警回调函数"""
        self.alert_callbacks.append(callback)
    
    def start_monitoring(self):
        """启动监控"""
        if self.monitoring:
            self.logger.warning("监控已在运行中")
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        self.logger.info("系统监控已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        if not self.monitoring:
            return
        
        self.monitoring = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        self.logger.info("系统监控已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            try:
                # 收集指标
                metrics = self.collect_metrics()
                
                if metrics:
                    # 添加到历史记录
                    self.metrics_history.append(metrics)
                    
                    # 检查告警
                    self.check_alerts(metrics)
                    
                    # 清理旧日志
                    if self.config['auto_cleanup_logs']:
                        self._cleanup_old_logs()
                
                # 等待下次收集
                time.sleep(self.config['monitoring_interval'])
                
            except Exception as e:
                self.logger.error(f"监控循环错误: {e}")
                time.sleep(self.config['monitoring_interval'])
    
    def _cleanup_old_logs(self):
        """清理旧日志"""
        try:
            retention_days = self.config['log_retention_days']
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            for log_file in self.logs_dir.glob("monitor_*.log"):
                try:
                    file_date = datetime.fromtimestamp(log_file.stat().st_mtime)
                    if file_date < cutoff_date:
                        log_file.unlink()
                        self.logger.info(f"已删除旧日志文件: {log_file}")
                except Exception:
                    continue
                    
        except Exception as e:
            self.logger.error(f"清理旧日志失败: {e}")
    
    def get_current_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        if not self.metrics_history:
            return {'status': 'no_data', 'message': '暂无监控数据'}
        
        latest_metrics = self.metrics_history[-1]
        
        return {
            'status': 'active' if self.monitoring else 'stopped',
            'latest_metrics': asdict(latest_metrics),
            'active_alerts': len(self.active_alerts),
            'total_alerts': len(self.alerts),
            'history_size': len(self.metrics_history),
            'uptime': self._get_system_uptime()
        }
    
    def _get_system_uptime(self) -> str:
        """获取系统运行时间"""
        try:
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            uptime_delta = timedelta(seconds=int(uptime_seconds))
            return str(uptime_delta)
        except Exception:
            return "未知"
    
    def get_metrics_summary(self, hours: int = 24) -> Dict[str, Any]:
        """获取指标摘要"""
        if not self.metrics_history:
            return {'message': '暂无监控数据'}
        
        # 过滤指定时间范围内的数据
        cutoff_time = datetime.now() - timedelta(hours=hours)
        filtered_metrics = [
            m for m in self.metrics_history
            if datetime.fromisoformat(m.timestamp) >= cutoff_time
        ]
        
        if not filtered_metrics:
            return {'message': f'过去{hours}小时内暂无监控数据'}
        
        # 计算统计信息
        cpu_values = [m.cpu_percent for m in filtered_metrics]
        memory_values = [m.memory_percent for m in filtered_metrics]
        disk_values = [m.disk_percent for m in filtered_metrics]
        
        summary = {
            'time_range': f'过去{hours}小时',
            'data_points': len(filtered_metrics),
            'cpu': {
                'avg': sum(cpu_values) / len(cpu_values),
                'min': min(cpu_values),
                'max': max(cpu_values)
            },
            'memory': {
                'avg': sum(memory_values) / len(memory_values),
                'min': min(memory_values),
                'max': max(memory_values)
            },
            'disk': {
                'avg': sum(disk_values) / len(disk_values),
                'min': min(disk_values),
                'max': max(disk_values)
            },
            'alerts_in_period': len([
                a for a in self.alerts
                if datetime.fromisoformat(a.timestamp) >= cutoff_time
            ])
        }
        
        return summary
    
    def export_metrics(self, output_format: str = 'json', hours: int = 24) -> str:
        """导出指标数据"""
        if not self.metrics_history:
            return "暂无监控数据"
        
        # 过滤指定时间范围内的数据
        cutoff_time = datetime.now() - timedelta(hours=hours)
        filtered_metrics = [
            m for m in self.metrics_history
            if datetime.fromisoformat(m.timestamp) >= cutoff_time
        ]
        
        if output_format == 'json':
            data = {
                'export_time': datetime.now().isoformat(),
                'time_range_hours': hours,
                'metrics': [asdict(m) for m in filtered_metrics],
                'alerts': [asdict(a) for a in self.alerts if datetime.fromisoformat(a.timestamp) >= cutoff_time]
            }
            return json.dumps(data, ensure_ascii=False, indent=2)
        
        elif output_format == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # 写入表头
            writer.writerow([
                'timestamp', 'cpu_percent', 'memory_percent', 'memory_used', 'memory_total',
                'disk_percent', 'disk_used', 'disk_total', 'network_sent', 'network_recv',
                'process_count'
            ])
            
            # 写入数据
            for metrics in filtered_metrics:
                writer.writerow([
                    metrics.timestamp, metrics.cpu_percent, metrics.memory_percent,
                    metrics.memory_used, metrics.memory_total, metrics.disk_percent,
                    metrics.disk_used, metrics.disk_total, metrics.network_sent,
                    metrics.network_recv, metrics.process_count
                ])
            
            return output.getvalue()
        
        else:
            raise ValueError(f"不支持的输出格式: {output_format}")
    
    def generate_report(self, output_format: str = 'markdown', hours: int = 24) -> str:
        """生成监控报告"""
        if output_format == 'markdown':
            return self._generate_markdown_report(hours)
        elif output_format == 'html':
            return self._generate_html_report(hours)
        else:
            raise ValueError(f"不支持的输出格式: {output_format}")
    
    def _generate_markdown_report(self, hours: int) -> str:
        """生成Markdown格式报告"""
        report = []
        
        # 报告头部
        report.append("# 📊 系统监控报告")
        report.append("")
        report.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"**项目路径**: {self.project_root}")
        report.append(f"**监控状态**: {'运行中' if self.monitoring else '已停止'}")
        report.append(f"**系统运行时间**: {self._get_system_uptime()}")
        report.append("")
        
        # 当前状态
        if self.metrics_history:
            latest_metrics = self.metrics_history[-1]
            
            report.append("## 🔍 当前系统状态")
            report.append("")
            report.append(f"- **CPU使用率**: {latest_metrics.cpu_percent:.1f}%")
            report.append(f"- **内存使用率**: {latest_metrics.memory_percent:.1f}% ({latest_metrics.memory_used // (1024**3):.1f}GB / {latest_metrics.memory_total // (1024**3):.1f}GB)")
            report.append(f"- **磁盘使用率**: {latest_metrics.disk_percent:.1f}% ({latest_metrics.disk_used // (1024**3):.1f}GB / {latest_metrics.disk_total // (1024**3):.1f}GB)")
            report.append(f"- **进程数量**: {latest_metrics.process_count}")
            
            if latest_metrics.load_average:
                report.append(f"- **负载平均值**: {', '.join(f'{x:.2f}' for x in latest_metrics.load_average)}")
            
            if latest_metrics.temperature:
                temp_info = ', '.join(f"{k}: {v:.1f}°C" for k, v in latest_metrics.temperature.items())
                report.append(f"- **温度**: {temp_info}")
            
            report.append("")
        
        # 统计摘要
        summary = self.get_metrics_summary(hours)
        if 'message' not in summary:
            report.append(f"## 📈 过去{hours}小时统计")
            report.append("")
            report.append(f"- **数据点数**: {summary['data_points']}")
            report.append("")
            
            report.append("### CPU使用率")
            report.append(f"- 平均: {summary['cpu']['avg']:.1f}%")
            report.append(f"- 最小: {summary['cpu']['min']:.1f}%")
            report.append(f"- 最大: {summary['cpu']['max']:.1f}%")
            report.append("")
            
            report.append("### 内存使用率")
            report.append(f"- 平均: {summary['memory']['avg']:.1f}%")
            report.append(f"- 最小: {summary['memory']['min']:.1f}%")
            report.append(f"- 最大: {summary['memory']['max']:.1f}%")
            report.append("")
            
            report.append("### 磁盘使用率")
            report.append(f"- 平均: {summary['disk']['avg']:.1f}%")
            report.append(f"- 最小: {summary['disk']['min']:.1f}%")
            report.append(f"- 最大: {summary['disk']['max']:.1f}%")
            report.append("")
            
            if summary['alerts_in_period'] > 0:
                report.append(f"- **告警数量**: {summary['alerts_in_period']}")
                report.append("")
        
        # 活跃告警
        if self.active_alerts:
            report.append("## 🚨 活跃告警")
            report.append("")
            
            for metric, alert in self.active_alerts.items():
                level_icon = {
                    'info': 'ℹ️',
                    'warning': '⚠️',
                    'error': '❌',
                    'critical': '🔥'
                }.get(alert.level, '❓')
                
                report.append(f"{level_icon} **{alert.metric}** ({alert.level.upper()})")
                report.append(f"- 当前值: {alert.value}")
                report.append(f"- 阈值: {alert.threshold}")
                report.append(f"- 时间: {alert.timestamp}")
                report.append(f"- 信息: {alert.message}")
                report.append("")
        
        # 最近告警
        recent_alerts = [
            a for a in self.alerts[-10:]  # 最近10个告警
            if datetime.fromisoformat(a.timestamp) >= datetime.now() - timedelta(hours=hours)
        ]
        
        if recent_alerts:
            report.append(f"## 📋 最近告警 (过去{hours}小时)")
            report.append("")
            
            for alert in reversed(recent_alerts):  # 按时间倒序
                level_icon = {
                    'info': 'ℹ️',
                    'warning': '⚠️',
                    'error': '❌',
                    'critical': '🔥'
                }.get(alert.level, '❓')
                
                status = "已解决" if alert.resolved else "活跃"
                
                report.append(f"{level_icon} **{alert.metric}** ({alert.level.upper()}) - {status}")
                report.append(f"- 时间: {alert.timestamp}")
                report.append(f"- 信息: {alert.message}")
                
                if alert.resolved:
                    report.append(f"- 解决时间: {alert.resolved_time}")
                
                report.append("")
        
        # 进程信息
        monitored_processes = self.config['monitored_processes']
        if monitored_processes:
            report.append("## 🔄 监控进程")
            report.append("")
            
            for process_name in monitored_processes:
                processes = self.get_process_info(process_name)
                
                if processes:
                    # 按CPU使用率排序
                    processes.sort(key=lambda p: p.cpu_percent, reverse=True)
                    
                    report.append(f"### {process_name}")
                    report.append("")
                    
                    for proc in processes[:5]:  # 显示前5个
                        report.append(f"- **PID {proc.pid}**: CPU {proc.cpu_percent:.1f}%, 内存 {proc.memory_percent:.1f}% ({proc.memory_rss // (1024**2):.0f}MB)")
                    
                    report.append("")
        
        return '\n'.join(report)
    
    def _generate_html_report(self, hours: int) -> str:
        """生成HTML格式报告"""
        # 简化的HTML报告
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>系统监控报告</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
        .metrics {{ display: flex; gap: 20px; margin: 20px 0; }}
        .metric-card {{ background: #fff; border: 1px solid #ddd; padding: 15px; border-radius: 5px; flex: 1; }}
        .alert {{ padding: 10px; margin: 10px 0; border-radius: 5px; }}
        .alert.warning {{ background: #fff3cd; border: 1px solid #ffeaa7; }}
        .alert.error {{ background: #f8d7da; border: 1px solid #f5c6cb; }}
        .alert.critical {{ background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }}
        .process-list {{ background: #f8f9fa; padding: 15px; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 系统监控报告</h1>
        <p><strong>生成时间</strong>: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>监控状态</strong>: {'运行中' if self.monitoring else '已停止'}</p>
    </div>
"""
        
        # 当前指标
        if self.metrics_history:
            latest_metrics = self.metrics_history[-1]
            
            html += f"""
    <h2>🔍 当前系统状态</h2>
    <div class="metrics">
        <div class="metric-card">
            <h3>CPU使用率</h3>
            <p>{latest_metrics.cpu_percent:.1f}%</p>
        </div>
        <div class="metric-card">
            <h3>内存使用率</h3>
            <p>{latest_metrics.memory_percent:.1f}%</p>
        </div>
        <div class="metric-card">
            <h3>磁盘使用率</h3>
            <p>{latest_metrics.disk_percent:.1f}%</p>
        </div>
        <div class="metric-card">
            <h3>进程数量</h3>
            <p>{latest_metrics.process_count}</p>
        </div>
    </div>
"""
        
        # 活跃告警
        if self.active_alerts:
            html += "<h2>🚨 活跃告警</h2>"
            
            for metric, alert in self.active_alerts.items():
                html += f"""
    <div class="alert {alert.level}">
        <strong>{alert.metric}</strong> ({alert.level.upper()})
        <p>{alert.message}</p>
        <small>时间: {alert.timestamp}</small>
    </div>
"""
        
        html += """
</body>
</html>
"""
        
        return html
    
    def save_report(self, output_format: str = 'markdown', hours: int = 24, filename: str = None) -> str:
        """保存监控报告"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"monitor_report_{timestamp}.{output_format}"
        
        report_content = self.generate_report(output_format, hours)
        report_path = self.reports_dir / filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"📄 监控报告已保存: {report_path}")
        return str(report_path)

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='YDS-Lab 系统监控工具')
    parser.add_argument('--project-root', help='指定项目根目录路径')
    parser.add_argument('--start', action='store_true', help='启动监控')
    parser.add_argument('--stop', action='store_true', help='停止监控')
    parser.add_argument('--status', action='store_true', help='查看监控状态')
    parser.add_argument('--report', action='store_true', help='生成监控报告')
    parser.add_argument('--export', choices=['json', 'csv'], help='导出监控数据')
    parser.add_argument('--hours', type=int, default=24, help='报告时间范围（小时）')
    parser.add_argument('--format', choices=['markdown', 'html'], default='markdown', help='报告格式')
    parser.add_argument('--output', help='输出文件名')
    parser.add_argument('--process', help='查看指定进程信息')
    parser.add_argument('--alerts', action='store_true', help='查看告警信息')
    
    args = parser.parse_args()
    
    monitor = SystemMonitor(args.project_root)
    
    # 启动监控
    if args.start:
        monitor.start_monitoring()
        print("✅ 监控已启动")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            monitor.stop_monitoring()
            print("\n⏹️ 监控已停止")
        
        return
    
    # 停止监控
    if args.stop:
        monitor.stop_monitoring()
        print("⏹️ 监控已停止")
        return
    
    # 查看状态
    if args.status:
        status = monitor.get_current_status()
        print("\n📊 监控状态")
        print("="*40)
        
        for key, value in status.items():
            print(f"{key}: {value}")
        
        return
    
    # 生成报告
    if args.report:
        report_path = monitor.save_report(args.format, args.hours, args.output)
        print(f"✅ 报告已生成: {report_path}")
        return
    
    # 导出数据
    if args.export:
        data = monitor.export_metrics(args.export, args.hours)
        
        if args.output:
            output_path = Path(args.output)
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = monitor.reports_dir / f"metrics_export_{timestamp}.{args.export}"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(data)
        
        print(f"✅ 数据已导出: {output_path}")
        return
    
    # 查看进程信息
    if args.process:
        processes = monitor.get_process_info(args.process)
        
        if processes:
            print(f"\n🔄 {args.process} 进程信息")
            print("="*60)
            
            # 按CPU使用率排序
            processes.sort(key=lambda p: p.cpu_percent, reverse=True)
            
            for proc in processes[:10]:  # 显示前10个
                print(f"PID {proc.pid:>6}: {proc.name:<20} CPU {proc.cpu_percent:>5.1f}% 内存 {proc.memory_percent:>5.1f}% ({proc.memory_rss // (1024**2):>4.0f}MB)")
        else:
            print(f"⚠️ 未找到 {args.process} 进程")
        
        return
    
    # 查看告警信息
    if args.alerts:
        print("\n🚨 告警信息")
        print("="*50)
        
        if monitor.active_alerts:
            print("活跃告警:")
            for metric, alert in monitor.active_alerts.items():
                print(f"  {alert.level.upper()}: {alert.message}")
        else:
            print("当前无活跃告警")
        
        recent_alerts = monitor.alerts[-10:] if monitor.alerts else []
        if recent_alerts:
            print(f"\n最近告警 (共{len(monitor.alerts)}个):")
            for alert in reversed(recent_alerts):
                status = "已解决" if alert.resolved else "活跃"
                print(f"  {alert.timestamp} [{alert.level.upper()}] {alert.message} ({status})")
        
        return
    
    # 默认显示当前指标
    metrics = monitor.collect_metrics()
    if metrics:
        print("\n📊 当前系统指标")
        print("="*40)
        print(f"CPU使用率: {metrics.cpu_percent:.1f}%")
        print(f"内存使用率: {metrics.memory_percent:.1f}% ({metrics.memory_used // (1024**3):.1f}GB / {metrics.memory_total // (1024**3):.1f}GB)")
        print(f"磁盘使用率: {metrics.disk_percent:.1f}% ({metrics.disk_used // (1024**3):.1f}GB / {metrics.disk_total // (1024**3):.1f}GB)")
        print(f"进程数量: {metrics.process_count}")
        
        if metrics.load_average:
            print(f"负载平均值: {', '.join(f'{x:.2f}' for x in metrics.load_average)}")
        
        if metrics.temperature:
            temp_info = ', '.join(f"{k}: {v:.1f}°C" for k, v in metrics.temperature.items())
            print(f"温度: {temp_info}")
    else:
        print("⚠️ 无法获取系统指标")

if __name__ == "__main__":
    main()