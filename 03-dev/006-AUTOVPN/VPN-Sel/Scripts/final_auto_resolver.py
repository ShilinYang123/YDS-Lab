#!/usr/bin/env python3
"""
最终自动域名解析和配置更新脚本
整合所有功能：批量解析、WireGuard配置更新、失败重试、监控
"""

import os
import sys
import time
import json
import socket
import logging
import subprocess
import concurrent.futures
from datetime import datetime
from typing import List, Dict, Set
import signal
import threading

# 配置日志
log_filename = f'final_auto_resolver_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 全局变量
stop_flag = threading.Event()
resolved_ips = {}  # 域名 -> IP列表
failed_domains = set()  # 解析失败的域名
success_count = 0
fail_count = 0

# 文件路径
DOMAIN_LIST_FILE = r"S:\YDS-Lab\03-dev\006-AUTOVPN\VPN-Sel\routes\需要获取IP的域名列表.txt"
FAILED_DOMAINS_FILE = r"S:\YDS-Lab\03-dev\006-AUTOVPN\VPN-Sel\routes\解析失败域名列表.txt"
IP_OUTPUT_FILE = r"S:\YDS-Lab\03-dev\006-AUTOVPN\VPN-Sel\routes\常用境外IP.txt"
WIREGUARD_CONFIG_FILE = r"S:\YDS-Lab\03-dev\006-AUTOVPN\VPN-Sel\config\wireguard\client\client.conf"

# DNS服务器列表（优化选择）
DNS_SERVERS = [
    "8.8.8.8",      # Google
    "8.8.4.4",      # Google
    "1.1.1.1",      # Cloudflare
    "1.0.0.1",      # Cloudflare
    "208.67.222.222", # OpenDNS
    "208.67.220.220", # OpenDNS
    "9.9.9.9",      # Quad9
    "149.112.112.112" # Quad9
]

def signal_handler(signum, frame):
    """处理中断信号"""
    logger.info("收到中断信号，正在优雅退出...")
    stop_flag.set()
    sys.exit(0)

def load_domains() -> List[str]:
    """加载域名列表"""
    try:
        with open(DOMAIN_LIST_FILE, 'r', encoding='utf-8') as f:
            domains = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        logger.info(f"加载了 {len(domains)} 个域名")
        return domains
    except Exception as e:
        logger.error(f"加载域名列表失败: {e}")
        return []

def resolve_domain_with_retry(domain: str, max_retries: int = 3) -> List[str]:
    """解析域名，带重试机制"""
    global success_count, fail_count
    
    for retry in range(max_retries):
        if stop_flag.is_set():
            return []
            
        try:
            # 使用socket库进行DNS解析
            ips = []
            
            # 尝试获取IPv4地址
            try:
                result = socket.gethostbyname_ex(domain)
                ips.extend(result[2])
            except:
                pass
            
            # 尝试获取IPv6地址
            try:
                result = socket.getaddrinfo(domain, None, socket.AF_INET6)
                for res in result:
                    ip = res[4][0]
                    if ip not in ips:
                        ips.append(ip)
            except:
                pass
            
            if ips:
                success_count += 1
                logger.info(f"✅ {domain} -> {ips}")
                return ips
            else:
                time.sleep(1)  # 短暂延迟后重试
                
        except Exception as e:
            logger.warning(f"解析 {domain} 失败 (尝试 {retry + 1}/{max_retries}): {e}")
            time.sleep(2 ** retry)  # 指数退避
    
    fail_count += 1
    failed_domains.add(domain)
    logger.error(f"❌ {domain} 解析失败")
    return []

def batch_resolve_domains(domains: List[str], batch_size: int = 20) -> Dict[str, List[str]]:
    """批量解析域名"""
    global resolved_ips
    
    logger.info(f"开始批量解析 {len(domains)} 个域名，每批 {batch_size} 个")
    
    total_batches = (len(domains) + batch_size - 1) // batch_size
    
    for batch_idx in range(total_batches):
        if stop_flag.is_set():
            break
            
        start_idx = batch_idx * batch_size
        end_idx = min(start_idx + batch_size, len(domains))
        batch_domains = domains[start_idx:end_idx]
        
        logger.info(f"处理批次 {batch_idx + 1}/{total_batches} ({len(batch_domains)} 个域名)")
        
        # 使用线程池并发解析
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_domain = {executor.submit(resolve_domain_with_retry, domain): domain 
                              for domain in batch_domains}
            
            for future in concurrent.futures.as_completed(future_to_domain):
                if stop_flag.is_set():
                    break
                    
                domain = future_to_domain[future]
                try:
                    ips = future.result()
                    if ips:
                        resolved_ips[domain] = ips
                except Exception as e:
                    logger.error(f"解析 {domain} 时发生异常: {e}")
                    failed_domains.add(domain)
        
        # 批次间等待时间优化
        if batch_idx < total_batches - 1:  # 不是最后一批
            wait_time = min(3, max(1, len(batch_domains) // 10))  # 动态等待时间
            logger.info(f"等待 {wait_time} 秒后继续...")
            time.sleep(wait_time)
    
    return resolved_ips

def save_failed_domains():
    """保存解析失败的域名"""
    try:
        with open(FAILED_DOMAINS_FILE, 'w', encoding='utf-8') as f:
            f.write(f"# 域名解析失败列表\n")
            f.write(f"# 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# 总计: {len(failed_domains)} 个\n\n")
            
            for domain in sorted(failed_domains):
                f.write(f"{domain}\n")
        
        logger.info(f"已保存 {len(failed_domains)} 个失败域名到 {FAILED_DOMAINS_FILE}")
    except Exception as e:
        logger.error(f"保存失败域名列表失败: {e}")

def save_resolved_ips():
    """保存解析到的IP地址"""
    try:
        all_ips = set()
        for ips in resolved_ips.values():
            all_ips.update(ips)
        
        with open(IP_OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(f"# 常用境外IP地址\n")
            f.write(f"# 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# 域名总数: {len(resolved_ips)}\n")
            f.write(f"# IP总数: {len(all_ips)}\n\n")
            
            for ip in sorted(all_ips):
                f.write(f"{ip}\n")
        
        logger.info(f"已保存 {len(all_ips)} 个IP地址到 {IP_OUTPUT_FILE}")
    except Exception as e:
        logger.error(f"保存IP地址失败: {e}")

def update_wireguard_config():
    """更新WireGuard配置文件"""
    try:
        if not os.path.exists(WIREGUARD_CONFIG_FILE):
            logger.warning(f"WireGuard配置文件不存在: {WIREGUARD_CONFIG_FILE}")
            return False
        
        # 读取现有配置
        with open(WIREGUARD_CONFIG_FILE, 'r', encoding='utf-8') as f:
            config_lines = f.readlines()
        
        # 找到 [Peer] 部分的 AllowedIPs 行
        peer_section = False
        updated = False
        
        for i, line in enumerate(config_lines):
            line_stripped = line.strip()
            
            if line_stripped.startswith('[Peer]'):
                peer_section = True
                continue
                
            if peer_section and line_stripped.startswith('AllowedIPs'):
                # 获取所有解析到的IP
                all_ips = set()
                for ips in resolved_ips.values():
                    all_ips.update(ips)
                
                if all_ips:
                    # 构建新的 AllowedIPs 值
                    existing_ips = line_stripped.replace('AllowedIPs = ', '').split(',')
                    existing_ips = [ip.strip() for ip in existing_ips if ip.strip()]
                    
                    # 合并现有IP和新IP
                    combined_ips = list(set(existing_ips + list(all_ips)))
                    
                    # 限制IP数量避免配置过大
                    if len(combined_ips) > 100:
                        combined_ips = combined_ips[:100]
                        logger.warning("IP数量过多，只保留前100个")
                    
                    new_allowed_ips = ', '.join(combined_ips)
                    config_lines[i] = f"AllowedIPs = {new_allowed_ips}\n"
                    updated = True
                    logger.info(f"更新AllowedIPs: {len(combined_ips)} 个IP")
                
                break
        
        if updated:
            # 保存更新后的配置
            with open(WIREGUARD_CONFIG_FILE, 'w', encoding='utf-8') as f:
                f.writelines(config_lines)
            
            logger.info(f"✅ WireGuard配置文件已更新: {WIREGUARD_CONFIG_FILE}")
            return True
        else:
            logger.warning("未找到需要更新的配置项")
            return False
            
    except Exception as e:
        logger.error(f"更新WireGuard配置失败: {e}")
        return False

def monitor_progress():
    """监控进度线程"""
    while not stop_flag.is_set():
        total = success_count + fail_count
        if total > 0:
            success_rate = (success_count / total) * 100
            logger.info(f"📊 进度: {total} 已处理, {success_count} 成功, {fail_count} 失败, 成功率: {success_rate:.1f}%")
        
        time.sleep(30)  # 每30秒报告一次

def main():
    """主函数"""
    logger.info("🚀 启动最终自动域名解析和配置更新系统")
    logger.info(f"日志文件: {log_filename}")
    
    # 设置信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 1. 加载域名列表
        domains = load_domains()
        if not domains:
            logger.error("没有域名需要解析")
            return
        
        # 2. 启动进度监控线程
        monitor_thread = threading.Thread(target=monitor_progress, daemon=True)
        monitor_thread.start()
        
        # 3. 批量解析域名
        logger.info("步骤1: 开始批量域名解析")
        resolve_results = batch_resolve_domains(domains)
        
        if not resolve_results:
            logger.error("域名解析失败")
            return
        
        logger.info(f"✅ 域名解析完成: {len(resolve_results)} 个成功, {len(failed_domains)} 个失败")
        
        # 4. 保存失败域名
        if failed_domains:
            save_failed_domains()
        
        # 5. 保存解析到的IP
        save_resolved_ips()
        
        # 6. 更新WireGuard配置
        logger.info("步骤2: 更新WireGuard配置")
        if update_wireguard_config():
            logger.info("✅ WireGuard配置更新成功")
        else:
            logger.warning("WireGuard配置更新失败或跳过")
        
        # 7. 最终统计
        total = success_count + fail_count
        success_rate = (success_count / total * 100) if total > 0 else 0
        
        logger.info("=" * 60)
        logger.info("🎉 最终自动域名解析和配置更新完成!")
        logger.info(f"📈 总计: {total} 个域名")
        logger.info(f"✅ 成功: {success_count} 个")
        logger.info(f"❌ 失败: {fail_count} 个")
        logger.info(f"📊 成功率: {success_rate:.1f}%")
        logger.info(f"📝 日志文件: {log_filename}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"主程序异常: {e}")
    finally:
        stop_flag.set()

if __name__ == "__main__":
    main()