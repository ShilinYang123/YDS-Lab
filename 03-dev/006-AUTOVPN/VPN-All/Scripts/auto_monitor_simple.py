#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版自动监控脚本 - 直接运行批量解析
"""

import os
import sys
import time
import subprocess
from datetime import datetime

def log(message):
    """记录日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")
    with open('auto_monitor_simple.log', 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")

def run_batch_resolver_with_retry():
    """运行批量解析器，带重试机制"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        log(f"尝试运行批量解析器 (第{retry_count+1}次)...")
        
        try:
            # 直接运行批量解析器
            result = subprocess.run([
                sys.executable, 'batch_domain_resolver.py'
            ], capture_output=True, text=True, cwd='s:\\YDS-Lab\\03-dev\\006-AUTOVPN\\allout\\Scripts', timeout=300)
            
            log(f"返回码: {result.returncode}")
            log(f"标准输出: {result.stdout}")
            
            if result.stderr:
                log(f"错误输出: {result.stderr}")
            
            if result.returncode == 0:
                log("✅ 批量解析成功完成")
                return True
            else:
                log(f"❌ 批量解析失败，准备重试...")
                retry_count += 1
                time.sleep(5)
                
        except subprocess.TimeoutExpired:
            log("❌ 批量解析超时，准备重试...")
            retry_count += 1
            time.sleep(5)
        except Exception as e:
            log(f"❌ 批量解析异常: {e}")
            retry_count += 1
            time.sleep(5)
    
    return False

def check_and_update_wireguard():
    """检查并更新WireGuard配置"""
    log("=== 检查WireGuard配置 ===")
    
    try:
        # 检查IP文件
        ip_file = r's:\\YDS-Lab\\03-dev\\006-AUTOVPN\\allout\\routes\\常用境外IP.txt'
        if not os.path.exists(ip_file):
            log(f"❌ IP文件不存在: {ip_file}")
            return False
        
        # 读取IP数量
        with open(ip_file, 'r', encoding='utf-8') as f:
            ips = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        log(f"✅ 发现 {len(ips)} 个IP地址")
        
        # 检查WireGuard配置文件
        wg_config_file = r's:\\YDS-Lab\\03-dev\\006-AUTOVPN\\allout\\config\\wireguard\\client\\wg0.conf'
        if not os.path.exists(wg_config_file):
            log(f"❌ WireGuard配置文件不存在: {wg_config_file}")
            return False
        
        # 读取现有配置
        with open(wg_config_file, 'r', encoding='utf-8') as f:
            config_content = f.read()
        
        log("✅ WireGuard配置已存在")
        return True
        
    except Exception as e:
        log(f"检查WireGuard配置异常: {e}")
        return False

def main():
    """主函数"""
    log("🚀 启动自动域名解析和配置监控")
    
    # 步骤1: 运行批量域名解析
    log("\\n📋 步骤1: 批量域名解析")
    resolver_success = run_batch_resolver_with_retry()
    
    if not resolver_success:
        log("❌ 批量解析失败，尝试直接更新配置...")
    
    # 步骤2: 检查并更新配置
    log("\\n📋 步骤2: 检查配置状态")
    config_success = check_and_update_wireguard()
    
    # 最终结果
    log("\\n" + "="*50)
    log("🎯 自动监控完成总结:")
    log(f"批量解析: {'✅ 通过' if resolver_success else '❌ 失败'}")
    log(f"配置检查: {'✅ 通过' if config_success else '❌ 失败'}")
    log(f"日志文件: auto_monitor_simple.log")
    
    if resolver_success and config_success:
        log("🎉 全部流程完成！系统已就绪")
    else:
        log("⚠️  部分流程失败，请检查日志")
    
    return 0 if (resolver_success and config_success) else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        log("用户中断操作")
        sys.exit(1)
    except Exception as e:
        log(f"主程序异常: {e}")
        sys.exit(1)