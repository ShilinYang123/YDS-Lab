#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import os
import sys
import time
import random
import argparse
import json

# Attempt to import required libraries
try:
    import dns.resolver
except ImportError as e:
    print(f"Error: Missing required Python libraries. Please install dnspython using pip3. Details: {e}")
    sys.exit(1)

# Configuration
DNS_SERVERS_TO_USE = [
    '8.8.8.8',
    '1.1.1.1',
    '9.9.9.9',
    '208.67.222.222',
    '208.67.220.220']  # Google, Cloudflare, Quad9, OpenDNS1, OpenDNS2

def get_ips_from_dns_servers(domain):
    """Queries multiple DNS servers for a domain and returns a list of unique IPs found by any server."""
    unique_ips_found = set()
    resolver = dns.resolver.Resolver()
    resolver.timeout = 5
    resolver.lifetime = 12

    for server_ip in DNS_SERVERS_TO_USE:
        resolver.nameservers = [server_ip]
        try:
            print(f"  Querying {domain} via DNS {server_ip}...")
            answers = resolver.resolve(domain, 'A', tcp=True)
            for rdata in answers:
                ip = rdata.address
                if ip:
                    print(f"    Found IP: {ip} for {domain} via {server_ip}")
                    unique_ips_found.add(ip)
        except dns.resolver.NXDOMAIN:
            print(f"  Domain {domain} not found (NXDOMAIN) via {server_ip}.")
        except dns.exception.Timeout:
            print(f"  Timeout querying {domain} via {server_ip}.")
        except dns.resolver.NoAnswer:
            print(f"  No A records for {domain} via {server_ip} (NoAnswer).")
        except dns.resolver.NoNameservers:
            print(f"  No nameservers available for query via {server_ip} (NoNameservers).")
        except Exception as e:
            print(f"  Error querying {domain} via {server_ip}: {type(e).__name__} {e}")
        time.sleep(0.1)
    return list(unique_ips_found), len(unique_ips_found) > 0

def process_domains(input_file_path, output_file_path):
    print(f"Processing domain list: {input_file_path}")
    try:
        with open(input_file_path, 'r', encoding='utf-8-sig') as f_in:
            domains = [line.strip() for line in f_in if line.strip()
                       and not line.startswith('#')]
    except FileNotFoundError:
        print(f"CRITICAL Error: Input domain list file not found at {input_file_path}. Script will exit.")
        return
    except Exception as e:
        print(f"CRITICAL Error reading domain list file {input_file_path}: {e}. Script will exit.")
        return

    if not domains:
        print("No domains found in the input file. Exiting.")
        return

    print(f"Found {len(domains)} domains to process.")
    final_domain_ip_map = {}

    for i, domain in enumerate(domains):
        progress = (i + 1) / len(domains) * 100
        print(f"Processing domain {i + 1}/{len(domains)} ({progress:.1f}%): {domain}")

        # Get all IPs from all configured DNS servers
        all_ips_from_dns_query, dns_success = get_ips_from_dns_servers(domain)
        if not dns_success:
            print(f"  No IPs found for {domain} from any specified DNS server after retries.")
            continue

        # Select the first IP as the best one (simple approach)
        if all_ips_from_dns_query:
            best_ip = all_ips_from_dns_query[0]
            final_domain_ip_map[domain] = best_ip
            print(f"  ==> Selected for {domain}: {best_ip}")
        else:
            print(f"  ==> FAILED to resolve {domain}")

    # Write results to output file
    try:
        with open(output_file_path, 'w', encoding='utf-8') as f_out:
            for domain, ip in final_domain_ip_map.items():
                f_out.write(f"{ip}\t{domain}\n")
        print(f"\nSuccessfully wrote {len(final_domain_ip_map)} resolved domain-IP pairs to {output_file_path}")
    except Exception as e:
        print(f"Error writing to output file {output_file_path}: {e}")

    print("Domain processing finished.")

if __name__ == "__main__":
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    input_file = os.path.join(PROJECT_ROOT, "routes", "需要获取IP的域名列表.txt")
    output_file = os.path.join(PROJECT_ROOT, "routes", "常用境外IP.txt")
    
    parser = argparse.ArgumentParser(
        description="Resolve domain names to IP addresses using multiple DNS servers.")
    parser.add_argument(
        "input_file",
        default=input_file,
        nargs='?',
        help=f"Path to the input file. Defaults to {input_file}")
    parser.add_argument(
        "output_file",
        default=output_file,
        nargs='?',
        help=f"Path to the output file. Defaults to {output_file}")
    args = parser.parse_args()

    print("===== Local Domain Resolution Script started =====")
    print(f"Input domain list: {args.input_file}")
    print(f"Output IP list: {args.output_file}")
    print(f"DNS Servers: {DNS_SERVERS_TO_USE}")

    try:
        process_domains(args.input_file, args.output_file)
        print("===== Local Domain Resolution Script finished successfully =====")
    except Exception as e:
        print(f"CRITICAL ERROR in main processing: {type(e).__name__} - {e}")
        sys.exit(1)