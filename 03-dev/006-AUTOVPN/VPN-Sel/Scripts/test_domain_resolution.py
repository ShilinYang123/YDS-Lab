#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# 添加脚本目录到Python路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

def test_domain_resolution(domain):
    """测试域名解析"""
    print(f"正在测试域名解析: {domain}")
    
    # 1. 使用系统的nslookup命令
    print("\n1. 使用nslookup命令:")
    try:
        import subprocess
        result = subprocess.run(['nslookup', domain], capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("错误信息:", result.stderr)
    except Exception as e:
        print(f"nslookup命令执行失败: {e}")
    
    # 2. 使用Python的socket模块
    print("\n2. 使用Python的socket模块:")
    try:
        import socket
        ip = socket.gethostbyname(domain)
        print(f"解析结果: {ip}")
    except Exception as e:
        print(f"socket解析失败: {e}")
    
    # 3. 使用dnspython库（如果可用）
    print("\n3. 使用dnspython库:")
    try:
        import dns.resolver
        resolver = dns.resolver.Resolver()
        resolver.nameservers = ['8.8.8.8', '1.1.1.1']  # 使用Google和Cloudflare的DNS
        answers = resolver.resolve(domain, 'A')
        print("解析结果:")
        for rdata in answers:
            print(f"  {rdata.address}")
    except ImportError:
        print("dnspython库未安装")
    except Exception as e:
        print(f"dnspython解析失败: {e}")

if __name__ == "__main__":
    domain = "ip.sb"
    if len(sys.argv) > 1:
        domain = sys.argv[1]
    
    test_domain_resolution(domain)