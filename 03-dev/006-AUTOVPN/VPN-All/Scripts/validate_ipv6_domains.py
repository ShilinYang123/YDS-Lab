#!/usr/bin/env python3
"""
IPv6域名验证脚本
用于验证域名是否真实支持IPv6，并收集可靠的IPv6域名列表
"""

import dns.resolver
import socket
import time
import sys
from typing import List, Dict, Tuple

def test_domain_ipv6_support(domain: str, timeout: int = 5) -> Dict:
    """测试域名是否支持IPv6"""
    result = {
        "domain": domain,
        "supports_ipv6": False,
        "ipv6_addresses": [],
        "ipv4_addresses": [],
        "connectivity_test": {
            "ipv6_http_reachable": False,
            "ipv6_https_reachable": False,
            "ipv4_http_reachable": False,
            "ipv4_https_reachable": False
        },
        "dns_servers_tested": [],
        "errors": []
    }
    
    # 测试多个DNS服务器
    dns_servers = [
        ("Google", "8.8.8.8"),
        ("Cloudflare", "1.1.1.1"),
        ("Quad9", "9.9.9.9"),
        ("OpenDNS", "208.67.222.222")
    ]
    
    for dns_name, dns_server in dns_servers:
        try:
            resolver = dns.resolver.Resolver()
            resolver.nameservers = [dns_server]
            resolver.timeout = timeout
            resolver.lifetime = timeout * 2
            
            # 测试AAAA记录 (IPv6)
            try:
                ipv6_answers = resolver.resolve(domain, "AAAA")
                for rdata in ipv6_answers:
                    ipv6_addr = rdata.address
                    if ipv6_addr and ipv6_addr not in result["ipv6_addresses"]:
                        result["ipv6_addresses"].append(ipv6_addr)
                        result["supports_ipv6"] = True
            except Exception as e:
                result["errors"].append(f"{dns_name} AAAA查询失败: {str(e)}")
            
            # 测试A记录 (IPv4)
            try:
                ipv4_answers = resolver.resolve(domain, "A")
                for rdata in ipv4_answers:
                    ipv4_addr = rdata.address
                    if ipv4_addr and ipv4_addr not in result["ipv4_addresses"]:
                        result["ipv4_addresses"].append(ipv4_addr)
            except Exception as e:
                result["errors"].append(f"{dns_name} A查询失败: {str(e)}")
            
            result["dns_servers_tested"].append(dns_name)
            
        except Exception as e:
            result["errors"].append(f"DNS服务器{dns_name}测试失败: {str(e)}")
    
    # 如果找到IPv6地址，进行连接性测试
    if result["ipv6_addresses"]:
        for ipv6_addr in result["ipv6_addresses"]:
            # 测试HTTP连接 (端口80)
            try:
                sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
                sock.settimeout(3)
                result_code = sock.connect_ex((ipv6_addr, 80))
                sock.close()
                if result_code == 0:
                    result["connectivity_test"]["ipv6_http_reachable"] = True
                    break
            except Exception as e:
                result["errors"].append(f"IPv6 HTTP连接测试失败: {str(e)}")
            
            # 测试HTTPS连接 (端口443)
            try:
                sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
                sock.settimeout(3)
                result_code = sock.connect_ex((ipv6_addr, 443))
                sock.close()
                if result_code == 0:
                    result["connectivity_test"]["ipv6_https_reachable"] = True
                    break
            except Exception as e:
                result["errors"].append(f"IPv6 HTTPS连接测试失败: {str(e)}")
    
    # 如果找到IPv4地址，也进行连接性测试作为对比
    if result["ipv4_addresses"]:
        for ipv4_addr in result["ipv4_addresses"]:
            # 测试HTTP连接 (端口80)
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                result_code = sock.connect_ex((ipv4_addr, 80))
                sock.close()
                if result_code == 0:
                    result["connectivity_test"]["ipv4_http_reachable"] = True
                    break
            except Exception as e:
                result["errors"].append(f"IPv4 HTTP连接测试失败: {str(e)}")
            
            # 测试HTTPS连接 (端口443)
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                result_code = sock.connect_ex((ipv4_addr, 443))
                sock.close()
                if result_code == 0:
                    result["connectivity_test"]["ipv4_https_reachable"] = True
                    break
            except Exception as e:
                result["errors"].append(f"IPv4 HTTPS连接测试失败: {str(e)}")
    
    return result

def validate_ipv6_domains(domains: List[str]) -> Tuple[List[Dict], List[Dict]]:
    """验证一批域名的IPv6支持情况"""
    ipv6_supported = []
    ipv6_not_supported = []
    
    print(f"开始验证 {len(domains)} 个域名的IPv6支持情况...")
    
    for i, domain in enumerate(domains, 1):
        print(f"正在测试 {i}/{len(domains)}: {domain}")
        
        result = test_domain_ipv6_support(domain)
        
        if result["supports_ipv6"] and result["ipv6_addresses"]:
            ipv6_supported.append(result)
            print(f"  ✅ {domain} 支持IPv6 - 地址: {result['ipv6_addresses']}")
            
            # 显示连接性测试结果
            connectivity = result["connectivity_test"]
            if connectivity["ipv6_http_reachable"]:
                print(f"     🌐 IPv6 HTTP可连接")
            if connectivity["ipv6_https_reachable"]:
                print(f"     🔒 IPv6 HTTPS可连接")
        else:
            ipv6_not_supported.append(result)
            print(f"  ❌ {domain} 不支持IPv6")
        
        # 短暂延迟避免过快
        time.sleep(0.5)
    
    return ipv6_supported, ipv6_not_supported

def generate_ipv6_domain_report(supported_domains: List[Dict], output_file: str):
    """生成IPv6域名验证报告"""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("IPv6域名验证报告\n")
        f.write("=" * 50 + "\n\n")
        
        f.write(f"总计测试域名: {len(supported_domains)} 个\n")
        f.write(f"支持IPv6的域名: {len(supported_domains)} 个\n\n")
        
        f.write("支持IPv6的域名列表:\n")
        f.write("-" * 30 + "\n")
        
        for domain_info in supported_domains:
            domain = domain_info["domain"]
            ipv6_addrs = domain_info["ipv6_addresses"]
            connectivity = domain_info["connectivity_test"]
            
            f.write(f"\n域名: {domain}\n")
            f.write(f"IPv6地址: {', '.join(ipv6_addrs)}\n")
            
            # 连接性状态
            conn_status = []
            if connectivity["ipv6_http_reachable"]:
                conn_status.append("HTTP可连接")
            if connectivity["ipv6_https_reachable"]:
                conn_status.append("HTTPS可连接")
            
            if conn_status:
                f.write(f"连接状态: {', '.join(conn_status)}\n")
            else:
                f.write("连接状态: 无法连接\n")
            
            if domain_info["errors"]:
                f.write(f"错误信息: {'; '.join(domain_info['errors'])}\n")

def main():
    """主函数"""
    # 已知的IPv6测试域名列表
    test_domains = [
        # Google服务
        "google.com",
        "www.google.com", 
        "ipv6.google.com",
        "mail.google.com",
        "drive.google.com",
        
        # Cloudflare
        "cloudflare.com",
        "www.cloudflare.com",
        "1.1.1.1",
        
        # Facebook/Meta
        "facebook.com",
        "www.facebook.com",
        "fbcdn.net",
        
        # Microsoft
        "microsoft.com",
        "www.microsoft.com",
        "outlook.com",
        
        # 其他知名IPv6支持域名
        "wikipedia.org",
        "www.wikipedia.org",
        "github.com",
        "www.github.com",
        "stackoverflow.com",
        "youtube.com",
        "www.youtube.com",
        "linkedin.com",
        "www.linkedin.com",
        "twitter.com",
        "x.com",
        
        # CDN和云服务
        "akamai.com",
        "fastly.com",
        "amazon.com",
        "aws.amazon.com",
        
        # 测试和验证域名
        "test-ipv6.com",
        "ipv6-test.com",
        "whatismyipv6.com"
    ]
    
    print("IPv6域名验证工具")
    print("=" * 30)
    print(f"将测试 {len(test_domains)} 个域名的IPv6支持情况\n")
    
    # 验证域名
    supported, not_supported = validate_ipv6_domains(test_domains)
    
    # 生成报告
    report_file = "..\\routes\\validated_ipv6_domains.txt"
    generate_ipv6_domain_report(supported, report_file)
    
    print(f"\n验证完成!")
    print(f"支持IPv6的域名: {len(supported)} 个")
    print(f"不支持IPv6的域名: {len(not_supported)} 个")
    print(f"详细报告已保存到: {report_file}")
    
    # 同时生成简单的域名列表文件
    simple_list_file = "..\\routes\\reliable_ipv6_domains.txt"
    with open(simple_list_file, 'w', encoding='utf-8') as f:
        for domain_info in supported:
            f.write(f"{domain_info['domain']}\n")
    
    print(f"简洁域名列表已保存到: {simple_list_file}")
    
    # 显示一些统计信息
    print(f"\nIPv6支持统计:")
    total_tested = len(supported) + len(not_supported)
    if total_tested > 0:
        support_rate = (len(supported) / total_tested) * 100
        print(f"IPv6支持率: {support_rate:.1f}%")

if __name__ == "__main__":
    main()