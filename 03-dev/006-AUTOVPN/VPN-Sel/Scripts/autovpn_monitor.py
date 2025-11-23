#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTOVPN服务监控器
持续监控服务状态，自动记录日志和异常情况
"""

import os
import sys
import time
import subprocess
import socket
import psutil
from datetime import datetime
from threading import Thread, Event
import json

# 添加脚本目录到路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

# 导入菜单功能
from autovpn_menu import load_config, is_process_running

class AutoVPNMonitor:
    def __init__(self):
        self.config = load_config()
        self.monitor_log = os.path.join(SCRIPT_DIR, "autovpn_monitor.log")
        self.status_file = os.path.join(SCRIPT_DIR, "service_status.json")
        self.stop_event = Event()
        self.check_interval = 30  # 检查间隔（秒）
        self.alert_threshold = 3   # 连续失败次数阈值
        self.failure_counts = {}
        
    def log_message(self, message, level="INFO"):
        """记录监控日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        
        with open(self.monitor_log, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')
    
    def check_port_status(self, host, port, timeout=3):
        """检查端口状态"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False
    
    def check_process_status(self, process_name):
        """检查进程状态"""
        try:
            return is_process_running(process_name)
        except:
            return False
    
    def check_network_connectivity(self):
        """检查网络连通性"""
        try:
            # 测试DNS解析
            result = subprocess.run(
                ["nslookup", "google.com"],
                capture_output=True,
                text=True,
                timeout=5
            )
            dns_ok = result.returncode == 0
            
            # 测试ping
            result = subprocess.run(
                ["ping", "8.8.8.8", "-n", "2"],
                capture_output=True,
                text=True,
                timeout=10
            )
            ping_ok = result.returncode == 0
            
            return dns_ok, ping_ok
            
        except:
            return False, False
    
    def check_ipv6_connectivity(self):
        """检查IPv6连通性"""
        try:
            # 测试IPv6回环
            result = subprocess.run(
                ["ping", "::1", "-n", "1"],
                capture_output=True,
                text=True,
                timeout=5
            )
            ipv6_loopback_ok = result.returncode == 0
            
            # 测试IPv6 DNS
            result = subprocess.run(
                ["nslookup", "-type=AAAA", "google.com"],
                capture_output=True,
                text=True,
                timeout=5
            )
            ipv6_dns_ok = result.returncode == 0 and "AAAA" in result.stdout
            
            return ipv6_loopback_ok, ipv6_dns_ok
            
        except:
            return False, False
    
    def get_service_status(self):
        """获取完整的服务状态"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'services': {},
            'network': {},
            'ipv6': {},
            'config': {}
        }
        
        # 检查主要服务
        status['services']['wstunnel'] = {
            'running': self.check_process_status('wstunnel.exe'),
            'socks5_port': self.check_port_status('127.0.0.1', 1082),
            'http_port': self.check_port_status('127.0.0.1', 8081)
        }
        
        # 检查网络
        dns_ok, ping_ok = self.check_network_connectivity()
        status['network'] = {
            'dns_ok': dns_ok,
            'ping_ok': ping_ok
        }
        
        # 检查IPv6
        ipv6_loopback, ipv6_dns = self.check_ipv6_connectivity()
        status['ipv6'] = {
            'loopback_ok': ipv6_loopback,
            'dns_ok': ipv6_dns
        }
        
        # 检查配置
        config = load_config()
        status['config'] = {
            'loaded': config is not None,
            'ipv6_enabled': config.get('ipv6_enabled', False) if config else False,
            'proxy_enabled': config.get('proxy_enabled', False) if config else False
        }
        
        return status
    
    def check_and_alert(self, service_name, status, threshold=3):
        """检查状态并发出警报"""
        if not status:
            self.failure_counts[service_name] = self.failure_counts.get(service_name, 0) + 1
            
            if self.failure_counts[service_name] >= threshold:
                self.log_message(f"⚠️  {service_name} 连续失败 {self.failure_counts[service_name]} 次！需要关注", "WARNING")
                return True
        else:
            # 重置失败计数
            if service_name in self.failure_counts:
                if self.failure_counts[service_name] > 0:
                    self.log_message(f"✅ {service_name} 恢复正常", "INFO")
                del self.failure_counts[service_name]
        
        return False
    
    def save_status_to_file(self, status):
        """保存状态到文件"""
        try:
            with open(self.status_file, 'w', encoding='utf-8') as f:
                json.dump(status, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.log_message(f"保存状态文件失败: {e}", "ERROR")
    
    def print_status_summary(self, status):
        """打印状态摘要"""
        print("\n" + "="*60)
        print(f"AUTOVPN服务状态监控 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        # 服务状态
        wstunnel_running = status['services']['wstunnel']['running']
        socks5_ok = status['services']['wstunnel']['socks5_port']
        http_ok = status['services']['wstunnel']['http_port']
        
        print(f"wstunnel服务: {'✅运行中' if wstunnel_running else '❌未运行'}")
        print(f"SOCKS5代理 (1082): {'✅监听' if socks5_ok else '❌未监听'}")
        print(f"HTTP代理 (8081): {'✅监听' if http_ok else '❌未监听'}")
        
        # 网络状态
        dns_ok = status['network']['dns_ok']
        ping_ok = status['network']['ping_ok']
        print(f"DNS解析: {'✅正常' if dns_ok else '❌异常'}")
        print(f"网络ping: {'✅正常' if ping_ok else '❌异常'}")
        
        # IPv6状态
        ipv6_loopback = status['ipv6']['loopback_ok']
        ipv6_dns = status['ipv6']['dns_ok']
        print(f"IPv6回环: {'✅正常' if ipv6_loopback else '❌异常'}")
        print(f"IPv6 DNS: {'✅正常' if ipv6_dns else '❌异常'}")
        
        # 配置状态
        config_loaded = status['config']['loaded']
        ipv6_enabled = status['config']['ipv6_enabled']
        proxy_enabled = status['config']['proxy_enabled']
        print(f"配置加载: {'✅成功' if config_loaded else '❌失败'}")
        print(f"IPv6开关: {'✅开启' if ipv6_enabled else '❌关闭'}")
        print(f"代理模式: {'✅开启' if proxy_enabled else '❌关闭'}")
        
        print("="*60)
    
    def monitor_loop(self):
        """监控主循环"""
        self.log_message("AUTOVPN服务监控器启动")
        
        while not self.stop_event.is_set():
            try:
                # 获取当前状态
                status = self.get_service_status()
                
                # 保存状态到文件
                self.save_status_to_file(status)
                
                # 打印状态摘要
                self.print_status_summary(status)
                
                # 检查并发出警报
                self.check_and_alert("wstunnel服务", status['services']['wstunnel']['running'])
                self.check_and_alert("SOCKS5代理", status['services']['wstunnel']['socks5_port'])
                self.check_and_alert("HTTP代理", status['services']['wstunnel']['http_port'])
                self.check_and_alert("网络连接", status['network']['dns_ok'] and status['network']['ping_ok'])
                
                # 记录异常状态
                if not status['services']['wstunnel']['running']:
                    self.log_message("wstunnel服务未运行", "WARNING")
                
                if not status['network']['dns_ok']:
                    self.log_message("DNS解析异常", "WARNING")
                
                if not status['network']['ping_ok']:
                    self.log_message("网络连接异常", "WARNING")
                
                # 等待下一个检查周期
                self.stop_event.wait(self.check_interval)
                
            except KeyboardInterrupt:
                self.log_message("监控被用户中断", "INFO")
                break
            except Exception as e:
                self.log_message(f"监控循环异常: {e}", "ERROR")
                self.stop_event.wait(5)  # 出错时等待5秒继续
    
    def start_monitoring(self):
        """开始监控"""
        try:
            self.monitor_loop()
        except KeyboardInterrupt:
            self.log_message("监控器正在关闭...", "INFO")
        finally:
            self.log_message("AUTOVPN服务监控器已停止", "INFO")
    
    def stop_monitoring(self):
        """停止监控"""
        self.stop_event.set()

def create_monitor_service():
    """创建监控服务脚本"""
    service_script = """@echo off
echo Starting AUTOVPN Monitor Service...
cd /d "{}"
python autovpn_monitor.py
pause
""".format(SCRIPT_DIR)
    
    service_path = os.path.join(SCRIPT_DIR, "start_monitor.bat")
    with open(service_path, 'w', encoding='utf-8') as f:
        f.write(service_script)
    
    return service_path

def main():
    """主函数"""
    print("AUTOVPN服务监控器")
    print("=" * 50)
    print("功能:")
    print("- 实时监控wstunnel服务状态")
    print("- 监控网络连通性")
    print("- 监控IPv6支持状态")
    print("- 自动记录异常和警报")
    print("- 生成状态报告文件")
    print("=" * 50)
    
    monitor = AutoVPNMonitor()
    
    try:
        # 创建监控服务启动脚本
        service_path = create_monitor_service()
        print(f"已创建监控服务启动脚本: {service_path}")
        print("您可以通过双击此文件来启动监控服务")
        print()
        
        # 开始监控
        monitor.start_monitoring()
        
    except KeyboardInterrupt:
        print("\n监控器被用户中断")
    except Exception as e:
        print(f"监控器启动失败: {e}")
    finally:
        monitor.stop_monitoring()

if __name__ == "__main__":
    main()