#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import subprocess

# 添加脚本目录到Python路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

def load_config():
    """加载config.env配置文件"""
    config = {}
    config_path = os.path.join(SCRIPT_DIR, "config.env")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        # 移除注释部分
                        if '#' in value:
                            value = value.split('#')[0]
                        config[key.strip()] = value.strip()
        return config
    except FileNotFoundError:
        print(f"[警告] 配置文件不存在: {config_path}")
        return {}
    except Exception as e:
        print(f"[错误] 读取配置文件失败: {e}")
        return {}

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

def update_hosts_directly(domain, ip):
    """直接更新hosts文件，不依赖现有脚本"""
    try:
        HOSTS_FILE = r'C:\Windows\System32\drivers\etc\hosts'
        
        # 读取现有hosts内容
        original_hosts = []
        if os.path.exists(HOSTS_FILE):
            with open(HOSTS_FILE, 'r', encoding='utf-8') as f:
                original_hosts = f.readlines()
        
        # 分离普通hosts条目和AUTOVPN部分
        normal_lines = []
        auto_vpn_lines = []
        in_auto_vpn_section = False
        
        for line in original_hosts:
            if line.strip() == '# AUTOVPN自动写入':
                in_auto_vpn_section = True
                auto_vpn_lines.append(line)  # 保留标题行
                continue
            
            if in_auto_vpn_section:
                # 检查是否是AUTOVPN部分的条目
                if line.startswith('#') or (line.strip() == ''):
                    # 新的注释部分或空行，说明AUTOVPN部分结束
                    in_auto_vpn_section = False
                    normal_lines.append(line)
                elif '\t' in line or ' ' in line:
                    # 检查是否是当前要更新的域名
                    parts = line.split()
                    if len(parts) >= 2:
                        existing_domain = parts[1]
                        # 如果不是我们要更新的域名，则保留
                        if existing_domain != domain and existing_domain != f"www.{domain}":
                            auto_vpn_lines.append(line)
                else:
                    # 不是AUTOVPN部分的条目
                    in_auto_vpn_section = False
                    normal_lines.append(line)
            else:
                normal_lines.append(line)
        
        # 添加新的域名映射到AUTOVPN部分
        if '# AUTOVPN自动写入\n' not in auto_vpn_lines:
            auto_vpn_lines.insert(0, '# AUTOVPN自动写入\n')
        
        auto_vpn_lines.append(f"{ip}\t{domain}\n")
        # 自动添加www版本
        if not domain.startswith('www.'):
            auto_vpn_lines.append(f"{ip}\twww.{domain}\n")
        
        # 确保AUTOVPN部分以空行结束
        if auto_vpn_lines and not auto_vpn_lines[-1].endswith('\n'):
            auto_vpn_lines[-1] += '\n'
        if not auto_vpn_lines[-1].strip():
            auto_vpn_lines.append('\n')
        
        # 合并内容
        final_hosts_lines = normal_lines + auto_vpn_lines
        
        # 写入新的hosts文件
        with open(HOSTS_FILE, 'w', encoding='utf-8') as f:
            f.writelines(final_hosts_lines)
            
        # 刷新DNS缓存
        try:
            subprocess.run(['ipconfig', '/flushdns'], 
                         capture_output=True, text=True)
        except:
            pass
            
        print(f"已更新hosts文件: {domain} -> {ip}")
        return True
    except Exception as e:
        print(f"[错误] 更新hosts文件失败: {e}")
        return False

def update_wireguard_config_directly(ip):
    """直接更新WireGuard配置文件"""
    try:
        # 从配置文件获取WireGuard配置路径
        config = load_config()
        wg_conf_path = config.get('WG_CONF_PATH', '')
        
        if not wg_conf_path or not os.path.exists(wg_conf_path):
            print(f"[错误] WireGuard配置文件不存在: {wg_conf_path}")
            return False
            
        # 读取配置文件
        with open(wg_conf_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 查找AllowedIPs行
        import re
        allowed_ips_match = re.search(r"^AllowedIPs\s*=\s*(.*)$", content, re.MULTILINE)
        if not allowed_ips_match:
            print("[错误] 未找到AllowedIPs配置项")
            return False
            
        # 获取现有的IP列表
        existing_ips = [ip.strip() for ip in allowed_ips_match.group(1).split(',')]
        
        # 添加新的IP（带/32后缀），但排除本机地址
        new_ip_entry = f"{ip}/32"
        local_ip = config.get('WG_LOCAL_IP', '10.9.0.2')
        local_ip_entry = f"{local_ip}/32"
        
        # 确保不添加本机地址到AllowedIPs
        if new_ip_entry != local_ip_entry and new_ip_entry not in existing_ips:
            existing_ips.append(new_ip_entry)
            # 更新配置内容
            new_allowed_ips = ", ".join(existing_ips)
            content = re.sub(r"^AllowedIPs\s*=\s*.*$", 
                           f"AllowedIPs = {new_allowed_ips}", 
                           content, flags=re.MULTILINE)
            
            # 写入更新后的配置
            with open(wg_conf_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
        print(f"已更新WireGuard配置: 添加 {ip}/32")
        return True
    except Exception as e:
        print(f"[错误] 更新WireGuard配置失败: {e}")
        return False

def main():
    domain = "ip.sb"
    if len(sys.argv) > 1:
        domain = sys.argv[1]
    
    print(f"=== 添加单个域名并完成全流程 ===")
    print(f"域名: {domain}")
    
    # 清理域名格式
    domain = domain.replace('http://', '').replace('https://', '')
    domain = domain.split('/')[0]  # 去掉路径
    domain = domain.split(':')[0]  # 去掉端口
    
    print(f"\n正在处理域名: {domain}")
    
    # 1. 添加到域名列表
    domain_file_path = os.path.join(PROJECT_ROOT, "routes", "需要获取IP的域名列表.txt")
    existing_domains = []
    try:
        if os.path.exists(domain_file_path):
            with open(domain_file_path, 'r', encoding='utf-8') as f:
                existing_domains = [line.strip() for line in f.readlines() 
                                  if line.strip() and not line.startswith('#')]
        
        if domain not in existing_domains:
            with open(domain_file_path, 'a', encoding='utf-8') as f:
                f.write(f"\n{domain}")
            print(f"✅ 已添加域名 {domain} 到解析列表")
        else:
            print(f"域名 {domain} 已存在于列表中")
    except Exception as e:
        print(f"[错误] 添加域名到列表失败: {e}")
    
    # 2. 解析IP
    print("\n正在解析域名IP...")
    ip = resolve_single_domain_ip(domain)
    if ip:
        print(f"✅ 域名 {domain} 解析成功: {ip}")
        
        # 3. 更新hosts文件
        print("\n正在更新hosts文件...")
        if update_hosts_directly(domain, ip):
            print(f"✅ 已更新hosts文件: {domain} -> {ip}")
        
        # 4. 更新WireGuard配置
        print("\n正在更新WireGuard配置...")
        if update_wireguard_config_directly(ip):
            print(f"✅ 已更新WireGuard配置: 添加 {ip}/32")
    else:
        print(f"[错误] 域名 {domain} 解析失败")

if __name__ == "__main__":
    main()