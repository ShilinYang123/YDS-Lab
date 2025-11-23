#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# 添加脚本目录到Python路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

def resolve_single_domain_ip(domain):
    """通过本地解析单个域名获取IP地址"""
    try:
        # 使用本地DNS解析
        import dns.resolver
        resolver = dns.resolver.Resolver()
        resolver.nameservers = ['8.8.8.8', '1.1.1.1']  # 使用Google和Cloudflare的DNS
        resolver.timeout = 5
        resolver.lifetime = 12
        
        print(f"正在解析域名: {domain}")
        answers = resolver.resolve(domain, 'A')
        if answers:
            ip = answers[0].address
            print(f"解析成功: {domain} -> {ip}")
            return ip
        else:
            print(f"解析失败: {domain}")
            return None
    except Exception as e:
        print(f"[错误] 域名解析失败: {e}")
        return None

if __name__ == "__main__":
    domain = "ip.sb"
    if len(sys.argv) > 1:
        domain = sys.argv[1]
    
    ip = resolve_single_domain_ip(domain)
    if ip:
        print(f"域名 {domain} 解析成功: {ip}")
    else:
        print(f"域名 {domain} 解析失败")