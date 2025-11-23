#!/usr/bin/env python3
"""
快速IPv6域名验证脚本 - 简化版
专注于测试最可靠的IPv6域名
"""

import dns.resolver
import socket
import time
import sys
from typing import List, Dict

def quick_ipv6_test(domain: str) -> Dict:
    """快速测试域名IPv6支持"""
    result = {
        "domain": domain,
        "supports_ipv6": False,
        "ipv6_addresses": [],
        "ipv4_addresses": [],
        "errors": []
    }
    
    try:
        # 使用Google DNS测试AAAA记录
        resolver = dns.resolver.Resolver()
        resolver.nameservers = ["8.8.8.8"]
        resolver.timeout = 3
        resolver.lifetime = 5
        
        # 测试AAAA记录 (IPv6)
        try:
            ipv6_answers = resolver.resolve(domain, "AAAA")
            for rdata in ipv6_answers:
                ipv6_addr = rdata.address
                if ipv6_addr and ipv6_addr not in result["ipv6_addresses"]:
                    result["ipv6_addresses"].append(ipv6_addr)
                    result["supports_ipv6"] = True
        except Exception as e:
            result["errors"].append(f"AAAA查询失败: {str(e)}")
        
        # 测试A记录 (IPv4) 用于对比
        try:
            ipv4_answers = resolver.resolve(domain, "A")
            for rdata in ipv4_answers:
                ipv4_addr = rdata.address
                if ipv4_addr and ipv4_addr not in result["ipv4_addresses"]:
                    result["ipv4_addresses"].append(ipv4_addr)
        except Exception as e:
            result["errors"].append(f"A查询失败: {str(e)}")
            
    except Exception as e:
        result["errors"].append(f"DNS解析失败: {str(e)}")
    
    return result

def main():
    """主函数 - 测试核心IPv6域名"""
    
    # 核心IPv6测试域名列表 - 这些是最可能支持IPv6的域名
    core_ipv6_domains = [
        # Google IPv6专用域名
        "ipv6.google.com",
        
        # Cloudflare - 已知支持IPv6
        "cloudflare.com",
        "www.cloudflare.com",
        "1.1.1.1",
        
        # IPv6测试专用域名
        "test-ipv6.com",
        "ipv6-test.com", 
        "whatismyipv6.com",
        "ipv6-test.nl",
        "testmyipv6.com",
        
        # 其他可能支持IPv6的域名
        "wikipedia.org",
        "www.wikipedia.org",
        "github.com",
        "www.github.com"
    ]
    
    print("快速IPv6域名验证工具")
    print("=" * 30)
    print(f"将测试 {len(core_ipv6_domains)} 个核心IPv6域名\n")
    
    ipv6_supported = []
    ipv6_not_supported = []
    
    for i, domain in enumerate(core_ipv6_domains, 1):
        print(f"正在测试 {i}/{len(core_ipv6_domains)}: {domain}")
        
        result = quick_ipv6_test(domain)
        
        if result["supports_ipv6"] and result["ipv6_addresses"]:
            ipv6_supported.append(result)
            print(f"  ✅ {domain} 支持IPv6 - 地址: {result['ipv6_addresses']}")
        else:
            ipv6_not_supported.append(result)
            print(f"  ❌ {domain} 不支持IPv6")
        
        # 短暂延迟避免过快
        time.sleep(0.3)
    
    # 生成结果文件
    print(f"\n验证完成!")
    print(f"支持IPv6的域名: {len(ipv6_supported)} 个")
    print(f"不支持IPv6的域名: {len(ipv6_not_supported)} 个")
    
    # 保存可靠的IPv6域名列表
    reliable_list_file = "..\\routes\\reliable_ipv6_domains.txt"
    with open(reliable_list_file, 'w', encoding='utf-8') as f:
        for domain_info in ipv6_supported:
            f.write(f"{domain_info['domain']}\n")
    
    print(f"可靠的IPv6域名列表已保存到: {reliable_list_file}")
    
    # 生成详细报告
    report_file = "..\\routes\\validated_ipv6_domains.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("IPv6域名验证报告\n")
        f.write("=" * 50 + "\n\n")
        
        f.write(f"总计测试域名: {len(core_ipv6_domains)} 个\n")
        f.write(f"支持IPv6的域名: {len(ipv6_supported)} 个\n")
        f.write(f"不支持IPv6的域名: {len(ipv6_not_supported)} 个\n\n")
        
        if ipv6_supported:
            f.write("支持IPv6的域名列表:\n")
            f.write("-" * 30 + "\n")
            
            for domain_info in ipv6_supported:
                domain = domain_info["domain"]
                ipv6_addrs = domain_info["ipv6_addresses"]
                
                f.write(f"\n域名: {domain}\n")
                f.write(f"IPv6地址: {', '.join(ipv6_addrs)}\n")
        
        if ipv6_not_supported:
            f.write(f"\n不支持IPv6的域名: {len(ipv6_not_supported)} 个\n")
            for domain_info in ipv6_not_supported:
                f.write(f"  - {domain_info['domain']}\n")
    
    print(f"详细报告已保存到: {report_file}")
    
    # 显示统计信息
    if len(core_ipv6_domains) > 0:
        support_rate = (len(ipv6_supported) / len(core_ipv6_domains)) * 100
        print(f"IPv6支持率: {support_rate:.1f}%")
    
    return ipv6_supported

if __name__ == "__main__":
    main()