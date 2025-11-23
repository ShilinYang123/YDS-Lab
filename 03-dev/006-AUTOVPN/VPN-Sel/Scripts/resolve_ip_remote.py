#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import dns.resolver
import dns.exception
import time
import os
import sys
import json
import logging
import paramiko
from typing import List, Dict, Optional, Tuple

# 新增：TCP连接测试相关配置
CONNECTIVITY_PORTS_TO_CHECK = [80, 443]
CONNECTIVITY_TIMEOUT_SEC = 2  # Short timeout for TCP connect

# IPv6 DNS服务器列表（用于AAAA记录验证）
DNS_SERVERS_IPV6 = [
    '8.8.8.8',      # Google
    '1.1.1.1',      # Cloudflare  
    '9.9.9.9',      # Quad9
    '208.67.222.222' # OpenDNS
]

# DNS配置
DNS_TIMEOUT_SEC = 5
DNS_LIFETIME_SEC = 12

# 虚拟环境配置
VENV_DIR = "autovpn_venv"
VENV_PYTHON_PATH = os.path.join(VENV_DIR, "bin", "python3")

# IPv6配置
IPv6_ENABLE = False  # 默认禁用IPv6支持
AAAA_RECORD_ENABLE = False  # 默认禁用AAAA记录查询

# 日志配置
logger = None

def setup_logging():
    """设置日志配置"""
    global logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logger = logging.getLogger(__name__)
    return logger

def log_aaaa_record_statistics(ipv6_addresses, domain, dns_server, query_time):
    """增强AAAA记录查询日志，添加详细的IPv6地址发现统计"""
    global logger
    
    if not logger:
        return
    
    # 统计不同类型的IPv6地址
    ipv4_mapped = 0  # IPv4映射地址 (::ffff:0:0/96)
    unique_local = 0  # 唯一本地地址 (fc00::/7)
    link_local = 0     # 链路本地地址 (fe80::/10)
    multicast = 0      # 多播地址 (ff00::/8)
    global_unicast = 0 # 全球单播地址
    
    for ipv6 in ipv6_addresses:
        if ipv6.startswith("::ffff:"):
            ipv4_mapped += 1
        elif ipv6.startswith("fc") or ipv6.startswith("fd"):
            unique_local += 1
        elif ipv6.startswith("fe80"):
            link_local += 1
        elif ipv6.startswith("ff"):
            multicast += 1
        else:
            global_unicast += 1
    
    total_ipv6 = len(ipv6_addresses)
    
    # 记录详细统计信息
    logger.info(f"🔍 AAAA记录统计 - 域名: {domain}")
    logger.info(f"   DNS服务器: {dns_server} (查询耗时: {query_time:.3f}s)")
    logger.info(f"   IPv6地址总数: {total_ipv6}")
    logger.info(f"   全球单播地址: {global_unicast}")
    logger.info(f"   IPv4映射地址: {ipv4_mapped}")
    logger.info(f"   唯一本地地址: {unique_local}")
    logger.info(f"   链路本地地址: {link_local}")
    logger.info(f"   多播地址: {multicast}")
    
    # 记录具体的IPv6地址
    if ipv6_addresses:
        logger.info(f"   发现的IPv6地址: {', '.join(ipv6_addresses[:5])}{'...' if len(ipv6_addresses) > 5 else ''}")

def validate_ipv6_connectivity(ipv6_addresses, domain, timeout=5):
    """验证IPv6地址的连接性"""
    
    if not ipv6_addresses:
        return False, 0, []
    
    successful_connections = 0
    connection_results = []
    
    for ipv6_addr in ipv6_addresses:
        result = {
            "ipv6": ipv6_addr,
            "connectable": False,
            "ports_tested": [],
            "error": None
        }
        
        try:
            # 测试常用端口
            for port in [80, 443]:
                sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                
                try:
                    result_code = sock.connect_ex((ipv6_addr, port))
                    if result_code == 0:
                        result["connectable"] = True
                        result["ports_tested"].append(port)
                        successful_connections += 1
                        logger.info(f"✅ IPv6连接测试成功 - {domain} [{ipv6_addr}]:{port}")
                    else:
                        logger.debug(f"❌ IPv6连接测试失败 - {domain} [{ipv6_addr}]:{port} (错误码: {result_code})")
                except Exception as e:
                    logger.debug(f"❌ IPv6连接测试异常 - {domain} [{ipv6_addr}]:{port} - {e}")
                finally:
                    sock.close()
                    
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"❌ IPv6连接测试严重错误 - {domain} [{ipv6_addr}] - {e}")
        
        connection_results.append(result)
    
    success_rate = (successful_connections / len(ipv6_addresses)) if ipv6_addresses else 0
    overall_connectable = success_rate >= 0.5  # 50%成功率认为整体可连接
    
    logger.info(f"📊 IPv6连接性测试统计 - {domain}: {successful_connections}/{len(ipv6_addresses)} 成功 (成功率: {success_rate:.1%})")
    
    return overall_connectable, success_rate, connection_results


def validate_dns_servers_ipv6_capability():
    """验证不同DNS服务器的AAAA记录返回能力"""
    
    test_domains = [
        "ipv6.google.com",
        "cloudflare.com", 
        "wikipedia.org",
        "testmyipv6.com"
    ]
    
    logger.info("🔍 开始验证DNS服务器IPv6 AAAA记录支持能力...")
    
    results = {}
    
    for dns_server in DNS_SERVERS_IPV6:
        logger.info(f"\n📡 测试DNS服务器: {dns_server}")
        server_results = {
            "total_queries": 0,
            "successful_queries": 0,
            "total_ipv6_addresses": 0,
            "response_times": [],
            "domain_results": {}
        }
        
        resolver = dns.resolver.Resolver()
        resolver.nameservers = [dns_server]
        resolver.timeout = DNS_TIMEOUT_SEC
        resolver.lifetime = DNS_LIFETIME_SEC
        
        for domain in test_domains:
            server_results["total_queries"] += 1
            start_time = time.time()
            
            try:
                # 查询AAAA记录
                answers = resolver.resolve(domain, 'AAAA')
                ipv6_addresses = [rdata.address for rdata in answers]
                
                query_time = time.time() - start_time
                server_results["response_times"].append(query_time)
                
                if ipv6_addresses:
                    server_results["successful_queries"] += 1
                    server_results["total_ipv6_addresses"] += len(ipv6_addresses)
                    server_results["domain_results"][domain] = {
                        "success": True,
                        "ipv6_count": len(ipv6_addresses),
                        "ipv6_addresses": ipv6_addresses,
                        "response_time": query_time
                    }
                    
                    # 记录详细统计
                    log_aaaa_record_statistics(ipv6_addresses, domain, dns_server, query_time)
                    
                else:
                    server_results["domain_results"][domain] = {
                        "success": False,
                        "error": "No AAAA records found"
                    }
                    logger.info(f"   ❌ {domain}: 未找到AAAA记录")
                    
            except dns.resolver.NXDOMAIN:
                query_time = time.time() - start_time
                server_results["domain_results"][domain] = {
                    "success": False,
                    "error": "NXDOMAIN"
                }
                logger.info(f"   ❌ {domain}: 域名不存在 (NXDOMAIN)")
                
            except dns.exception.Timeout:
                query_time = time.time() - start_time
                server_results["domain_results"][domain] = {
                    "success": False,
                    "error": "Timeout"
                }
                logger.info(f"   ❌ {domain}: 查询超时")
                
            except dns.resolver.NoAnswer:
                query_time = time.time() - start_time
                server_results["domain_results"][domain] = {
                    "success": False,
                    "error": "NoAnswer"
                }
                logger.info(f"   ❌ {domain}: 无响应 (NoAnswer)")
                
            except Exception as e:
                query_time = time.time() - start_time
                server_results["domain_results"][domain] = {
                    "success": False,
                    "error": str(e)
                }
                logger.info(f"   ❌ {domain}: 错误 - {type(e).__name__}: {e}")
            
            # 短暂延迟避免过快查询
            time.sleep(0.2)
        
        results[dns_server] = server_results
        
        # 计算统计信息
        avg_response_time = sum(server_results["response_times"]) / len(server_results["response_times"]) if server_results["response_times"] else 0
        success_rate = (server_results["successful_queries"] / server_results["total_queries"] * 100) if server_results["total_queries"] > 0 else 0
        
        logger.info(f"\n📊 DNS服务器 {dns_server} 统计:")
        logger.info(f"   成功率: {success_rate:.1f}% ({server_results['successful_queries']}/{server_results['total_queries']})")
        logger.info(f"   平均响应时间: {avg_response_time:.3f}s")
        logger.info(f"   发现IPv6地址总数: {server_results['total_ipv6_addresses']}")
    
    # 生成综合报告
    logger.info("\n" + "="*60)
    logger.info("📋 DNS服务器IPv6 AAAA记录支持能力综合报告")
    logger.info("="*60)
    
    best_server = None
    best_score = -1
    
    for dns_server, result in results.items():
        success_rate = (result["successful_queries"] / result["total_queries"] * 100) if result["total_queries"] > 0 else 0
        avg_response_time = sum(result["response_times"]) / len(result["response_times"]) if result["response_times"] else 999
        ipv6_per_query = result["total_ipv6_addresses"] / result["successful_queries"] if result["successful_queries"] > 0 else 0
        
        # 综合评分：成功率权重60%，响应时间权重25%，IPv6地址丰富度权重15%
        score = (success_rate * 0.6) + (max(0, 1 - avg_response_time/2) * 25) + (min(ipv6_per_query/3, 1) * 15)
        
        logger.info(f"\n🌐 {dns_server}:")
        logger.info(f"   综合评分: {score:.1f}")
        logger.info(f"   成功率: {success_rate:.1f}%")
        logger.info(f"   平均响应时间: {avg_response_time:.3f}s")
        logger.info(f"   平均IPv6地址数: {ipv6_per_query:.1f}/查询")
        
        if score > best_score:
            best_score = score
            best_server = dns_server
    
    logger.info(f"\n🏆 推荐DNS服务器: {best_server} (评分: {best_score:.1f})")
    
    return results


class SSHManager:
    """SSH连接管理器"""
    
    def __init__(self, hostname, port, username, password=None, key_filename=None):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.key_filename = key_filename
        self.ssh = None
        self.connected = False
    
    def connect(self):
        """建立SSH连接"""
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            connect_kwargs = {
                'hostname': self.hostname,
                'port': self.port,
                'username': self.username,
            }
            
            if self.key_filename:
                connect_kwargs['key_filename'] = self.key_filename
            elif self.password:
                connect_kwargs['password'] = self.password
            
            self.ssh.connect(**connect_kwargs)
            self.connected = True
            logger.info(f"✅ SSH连接成功: {self.username}@{self.hostname}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"❌ SSH连接失败: {e}")
            return False
    
    def execute_command(self, command, timeout=30):
        """执行远程命令"""
        if not self.connected:
            logger.error("SSH未连接")
            return None, None, 1
        
        try:
            stdin, stdout, stderr = self.ssh.exec_command(command, timeout=timeout)
            exit_code = stdout.channel.recv_exit_status()
            
            stdout_data = stdout.read().decode('utf-8', errors='ignore')
            stderr_data = stderr.read().decode('utf-8', errors='ignore')
            
            return stdout_data, stderr_data, exit_code
            
        except Exception as e:
            logger.error(f"命令执行失败: {e}")
            return None, str(e), 1
    
    def setup_virtual_environment(self):
        """设置虚拟环境"""
        commands = [
            f"python3 -m venv {VENV_DIR}",
            f"{VENV_PYTHON_PATH} -m pip install --upgrade pip",
            f"{VENV_PYTHON_PATH} -m pip install dnspython requests paramiko"
        ]
        
        for cmd in commands:
            stdout, stderr, exit_code = self.execute_command(cmd)
            if exit_code != 0:
                logger.error(f"虚拟环境设置失败: {stderr}")
                return False
        
        logger.info("✅ 虚拟环境设置完成")
        return True
    
    def upload_file(self, local_path, remote_path):
        """上传文件"""
        try:
            sftp = self.ssh.open_sftp()
            sftp.put(local_path, remote_path)
            sftp.close()
            logger.info(f"✅ 文件上传成功: {local_path} -> {remote_path}")
            return True
        except Exception as e:
            logger.error(f"❌ 文件上传失败: {e}")
            return False
    
    def download_file(self, remote_path, local_path):
        """下载文件"""
        try:
            sftp = self.ssh.open_sftp()
            sftp.get(remote_path, local_path)
            sftp.close()
            logger.info(f"✅ 文件下载成功: {remote_path} -> {local_path}")
            return True
        except Exception as e:
            logger.error(f"❌ 文件下载失败: {e}")
            return False
    
    def close(self):
        """关闭SSH连接"""
        if self.ssh:
            self.ssh.close()
            self.connected = False
            logger.info("🔌 SSH连接已关闭")


def get_ips_from_dns_servers(domain, ipv6_enable=False):
    """从多个DNS服务器获取IP地址"""
    ipv4_addresses = set()
    ipv6_addresses = set()
    successful_queries = 0
    total_queries = 0
    
    # 测试的DNS服务器列表
    dns_servers = ['8.8.8.8', '1.1.1.1', '9.9.9.9', '208.67.222.222']
    
    for dns_server in dns_servers:
        total_queries += 1
        resolver = dns.resolver.Resolver()
        resolver.nameservers = [dns_server]
        resolver.timeout = DNS_TIMEOUT_SEC
        resolver.lifetime = DNS_LIFETIME_SEC
        
        try:
            # 查询A记录 (IPv4)
            answers = resolver.resolve(domain, 'A')
            for rdata in answers:
                ipv4_addresses.add(str(rdata))
            successful_queries += 1
            
            # 如果启用IPv6，查询AAAA记录
            if ipv6_enable:
                try:
                    answers = resolver.resolve(domain, 'AAAA')
                    ipv6_found = [rdata.address for rdata in answers]
                    for ipv6_addr in ipv6_found:
                        ipv6_addresses.add(ipv6_addr)
                    
                    # 记录AAAA统计信息
                    if AAAA_RECORD_ENABLE and ipv6_found:
                        log_aaaa_record_statistics(ipv6_found, domain, dns_server, 0.1)
                        
                except Exception as e:
                    logger.debug(f"AAAA记录查询失败 {domain} @ {dns_server}: {e}")
            
        except Exception as e:
            logger.debug(f"DNS查询失败 {domain} @ {dns_server}: {e}")
    
    # 如果启用IPv6且AAAA记录查询启用，验证DNS服务器IPv6能力
    if ipv6_enable and AAAA_RECORD_ENABLE:
        validate_dns_servers_ipv6_capability()
    
    logger.info(f"DNS解析完成: {domain} -> IPv4: {len(ipv4_addresses)}, IPv6: {len(ipv6_addresses)}, 成功率: {successful_queries}/{total_queries}")
    
    return list(ipv4_addresses), list(ipv6_addresses), successful_queries, total_queries


def setup_virtual_environment_and_execute_script(ssh_manager, ipv6_param=""):
    """设置虚拟环境并执行脚本"""
    # 设置虚拟环境
    if not ssh_manager.setup_virtual_environment():
        return False
    
    # 上传当前脚本到远程服务器
    local_script_path = os.path.abspath(__file__)
    remote_script_path = f"resolve_ip_remote.py"
    
    if not ssh_manager.upload_file(local_script_path, remote_script_path):
        return False
    
    # 执行远程解析
    cmd = f"{VENV_PYTHON_PATH} {remote_script_path} {ipv6_param}"
    stdout, stderr, exit_code = ssh_manager.execute_command(cmd, timeout=300)
    
    if exit_code != 0:
        logger.error(f"远程脚本执行失败: {stderr}")
        return False
    
    logger.info("✅ 远程脚本执行完成")
    return True


def main():
    """主函数"""
    global logger, IPv6_ENABLE, AAAA_RECORD_ENABLE
    
    # 设置日志
    logger = setup_logging()
    
    logger.info("🚀 AUTOVPN远程域名解析脚本启动")
    
    # 检查命令行参数
    ipv6_param = ""
    if len(sys.argv) > 1:
        if "--ipv6" in sys.argv:
            IPv6_ENABLE = True
            ipv6_param = "--ipv6"
            logger.info("✅ IPv6支持已启用")
    
    # 如果启用了IPv6，进行DNS服务器验证
    if IPv6_ENABLE:
        logger.info("🔍 检测到IPv6支持，开始验证DNS服务器AAAA记录能力...")
        validate_dns_servers_ipv6_capability()
    
    # 读取域名列表
    domain_list_file = os.path.join(os.path.dirname(__file__), "..", "routes", "需要获取IP的域名列表.txt")
    if not os.path.exists(domain_list_file):
        logger.error(f"域名列表文件不存在: {domain_list_file}")
        return 1
    
    with open(domain_list_file, 'r', encoding='utf-8') as f:
        domains = [line.strip() for line in f.readlines() if line.strip() and not line.startswith('#')]
    
    if not domains:
        logger.error("域名列表为空")
        return 1
    
    logger.info(f"📋 待解析域名数量: {len(domains)}")
    
    # 解析每个域名
    all_ipv4_addresses = []
    all_ipv6_addresses = []
    
    for domain in domains:
        logger.info(f"\n🔍 开始解析域名: {domain}")
        
        # 本地DNS解析
        ipv4_list, ipv6_list, successful, total = get_ips_from_dns_servers(domain, IPv6_ENABLE)
        
        all_ipv4_addresses.extend(ipv4_list)
        all_ipv6_addresses.extend(ipv6_list)
        
        # 如果启用了IPv6，验证IPv6地址的连接性
        if IPv6_ENABLE and ipv6_list:
            logger.info(f"🔍 开始验证IPv6地址连接性: {domain}")
            connectable, success_rate, results = validate_ipv6_connectivity(ipv6_list, domain)
            logger.info(f"📊 IPv6连接性测试结果: {'可连接' if connectable else '不可连接'} (成功率: {success_rate:.1%})")
    
    # 去重并排序
    unique_ipv4 = sorted(list(set(all_ipv4_addresses)))
    unique_ipv6 = sorted(list(set(all_ipv6_addresses)))
    
    logger.info(f"\n📊 解析结果统计:")
    logger.info(f"   总IPv4地址数: {len(unique_ipv4)}")
    logger.info(f"   总IPv6地址数: {len(unique_ipv6)}")
    
    # 写入结果文件
    output_file = os.path.join(os.path.dirname(__file__), "..", "routes", "常用境外IP.txt")
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            # 写入IPv4地址
            for ip in unique_ipv4:
                f.write(f"{ip}\t# IPv4地址\n")
            
            # 写入IPv6地址（如果启用了IPv6）
            if IPv6_ENABLE and unique_ipv6:
                f.write("\n# IPv6地址\n")
                for ip in unique_ipv6:
                    f.write(f"{ip}\t# IPv6地址\n")
        
        logger.info(f"✅ 解析结果已写入: {output_file}")
        
    except Exception as e:
        logger.error(f"❌ 写入结果文件失败: {e}")
        return 1
    
    logger.info("🎉 域名解析完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())