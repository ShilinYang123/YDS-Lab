#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后台自动监控脚本 - 持续监控批量解析进度
"""

import os
import sys
import time
import subprocess
import threading
from datetime import datetime

class BackgroundMonitor:
    def __init__(self):
        self.running = True
        self.log_file = f"auto_background_monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self.start_time = time.time()
        self.last_progress = 0
        
    def log(self, message):
        """记录日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        elapsed = int(time.time() - self.start_time)
        log_message = f"[{timestamp}] [{elapsed}s] {message}"
        print(log_message)
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + '\n')
    
    def monitor_batch_progress(self):
        """监控批量解析进度"""
        self.log("🔍 开始监控批量解析进度...")
        
        while self.running:
            try:
                # 检查批量解析器是否在运行
                result = subprocess.run([
                    'tasklist', '/FI', 'IMAGENAME eq python.exe', '/FO', 'CSV'
                ], capture_output=True, text=True)
                
                if 'batch_domain_resolver.py' in result.stdout:
                    self.log("📊 批量解析器正在运行...")
                else:
                    self.log("⏸️  批量解析器未在运行")
                
                # 检查日志文件
                log_files = [
                    'batch_domain_resolver.log',
                    'auto_monitor_simple.log',
                    'auto_complete_resolver.log'
                ]
                
                for log_file in log_files:
                    if os.path.exists(log_file):
                        try:
                            with open(log_file, 'r', encoding='utf-8') as f:
                                content = f.read()
                                
                            # 分析进度
                            if '批次' in content and '/' in content:
                                import re
                                batch_matches = re.findall(r'批次 (\\d+)/(\\d+)', content)
                                if batch_matches:
                                    current = int(batch_matches[-1][0])
                                    total = int(batch_matches[-1][1])
                                    progress = (current / total) * 100
                                    
                                    if progress > self.last_progress:
                                        self.log(f"🎯 解析进度: {current}/{total} ({progress:.1f}%)")
                                        self.last_progress = progress
                            
                            # 检查是否完成
                            if '解析完成' in content or '全部完成' in content:
                                self.log("✅ 检测到解析完成信号")
                                return True
                                
                        except Exception as e:
                            self.log(f"读取日志文件异常: {e}")
                
                # 检查IP文件更新
                ip_file = r's:\\YDS-Lab\\03-dev\\006-AUTOVPN\\allout\\routes\\常用境外IP.txt'
                if os.path.exists(ip_file):
                    try:
                        with open(ip_file, 'r', encoding='utf-8') as f:
                            ip_count = len([line for line in f if line.strip() and not line.startswith('#')])
                        
                        if ip_count > 0:
                            self.log(f"📈 当前IP数量: {ip_count}")
                    except Exception as e:
                        self.log(f"检查IP文件异常: {e}")
                
                time.sleep(10)  # 每10秒检查一次
                
            except Exception as e:
                self.log(f"监控循环异常: {e}")
                time.sleep(5)
    
    def auto_restart_if_stuck(self):
        """自动重启卡住的解析器"""
        self.log("🔄 启动自动重启监控...")
        
        last_ip_count = 0
        stuck_count = 0
        max_stuck_time = 300  # 5分钟无变化认为卡住
        last_change_time = time.time()
        
        while self.running:
            try:
                # 检查IP文件
                ip_file = r's:\\YDS-Lab\\03-dev\\006-AUTOVPN\\allout\\routes\\常用境外IP.txt'
                if os.path.exists(ip_file):
                    with open(ip_file, 'r', encoding='utf-8') as f:
                        ip_count = len([line for line in f if line.strip() and not line.startswith('#')])
                    
                    if ip_count > last_ip_count:
                        self.log(f"📊 IP数量更新: {last_ip_count} -> {ip_count}")
                        last_ip_count = ip_count
                        last_change_time = time.time()
                        stuck_count = 0
                    elif ip_count == last_ip_count and ip_count > 0:
                        # 检查是否卡住
                        if time.time() - last_change_time > max_stuck_time:
                            stuck_count += 1
                            self.log(f"⚠️  检测到卡住 (次数: {stuck_count})")
                            
                            if stuck_count >= 2:  # 连续检测到卡住
                                self.log("🔄 尝试重启批量解析器...")
                                
                                # 杀死现有进程
                                subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], capture_output=True)
                                time.sleep(3)
                                
                                # 重新启动
                                subprocess.Popen([
                                    sys.executable, 'batch_domain_resolver.py'
                                ], cwd='s:\\YDS-Lab\\03-dev\\006-AUTOVPN\\allout\\Scripts')
                                
                                self.log("✅ 已重启批量解析器")
                                stuck_count = 0
                                last_change_time = time.time()
                
                time.sleep(30)  # 每30秒检查一次
                
            except Exception as e:
                self.log(f"自动重启监控异常: {e}")
                time.sleep(10)
    
    def monitor_system_resources(self):
        """监控系统资源"""
        self.log("💻 启动系统资源监控...")
        
        while self.running:
            try:
                # 检查CPU和内存使用情况
                result = subprocess.run([
                    'wmic', 'cpu', 'get', 'loadpercentage', '/value'
                ], capture_output=True, text=True)
                
                if 'LoadPercentage' in result.stdout:
                    import re
                    cpu_match = re.search(r'LoadPercentage=(\\d+)', result.stdout)
                    if cpu_match:
                        cpu_usage = int(cpu_match.group(1))
                        if cpu_usage > 90:
                            self.log(f"⚠️  CPU使用率过高: {cpu_usage}%")
                
                # 检查内存使用
                result = subprocess.run([
                    'wmic', 'OS', 'get', 'TotalVisibleMemorySize,FreePhysicalMemory', '/value'
                ], capture_output=True, text=True)
                
                if 'TotalVisibleMemorySize' in result.stdout:
                    mem_match = re.findall(r'(\\d+)', result.stdout)
                    if len(mem_match) >= 2:
                        total_mem = int(mem_match[0])
                        free_mem = int(mem_match[1])
                        used_percent = ((total_mem - free_mem) / total_mem) * 100
                        
                        if used_percent > 90:
                            self.log(f"⚠️  内存使用率过高: {used_percent:.1f}%")
                
                time.sleep(60)  # 每分钟检查一次
                
            except Exception as e:
                self.log(f"资源监控异常: {e}")
                time.sleep(30)
    
    def run_monitor(self):
        """运行完整监控"""
        self.log("🚀 启动后台自动监控系统")
        self.log(f"日志文件: {self.log_file}")
        
        # 启动监控线程
        threads = []
        
        # 进度监控线程
        progress_thread = threading.Thread(target=self.monitor_batch_progress)
        threads.append(progress_thread)
        
        # 自动重启线程
        restart_thread = threading.Thread(target=self.auto_restart_if_stuck)
        threads.append(restart_thread)
        
        # 资源监控线程
        resource_thread = threading.Thread(target=self.monitor_system_resources)
        threads.append(resource_thread)
        
        # 启动所有线程
        for thread in threads:
            thread.daemon = True
            thread.start()
        
        try:
            # 主监控循环
            while self.running:
                # 检查是否所有批次完成
                log_file = 'batch_domain_resolver.log'
                if os.path.exists(log_file):
                    with open(log_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    if '所有批次处理完成' in content or '解析任务全部完成' in content:
                        self.log("🎉 检测到所有批次完成！")
                        self.running = False
                        break
                
                # 检查总运行时间
                if time.time() - self.start_time > 3600:  # 1小时超时
                    self.log("⚠️  监控超时，准备退出...")
                    self.running = False
                    break
                
                time.sleep(30)  # 每30秒检查一次
            
            # 等待所有线程结束
            for thread in threads:
                thread.join(timeout=10)
            
            self.log("✅ 后台监控完成")
            
        except KeyboardInterrupt:
            self.log("用户中断监控")
            self.running = False
        except Exception as e:
            self.log(f"监控异常: {e}")
            self.running = False
        
        # 最终状态检查
        self.log("\\n" + "="*60)
        self.log("📊 最终状态总结:")
        
        # 检查IP文件
        ip_file = r's:\\YDS-Lab\\03-dev\\006-AUTOVPN\\allout\\routes\\常用境外IP.txt'
        if os.path.exists(ip_file):
            with open(ip_file, 'r', encoding='utf-8') as f:
                ip_count = len([line for line in f if line.strip() and not line.startswith('#')])
            self.log(f"✅ 最终IP数量: {ip_count}")
        
        # 检查日志
        if os.path.exists('batch_domain_resolver.log'):
            with open('batch_domain_resolver.log', 'r', encoding='utf-8') as f:
                content = f.read()
                if '完成' in content:
                    self.log("✅ 批量解析已完成")
                else:
                    self.log("⚠️  批量解析状态未知")
        
        self.log(f"📁 完整日志: {self.log_file}")
        return True

def main():
    """主函数"""
    monitor = BackgroundMonitor()
    return monitor.run_monitor()

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\\n用户中断监控")
        sys.exit(1)
    except Exception as e:
        print(f"\\n监控程序异常: {e}")
        sys.exit(1)