#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动完成域名解析和WireGuard配置脚本
监控整个流程，自动处理等待和选择
"""

import os
import sys
import time
import subprocess
import threading
import queue
import signal
from datetime import datetime

class AutoCompleteResolver:
    def __init__(self):
        self.running = True
        self.current_step = 0
        self.log_file = f"auto_complete_resolver_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self.menu_process = None
        self.output_queue = queue.Queue()
        
    def log(self, message):
        """记录日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + '\n')
    
    def run_batch_domain_resolver(self):
        """运行批量域名解析器"""
        self.log("=== 开始批量域名解析 ===")
        try:
            # 运行批量解析器
            result = subprocess.run([
                sys.executable, 'batch_domain_resolver.py'
            ], capture_output=True, text=True, cwd='s:\\YDS-Lab\\03-dev\\006-AUTOVPN\\VPN-Sel\\Scripts')
            
            if result.returncode == 0:
                self.log("✅ 批量域名解析完成")
                self.log(f"输出: {result.stdout}")
                return True
            else:
                self.log(f"❌ 批量域名解析失败: {result.stderr}")
                return False
                
        except Exception as e:
            self.log(f"❌ 批量域名解析异常: {e}")
            return False
    
    def read_menu_output(self, process):
        """读取菜单输出"""
        try:
            while self.running and process.poll() is None:
                line = process.stdout.readline()
                if line:
                    line = line.strip()
                    self.output_queue.put(line)
                    self.log(f"菜单输出: {line}")
                    
                    # 自动处理不同的菜单情况
                    self.handle_menu_output(line)
                    
        except Exception as e:
            self.log(f"读取菜单输出异常: {e}")
    
    def handle_menu_output(self, line):
        """自动处理菜单输出"""
        line_lower = line.lower()
        
        # 等待选择提示
        if '请选择功能' in line or '请输入有效选项' in line:
            self.log("检测到选择提示，自动选择批量解析功能...")
            time.sleep(1)
            # 选择选项2：批量域名解析
            if self.menu_process and self.menu_process.stdin:
                self.menu_process.stdin.write("2\n")
                self.menu_process.stdin.flush()
                self.log("已选择选项2：批量域名解析")
        
        # 检测到网络检查卡住
        elif '网络状态检查' in line or '网络连接测试' in line:
            self.log("检测到网络检查，等待完成...")
            time.sleep(5)  # 给网络检查一些时间
            
        # 检测到等待输入
        elif '按任意键继续' in line or 'press any key' in line_lower:
            self.log("检测到等待输入，自动继续...")
            if self.menu_process and self.menu_process.stdin:
                self.menu_process.stdin.write("\n")
                self.menu_process.stdin.flush()
        
        # 检测到确认提示
        elif '确认' in line and ('y/n' in line_lower or '是/否' in line):
            self.log("检测到确认提示，自动确认...")
            if self.menu_process and self.menu_process.stdin:
                self.menu_process.stdin.write("y\n")
                self.menu_process.stdin.flush()
        
        # 检测到错误
        elif '错误' in line or '失败' in line or 'error' in line_lower:
            self.log(f"检测到错误: {line}")
            
        # 检测到成功完成
        elif '完成' in line and ('解析' in line or '配置' in line):
            self.log(f"检测到完成: {line}")
    
    def run_interactive_menu(self):
        """运行交互式菜单"""
        self.log("=== 启动交互式菜单自动处理 ===")
        
        try:
            # 启动菜单进程
            self.menu_process = subprocess.Popen([
                sys.executable, 'autovpn_menu.py'
            ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, 
               stderr=subprocess.PIPE, text=True, cwd='s:\\YDS-Lab\\03-dev\\006-AUTOVPN\\VPN-Sel\\Scripts')
            
            # 启动输出读取线程
            output_thread = threading.Thread(target=self.read_menu_output, args=(self.menu_process,))
            output_thread.daemon = True
            output_thread.start()
            
            # 等待进程完成或超时
            timeout = 300  # 5分钟超时
            start_time = time.time()
            
            while self.running:
                if self.menu_process.poll() is not None:
                    self.log("菜单进程已结束")
                    break
                    
                if time.time() - start_time > timeout:
                    self.log("菜单进程超时，强制结束")
                    self.menu_process.terminate()
                    break
                    
                time.sleep(1)
            
            # 等待线程结束
            output_thread.join(timeout=5)
            
            # 获取最终结果
            return_code = self.menu_process.returncode
            self.log(f"菜单进程返回码: {return_code}")
            
            return return_code == 0
            
        except Exception as e:
            self.log(f"运行交互式菜单异常: {e}")
            return False
    
    def update_wireguard_config(self):
        """更新WireGuard配置"""
        self.log("=== 开始更新WireGuard配置 ===")
        
        try:
            # 检查IP文件
            ip_file = r's:\\YDS-Lab\\03-dev\\006-AUTOVPN\\VPN-Sel\\routes\\常用境外IP.txt'
            if not os.path.exists(ip_file):
                self.log(f"❌ IP文件不存在: {ip_file}")
                return False
            
            # 读取IP列表
            with open(ip_file, 'r', encoding='utf-8') as f:
                ips = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            self.log(f"读取到 {len(ips)} 个IP地址")
            
            # 检查WireGuard配置文件
            wg_config_file = r's:\\YDS-Lab\\03-dev\\006-AUTOVPN\\VPN-Sel\\config\\wireguard\\client\\wg0.conf'
            if not os.path.exists(wg_config_file):
                self.log(f"❌ WireGuard配置文件不存在: {wg_config_file}")
                return False
            
            # 读取现有配置
            with open(wg_config_file, 'r', encoding='utf-8') as f:
                config_content = f.read()
            
            # 更新AllowedIPs配置
            if 'AllowedIPs' in config_content:
                # 构建新的AllowedIPs行
                allowed_ips = ', '.join([f"{ip}/32" for ip in ips[:50]])  # 限制前50个IP
                new_config = config_content
                
                # 替换或添加AllowedIPs
                import re
                new_config = re.sub(
                    r'AllowedIPs\s*=\s*.*?\n',
                    f'AllowedIPs = {allowed_ips}\n',
                    config_content
                )
                
                # 写入新配置
                with open(wg_config_file, 'w', encoding='utf-8') as f:
                    f.write(new_config)
                
                self.log(f"✅ WireGuard配置已更新，包含 {len(ips[:50])} 个IP")
                return True
            else:
                self.log("❌ 配置文件中未找到AllowedIPs字段")
                return False
                
        except Exception as e:
            self.log(f"更新WireGuard配置异常: {e}")
            return False
    
    def run_complete_workflow(self):
        """运行完整工作流"""
        self.log("🚀 启动自动完成域名解析和配置工作流")
        
        # 步骤1: 批量域名解析
        self.log("\\n📋 步骤1: 批量域名解析")
        if not self.run_batch_domain_resolver():
            self.log("❌ 批量解析失败，继续尝试交互式菜单...")
        
        # 步骤2: 交互式菜单自动处理
        self.log("\\n📋 步骤2: 交互式菜单自动处理")
        menu_success = self.run_interactive_menu()
        
        # 步骤3: 更新WireGuard配置
        self.log("\\n📋 步骤3: 更新WireGuard配置")
        wg_success = self.update_wireguard_config()
        
        # 最终结果
        self.log("\\n" + "="*50)
        self.log("🎯 自动工作流完成总结:")
        self.log(f"批量解析: {'✅ 通过' if menu_success else '❌ 失败'}")
        self.log(f"交互菜单: {'✅ 通过' if menu_success else '❌ 失败'}")
        self.log(f"WireGuard配置: {'✅ 通过' if wg_success else '❌ 失败'}")
        self.log(f"日志文件: {self.log_file}")
        
        return menu_success and wg_success
    
    def signal_handler(self, signum, frame):
        """处理信号"""
        self.log(f"收到信号 {signum}，准备退出...")
        self.running = False
        if self.menu_process:
            self.menu_process.terminate()

def main():
    """主函数"""
    resolver = AutoCompleteResolver()
    
    # 注册信号处理
    signal.signal(signal.SIGINT, resolver.signal_handler)
    signal.signal(signal.SIGTERM, resolver.signal_handler)
    
    try:
        success = resolver.run_complete_workflow()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        resolver.log("用户中断操作")
        sys.exit(1)
    except Exception as e:
        resolver.log(f"主程序异常: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()