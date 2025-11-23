#!/usr/bin/python3
import socket
import time
import random
import argparse
import json
import sys  # For stderr

# Attempt to import required libraries
try:
    import dns.resolver
    import requests
except ImportError as e:
    print(
        f"Error: Missing required Python libraries. Please install dnspython and requests using pip3. Details: {e}",
        file=sys.stderr)
    sys.exit(1)

# Configuration
DNS_SERVERS_TO_USE = [
    '8.8.8.8',
    '1.1.1.1',
    '9.9.9.9',
    '208.67.222.222',
    '208.67.220.220']  # Google, Cloudflare, Quad9, OpenDNS1, OpenDNS2
PREFERRED_COUNTRIES = [
    "US",
    "CA",
    "GB",
    "AU",
    "NZ",
    "SG",
    "JP",
    "KR",
    "DE",
    "FR",
    "NL"]  # Prioritize IPs from these countries

IP_API_URL_TEMPLATE = "http://ip-api.com/json/{ip}?fields=status,message,countryCode,isp,org,query"
IP_API_TIMEOUT_SEC = 10  # Increased timeout for ip-api.com
# Ensures max 24 calls per minute, per user request for safety.
IP_API_SLEEP_SEC = 2.5

DNS_TIMEOUT_SEC = 5  # Timeout for each DNS query
DNS_LIFETIME_SEC = 12  # Total lifetime for a resolve operation across retries
# dnspython's resolve() method handles retries internally based on
# lifetime vs timeout.

# 新增：TCP连接测试相关配置
CONNECTIVITY_PORTS_TO_CHECK = [80, 443]
CONNECTIVITY_TIMEOUT_SEC = 2  # Short timeout for TCP connect

# 修改日志路径为远程服务器上的路径
LOG_FILE_PATH = "./get_clean_ips_v2.log"


def log_message(message, print_to_stdout=True):
    """Logs a message to stdout and to the log file."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} - {message}"
    if print_to_stdout:
        print(log_entry)
    try:
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f_log:
            f_log.write(log_entry + "\n")
    except Exception as e:
        # If logging to file fails, print to stderr to ensure the error is
        # visible, especially if stdout was suppressed
        print(
            f"{timestamp} - CRITICAL: Failed to write to log file {LOG_FILE_PATH}: {e}. Message: {message}",
            file=sys.stderr)


def get_ips_from_dns_servers(domain, ipv6_enable=False):
    """Queries multiple DNS servers for a domain and returns a list of unique IPs found by any server."""
    unique_ips_found = set()
    unique_ipv6_ips_found = set()
    
    try:
        # 尝试显式获取 Resolver 类
        SpecificResolver = dns.resolver.Resolver
    except AttributeError:
        log_message(
            "CRITICAL: dns.resolver.Resolver class not found even after import. Dnspython might be corrupted.")
        return [], False, [], False  # 返回空列表和失败标志

    resolver = SpecificResolver()
    resolver.timeout = DNS_TIMEOUT_SEC
    resolver.lifetime = DNS_LIFETIME_SEC

    for server_ip in DNS_SERVERS_TO_USE:
        resolver.nameservers = [server_ip]
        try:
            log_message(
                f"  Querying {domain} via DNS {server_ip}...",
                print_to_stdout=False)
            
            # For A records (IPv4)
            try:
                # 尝试使用新版本的resolve方法
                answers = resolver.resolve(domain, 'A')
            except AttributeError:
                # 如果resolve方法不存在，尝试使用旧版本的query方法
                log_message(
                    f"  Using legacy 'query' method instead of 'resolve' for {domain}")
                answers = resolver.query(domain, 'A')

            for rdata in answers:
                ip = rdata.address
                if ip:
                    log_message(
                        f"    Found IPv4: {ip} for {domain} via {server_ip}",
                        print_to_stdout=False)
                    unique_ips_found.add(ip)
            
            # For AAAA records (IPv6) - 如果IPv6启用
            if ipv6_enable:
                try:
                    # 尝试使用新版本的resolve方法
                    answers_v6 = resolver.resolve(domain, 'AAAA')
                except AttributeError:
                    # 如果resolve方法不存在，尝试使用旧版本的query方法
                    answers_v6 = resolver.query(domain, 'AAAA')

                for rdata in answers_v6:
                    ipv6 = rdata.address
                    if ipv6:
                        log_message(
                            f"    Found IPv6: {ipv6} for {domain} via {server_ip}",
                            print_to_stdout=False)
                        unique_ipv6_ips_found.add(ipv6)
                        
        except dns.resolver.NXDOMAIN:
            log_message(
                f"  Domain {domain} not found (NXDOMAIN) via {server_ip}.",
                print_to_stdout=False)
        except dns.exception.Timeout:
            log_message(
                f"  Timeout querying {domain} via {server_ip}.",
                print_to_stdout=False)
        except dns.resolver.NoAnswer:
            log_message(
                f"  No A/AAAA records for {domain} via {server_ip} (NoAnswer).",
                print_to_stdout=False)
        except dns.resolver.NoNameservers:
            log_message(
                f"  No nameservers available for query via {server_ip} (NoNameservers).",
                print_to_stdout=False)
        except Exception as e:
            log_message(
                f"  Error querying {domain} via {server_ip}: {type(e).__name__} {e}",
                print_to_stdout=False)
        # Small polite delay between querying different DNS servers for the
        # same domain
        time.sleep(0.1)
    
    # 返回IPv4和IPv6结果
    ipv4_success = len(unique_ips_found) > 0
    ipv6_success = len(unique_ipv6_ips_found) > 0
    
    if ipv6_enable:
        return list(unique_ips_found), ipv4_success, list(unique_ipv6_ips_found), ipv6_success
    else:
        return list(unique_ips_found), ipv4_success, [], False


def get_ip_geo_info(ip_address):
    """Gets geolocation info for an IP using ip-api.com."""
    url = IP_API_URL_TEMPLATE.format(ip=ip_address)
    geo_info = {
        "ip": ip_address,
        "countryCode": "N/A",
        "isp": "N/A",
        "org": "N/A",
        "error": None}
    try:
        log_message(
            f"    Querying ip-api.com for {ip_address}...",
            print_to_stdout=False)
        response = requests.get(url, timeout=IP_API_TIMEOUT_SEC)
        response.raise_for_status()
        data = response.json()
        if data.get("status") == "success":
            geo_info["countryCode"] = data.get("countryCode", "N/A")
            geo_info["isp"] = data.get("isp", "N/A")
            geo_info["org"] = data.get("org", "N/A")
        else:
            geo_info["error"] = data.get(
                "message", "ip-api.com returned non-success status")
            log_message(
                f"    ip-api.com query for {ip_address} non-success: {geo_info['error']}",
                print_to_stdout=False)
    except requests.exceptions.Timeout:
        geo_info["error"] = "Request timed out"
        log_message(
            f"    Timeout fetching geo info for {ip_address} from ip-api.com.",
            print_to_stdout=False)
    except requests.exceptions.RequestException as e:
        geo_info["error"] = str(e)
        log_message(
            f"    Error fetching geo info for {ip_address} from ip-api.com: {e}",
            print_to_stdout=False)
    except json.JSONDecodeError as e:
        geo_info["error"] = f"JSON decode error: {e}"
        log_message(
            f"    Error decoding JSON from ip-api.com for {ip_address}: {e}",
            print_to_stdout=False)

    log_message(
        f"    Sleeping for {IP_API_SLEEP_SEC}s after ip-api.com call for {ip_address}...",
        print_to_stdout=False)
    time.sleep(IP_API_SLEEP_SEC)  # Strict rate limiting
    return geo_info


def select_best_ip(domain, ip_geo_list_with_dns_hits):
    if not ip_geo_list_with_dns_hits:
        return None

    candidates = []
    for item in ip_geo_list_with_dns_hits:
        ip = item["ip"]
        geo_info = item["geo_info"]
        dns_hit_count = item["dns_hits"]
        score = 0

        # 步骤1: TCP 连接性测试 (新)
        is_connectable = check_ip_connectivity(
            ip, CONNECTIVITY_PORTS_TO_CHECK, CONNECTIVITY_TIMEOUT_SEC)
        connectivity_score_adjustment = 0
        if is_connectable:
            connectivity_score_adjustment = 60  # 主要的积极信号
            log_message(
                f"    IP_SELECT: IP {ip} passed connectivity test. Score bonus: +{connectivity_score_adjustment}",
                print_to_stdout=False)
        else:
            connectivity_score_adjustment = -200  # 非常大的负面信号，基本排除此IP
            log_message(
                f"    IP_SELECT: IP {ip} FAILED connectivity test. Score penalty: {connectivity_score_adjustment}",
                print_to_stdout=False)
        score += connectivity_score_adjustment

        # 步骤2: DNS命中次数评分
        # Each DNS server confirming an IP is a strong signal
        dns_score = dns_hit_count * 20
        score += dns_score
        log_message(
            f"    IP_SELECT: IP {ip}, DNS hits {dns_hit_count}. Score bonus: +{dns_score}",
            print_to_stdout=False)

        # 步骤3: 地理位置评分
        geo_score_adjustment = 0
        if geo_info and not geo_info["error"]:
            if geo_info["countryCode"] in PREFERRED_COUNTRIES:
                geo_score_adjustment += 50
                if geo_info["countryCode"] == "US":
                    geo_score_adjustment += 10  # Extra for US
                log_message(
                    f"    IP_SELECT: IP {ip} from preferred country {geo_info['countryCode']}. Score bonus: +{geo_score_adjustment - (geo_score_adjustment - (50 + (10 if geo_info['countryCode'] == 'US' else 0)))}",
                    print_to_stdout=False)  # Log only this step's bonus
            elif geo_info["countryCode"] == "N/A":  # Unknown country might be okay
                log_message(
                    f"    IP_SELECT: IP {ip} country N/A. No geo score change.",
                    print_to_stdout=False)
                pass
            else:  # Known, but not preferred country
                geo_score_adjustment -= 10
                log_message(
                    f"    IP_SELECT: IP {ip} from non-preferred country {geo_info['countryCode']}. Score penalty: -10",
                    print_to_stdout=False)
        else:  # Geo lookup failed or had an error
            geo_score_adjustment -= 30
            log_message(
                f"    IP_SELECT: IP {ip} geo lookup failed/error. Score penalty: -30",
                print_to_stdout=False)
        score += geo_score_adjustment

        candidates.append({"ip": ip,
                           "score": score,
                           "geo": geo_info,
                           "dns_hits": dns_hit_count,
                           "connectable": is_connectable})

    if not candidates:
        return None

    # 按最终得分排序
    candidates.sort(key=lambda x: x["score"], reverse=True)

    best_candidate = candidates[0]
    log_message(f"  IP Selection for {domain}:")  # This summary line to stdout
    for c in candidates:
        log_message(
            f"    - IP: {c['ip']}, Score: {c['score']}, DNS Hits: {c['dns_hits']}, Connectable: {c['connectable']}, Country: {c['geo'].get('countryCode', 'N/A') if c['geo'] else 'N/A'}, ISP: {c['geo'].get('isp', 'N/A') if c['geo'] else 'N/A'}",
            print_to_stdout=False)  # Detailed candidate list to log file only

    # 调整阈值，因为连接性测试现在是主要因素
    # 如果最佳候选者连接性测试失败，则不选择 (除非没有其他选择且分数不是太差)
    # 示例：如果连接不上且总分是负的，就放弃
    if not best_candidate["connectable"] and best_candidate["score"] < 0:
        log_message(
            f"  WARNING: Best IP {best_candidate['ip']} for {domain} (Score: {best_candidate['score']}) FAILED connectivity test and has low score. Not selecting.")
        return None
    elif best_candidate["score"] < -50:  # 即使能连上，但如果其他因素导致分数极低
        log_message(
            f"  WARNING: Best IP {best_candidate['ip']} for {domain} has very low score ({best_candidate['score']}) despite connectivity. Not selecting.")
        return None

    log_message(
        f"  ==> Selected for {domain} (after connectivity check): {best_candidate['ip']}")
    return best_candidate["ip"]


def get_dns_hit_counts(domain_ips_map_from_all_dns):
    """ Takes a list of (dns_server, ip_list) tuples and returns a dict of {ip: count} """
    ip_counts = {}
    # This function is not directly used in current flow, replaced by direct counting in process_domains
    # Retained for potential future use if data structure changes
    return ip_counts


def process_domains_new(input_file_path, output_file_path, ipv6_enable=False):
    log_message(
        f"Processing domain list: {input_file_path}",
        print_to_stdout=True)
    try:
        with open(input_file_path, 'r', encoding='utf-8-sig') as f_in:
            domains = [line.strip() for line in f_in if line.strip()
                       and not line.startswith('#')]
    except FileNotFoundError:
        log_message(
            f"CRITICAL Error: Input domain list file not found at {input_file_path}. Script will exit.")
        return
    except Exception as e:
        log_message(
            f"CRITICAL Error reading domain list file {input_file_path}: {e}. Script will exit.")
        return

    if not domains:
        log_message("No domains found in the input file. Exiting.")
        return

    log_message(f"Found {len(domains)} domains to process.")
    final_domain_ip_map = {}

    for i, domain in enumerate(domains):
        progress = (i + 1) / len(domains) * 100
        log_message(f"Processing domain {i + 1}/{len(domains)} ({progress:.1f}%): {domain}")

        # Step 1: Get all IPs from all configured DNS servers
        all_ips_from_dns_query, dns_success, ipv6_ips, ipv6_success = get_ips_from_dns_servers(domain, ipv6_enable)
        if not dns_success and not (ipv6_enable and ipv6_success):
            log_message(
                f"  No IPs found for {domain} from any specified DNS server after retries.")
            continue  # Move to next domain

        # Count hits for each IP across all DNS servers
        ip_hit_counts = {}
        for ip_addr in all_ips_from_dns_query:
            ip_hit_counts[ip_addr] = ip_hit_counts.get(ip_addr, 0) + 1
            
        # 统计IPv6地址命中次数
        ipv6_hit_counts = {}
        if ipv6_enable and ipv6_success:
            for ipv6_addr in ipv6_ips:
                ipv6_hit_counts[ipv6_addr] = ipv6_hit_counts.get(ipv6_addr, 0) + 1

        unique_ips_to_geolocate = sorted(list(ip_hit_counts.keys()))
        unique_ipv6_to_geolocate = sorted(list(ipv6_hit_counts.keys())) if ipv6_enable else []
        
        # 增强IPv6日志记录
        if ipv6_enable:
            log_message(f"  IPv4解析结果: {len(unique_ips_to_geolocate)}个地址")
            if ipv6_success and unique_ipv6_to_geolocate:
                log_message(f"  🎉 IPv6解析成功: {len(unique_ipv6_to_geolocate)}个地址 - {unique_ipv6_to_geolocate}")
            else:
                log_message(f"  🔍 IPv6解析: 未发现AAAA记录")
        
        log_message(
            f"  Unique IPs from DNS for {domain}: {unique_ips_to_geolocate}. Hit counts: {ip_hit_counts}")

        # Step 2: Get Geo Info for unique IPs
        ip_geo_data_with_hits = []
        if unique_ips_to_geolocate:
            for ip_addr in unique_ips_to_geolocate:
                geo_info = get_ip_geo_info(ip_addr)
                ip_geo_data_with_hits.append(
                    {"ip": ip_addr, "geo_info": geo_info, "dns_hits": ip_hit_counts.get(ip_addr, 0)})

        # Step 3: Select the best IP
        best_ip = select_best_ip(domain, ip_geo_data_with_hits)

        if best_ip:
            final_domain_ip_map[domain] = best_ip
            # 这条日志现在由 select_best_ip 内部打印，包含连接性信息
            # log_message(f"  ==> Selected for {domain}: {best_ip}")
        else:
            log_message(
                f"  ==> FAILED to select a reliable IP for {domain} after all checks (incl. connectivity).")
            # final_domain_ip_map[domain] = "RESOLUTION_FAILED" # Or skip

    # Step 4: Write results to output file
    try:
        # Ensure unique entries by domain (last one wins if somehow duplicated before this stage)
        # final_domain_ip_map is already a dict, so domains are unique.
        with open(output_file_path, 'w', encoding='utf-8') as f_out:
            for domain, ip in final_domain_ip_map.items():
                f_out.write(f"{ip}\t{domain}\n")
        log_message(
            f"\nSuccessfully wrote {len(final_domain_ip_map)} resolved domain-IP pairs to {output_file_path}")
    except Exception as e:
        log_message(f"Error writing to output file {output_file_path}: {e}")

    log_message("Domain processing finished.")

# 新增：网络环境IPv6支持检测函数


def check_network_ipv6_support():
    """检测当前网络环境是否支持IPv6连接"""
    log_message("正在检测网络环境IPv6支持情况...", print_to_stdout=True)
    
    ipv6_support_status = {
        "has_ipv6_address": False,
        "can_connect_ipv6_google": False,
        "can_resolve_ipv6_dns": False,
        "ipv6_test_addresses": [],
        "error_messages": []
    }
    
    try:
        # 1. 检查本机是否有IPv6地址
        try:
            # 尝试获取本机IPv6地址
            sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
            sock.connect(("2001:4860:4860::8888", 80))  # Google IPv6 DNS
            local_ipv6 = sock.getsockname()[0]
            sock.close()
            ipv6_support_status["has_ipv6_address"] = True
            ipv6_support_status["ipv6_test_addresses"].append(local_ipv6)
            log_message(f"✅ 检测到本机IPv6地址: {local_ipv6}", print_to_stdout=True)
        except Exception as e:
            ipv6_support_status["error_messages"].append(f"无法获取本机IPv6地址: {str(e)}")
            log_message(f"❌ 未检测到本机IPv6地址: {str(e)}", print_to_stdout=True)
        
        # 2. 测试IPv6连接性 - 尝试连接Google IPv6地址
        try:
            test_sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            test_sock.settimeout(3)
            result = test_sock.connect_ex(("2001:4860:4860::8888", 80))  # Google IPv6
            test_sock.close()
            
            if result == 0:
                ipv6_support_status["can_connect_ipv6_google"] = True
                log_message("✅ IPv6连接测试成功 - 可以连接到Google IPv6地址", print_to_stdout=True)
            else:
                ipv6_support_status["error_messages"].append(f"IPv6连接测试失败，错误码: {result}")
                log_message(f"❌ IPv6连接测试失败，错误码: {result}", print_to_stdout=True)
        except Exception as e:
            ipv6_support_status["error_messages"].append(f"IPv6连接测试异常: {str(e)}")
            log_message(f"❌ IPv6连接测试异常: {str(e)}", print_to_stdout=True)
        
        # 3. 测试IPv6 DNS解析能力
        try:
            resolver = dns.resolver.Resolver()
            resolver.nameservers = ["2001:4860:4860::8888"]  # Google IPv6 DNS
            answers = resolver.resolve("ipv6.google.com", "AAAA")
            
            if answers:
                ipv6_support_status["can_resolve_ipv6_dns"] = True
                resolved_ips = [rdata.address for rdata in answers]
                log_message(f"✅ IPv6 DNS解析测试成功 - ipv6.google.com解析到: {resolved_ips}", print_to_stdout=True)
            else:
                ipv6_support_status["error_messages"].append("IPv6 DNS解析返回空结果")
                log_message("❌ IPv6 DNS解析返回空结果", print_to_stdout=True)
        except Exception as e:
            ipv6_support_status["error_messages"].append(f"IPv6 DNS解析测试失败: {str(e)}")
            log_message(f"❌ IPv6 DNS解析测试失败: {str(e)}", print_to_stdout=True)
        
        # 总结网络环境IPv6支持情况
        support_score = sum([
            ipv6_support_status["has_ipv6_address"],
            ipv6_support_status["can_connect_ipv6_google"], 
            ipv6_support_status["can_resolve_ipv6_dns"]
        ])
        
        if support_score == 3:
            log_message("🎉 网络环境IPv6支持良好 - 所有测试均通过", print_to_stdout=True)
        elif support_score >= 2:
            log_message("⚠️ 网络环境IPv6支持部分可用 - 部分测试通过", print_to_stdout=True)
        else:
            log_message("❌ 网络环境IPv6支持有限 - 多数测试失败", print_to_stdout=True)
            
        log_message(f"IPv6支持评分: {support_score}/3", print_to_stdout=True)
        
    except Exception as e:
        ipv6_support_status["error_messages"].append(f"IPv6支持检测总体异常: {str(e)}")
        log_message(f"❌ IPv6支持检测总体异常: {str(e)}", print_to_stdout=True)
    
    return ipv6_support_status


# 新增：TCP 连接测试函数


def check_ip_connectivity(ip_address, ports_to_check, timeout_sec):
    """Checks TCP connectivity to an IP on specified ports."""
    for port in ports_to_check:
        log_message(
            f"    CONN_TEST: Attempting TCP connect to {ip_address} on port {port} (timeout: {timeout_sec}s)...",
            print_to_stdout=False)
        try:
            sock = socket.create_connection(
                (ip_address, port), timeout=timeout_sec)
            sock.close()
            log_message(
                f"    CONN_TEST: Success connecting to {ip_address} on port {port}.",
                print_to_stdout=False)
            return True  # At least one port connected successfully
        except socket.timeout:
            log_message(
                f"    CONN_TEST: Timeout connecting to {ip_address} on port {port}.",
                print_to_stdout=False)
        except socket.error as e:
            log_message(
                f"    CONN_TEST: Error connecting to {ip_address} on port {port}: {e}",
                print_to_stdout=False)
        time.sleep(0.1)  # Small delay between port checks on the same IP
    log_message(
        f"    CONN_TEST: Failed to connect to {ip_address} on any of the specified ports {ports_to_check}.",
        print_to_stdout=True)  # Summary of connectivity test to stdout
    return False


if __name__ == "__main__":
    # Initialize log file (overwrite existing) and log script start parameters.
    # This must be the first logging action.
    try:
        with open(LOG_FILE_PATH, "w", encoding="utf-8") as f_log:
            f_log.write(
                f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Log initialized for get_clean_ips_v2.py run.\n")
    except Exception as e:
        # If log file cannot be opened/written, critical messages will go to
        # stderr.
        print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - CRITICAL: Failed to initialize log file {LOG_FILE_PATH}: {e}. Subsequent file logging will fail.", file=sys.stderr)

    parser = argparse.ArgumentParser(
        description="Resolve domain names to IP addresses using multiple DNS servers and geo-verification.")
    parser.add_argument(
        "input_file",
        default="/root/常用境外域名.txt",
        nargs='?',
        help="Path to the input file. Defaults to /root/常用境外域名.txt")
    parser.add_argument(
        "output_file",
        default="/root/常用境外IP.txt",
        nargs='?',
        help="Path to the output file. Defaults to /root/常用境外IP.txt")
    parser.add_argument(
        "--ipv6",
        action="store_true",
        help="Enable IPv6 support for domain resolution")
    args = parser.parse_args()

    log_message(
        f"===== Script get_clean_ips_v2.py (enhanced logging) started =====",
        print_to_stdout=True)
    log_message(f"Input domain list: {args.input_file}", print_to_stdout=True)
    log_message(f"Output IP list: {args.output_file}", print_to_stdout=True)
    log_message(f"Log file: {LOG_FILE_PATH}", print_to_stdout=True)
    log_message(
        f"DNS Servers: {DNS_SERVERS_TO_USE}",
        print_to_stdout=False)  # Log to file only
    log_message(
        f"Preferred Countries: {PREFERRED_COUNTRIES}",
        print_to_stdout=False)  # Log to file only
    log_message(
        f"IP-API Timeout: {IP_API_TIMEOUT_SEC}s, Sleep: {IP_API_SLEEP_SEC}s",
        print_to_stdout=False)  # Log to file only
    log_message(
        f"DNS Timeout: {DNS_TIMEOUT_SEC}s, Lifetime: {DNS_LIFETIME_SEC}s",
        print_to_stdout=False)  # Log to file only
    log_message(
        f"Connectivity Ports: {CONNECTIVITY_PORTS_TO_CHECK}, Timeout: {CONNECTIVITY_TIMEOUT_SEC}s",
        print_to_stdout=True)
    
    # Log IPv6 status
    if args.ipv6:
        log_message("IPv6 support is ENABLED for domain resolution", print_to_stdout=True)
        # 当启用IPv6时，先检测网络环境支持情况
        log_message("开始检测网络环境IPv6支持情况...", print_to_stdout=True)
        ipv6_network_status = check_network_ipv6_support()
        
        # 根据网络环境检测结果给出建议
        if not ipv6_network_status["has_ipv6_address"]:
            log_message("⚠️ 警告: 未检测到本机IPv6地址，建议检查网络配置", print_to_stdout=True)
        if not ipv6_network_status["can_connect_ipv6_google"]:
            log_message("⚠️ 警告: 无法连接IPv6地址，可能存在网络连通性问题", print_to_stdout=True)
        if not ipv6_network_status["can_resolve_ipv6_dns"]:
            log_message("⚠️ 警告: IPv6 DNS解析失败，可能影响IPv6域名解析", print_to_stdout=True)
            
        # 如果网络环境不支持IPv6，给出明确提示
        support_score = sum([
            ipv6_network_status["has_ipv6_address"],
            ipv6_network_status["can_connect_ipv6_google"], 
            ipv6_network_status["can_resolve_ipv6_dns"]
        ])
        
        if support_score < 2:
            log_message("❌ 当前网络环境IPv6支持较差，建议检查网络配置或联系网络管理员", print_to_stdout=True)
            log_message("💡 建议: 可以尝试禁用IPv6功能(--no-ipv6)或检查系统IPv6配置", print_to_stdout=True)
    else:
        log_message("IPv6 support is DISABLED for domain resolution", print_to_stdout=True)

    try:
        process_domains_new(args.input_file, args.output_file, ipv6_enable=args.ipv6)
        log_message(
            "===== Script get_clean_ips_v2.py (enhanced logging) finished successfully =====",
            print_to_stdout=True)
    except Exception as e:
        log_message(
            f"CRITICAL ERROR in main processing: {type(e).__name__} - {e}. Check logs for details.",
            print_to_stdout=True)
        # Also print to stderr for high visibility of critical failure
        print(
            f"{time.strftime('%Y-%m-%d %H:%M:%S')} - CRITICAL ERROR in main processing: {type(e).__name__} - {e}. Check log file {LOG_FILE_PATH} for details.",
            file=sys.stderr)
        sys.exit(1)  # Indicate failure

# 示例用法 (在服务器上执行):
# python3 get_clean_ips.py /path/to/常用境外域名.txt /path/to/常用境外IP.txt
#
# 注意：此脚本使用socket.getaddrinfo，它依赖服务器的系统级DNS配置。
# 为确保获取的是"干净"IP，请保证服务器的 /etc/resolv.conf (Linux) 指向可信的、无污染的DNS服务器，
# 例如 Google Public DNS (8.8.8.8, 8.8.4.4) 或 Cloudflare DNS (1.1.1.1, 1.0.0.1)。
# 如果需要更严格地通过脚本指定DNS服务器，建议使用 `dnspython` 库，
# 或者通过 subprocess 调用 `dig @<dns_server_ip> <domain_name> A +short` (针对IPv4 A记录)。
# 例如，使用 dnspython:
# import dns.resolver
# my_resolver = dns.resolver.Resolver()
# my_resolver.nameservers = ['8.8.8.8']
# answer = my_resolver.resolve(domain, 'A')
# ips = [rdata.address for rdata in answer]
