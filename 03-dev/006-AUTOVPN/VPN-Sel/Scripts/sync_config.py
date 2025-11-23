#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys

# 设置控制台编码和异常处理
if os.name == 'nt':  # Windows系统
    import codecs
    import threading

    # 重定向stderr以隐藏subprocess的编码异常
    class QuietStderr:
        def write(self, data):
            # 过滤掉特定的编码错误信息
            if 'UnicodeDecodeError' not in str(
                    data) and 'illegal multibyte sequence' not in str(data):
                sys.__stderr__.write(data)

        def flush(self):
            sys.__stderr__.flush()

    sys.stderr = QuietStderr()
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())

import shutil
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.env")
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")


def load_config():
    """加载并验证配置文件"""
    config = {}
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.split('#')[0].strip()

        # 验证必要参数
        required_params = ['WG_CONF_PATH', 'SERVER_IP', 'WSTUNNEL_PORT']
        for param in required_params:
            if param not in config:
                raise ValueError(f"缺少必要参数: {param}")

        return config
    except Exception as e:
        print(f"[错误] 配置加载失败: {e}")
        sys.exit(1)


def sync_wireguard_config(config):
    """同步WireGuard配置"""
    wg_conf_path = config['WG_CONF_PATH']
    if not os.path.exists(wg_conf_path):
        # 从备份恢复
        backup_path = os.path.join(
            PROJECT_ROOT, "备用文件/config/wireguard/client/PC3.conf")
        if os.path.exists(backup_path):
            shutil.copy(backup_path, wg_conf_path)
            print(f"✅ 已从备份恢复WireGuard配置: {backup_path}")
        else:
            raise FileNotFoundError(f"WireGuard配置文件和备份均不存在: {wg_conf_path}")

    # 读取常用境外IP.txt获取最新IP列表
    ip_file = os.path.join(PROJECT_ROOT, "routes", "常用境外IP.txt")
    allowed_ips = set()  # 使用set自动去重

    if os.path.exists(ip_file):
        with open(ip_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and (
                        ' ' in line or '\t' in line):
                    parts = line.split()
                    if len(parts) >= 2:
                        ip = parts[0]
                        # 验证IP格式并添加/32后缀
                        try:
                            import ipaddress
                            ipaddress.ip_address(ip)  # 验证IP格式
                            allowed_ips.add(f"{ip}/32")
                        except ValueError:
                            continue

    # 添加默认的内网IP
    default_ips = ['10.9.0.1/32', '10.9.0.2/32', '10.9.0.3/32']
    for ip in default_ips:
        allowed_ips.add(ip)

    # 更新WireGuard配置文件
    with open(wg_conf_path, 'r+', encoding='utf-8') as f:
        content = f.read()
        import re

        # 更新Endpoint
        content = re.sub(r"^Endpoint\s*=\s*.*\n",
                         f"Endpoint = 127.0.0.1:{config['WSTUNNEL_PORT']}\n",
                         content, flags=re.MULTILINE)

        # 更新MTU参数
        if 'MTU_SIZE' in config:
            content = re.sub(r"^MTU\s*=\s*.*$",
                             f"MTU = {config['MTU_SIZE']}",
                             content, flags=re.MULTILINE)

        # 更新DNS参数
        if 'PRIMARY_DNS' in config:
            content = re.sub(r"^DNS\s*=\s*.*$",
                             f"DNS = {config['PRIMARY_DNS']}",
                             content, flags=re.MULTILINE)

        # 更新PersistentKeepalive参数
        if 'KEEPALIVE_INTERVAL' in config:
            content = re.sub(
                r"^PersistentKeepalive\s*=\s*.*$",
                f"PersistentKeepalive = {
                    config['KEEPALIVE_INTERVAL']}",
                content,
                flags=re.MULTILINE)

        # 更新AllowedIPs，去重后的IP列表
        allowed_ips_str = ', '.join(sorted(allowed_ips))
        content = re.sub(r"^AllowedIPs\s*=\s*.*\n",
                         f"AllowedIPs = {allowed_ips_str}\n",
                         content, flags=re.MULTILINE)

        f.seek(0)
        f.write(content)
        f.truncate()

    print(f"✅ 已更新WireGuard配置:")
    print(f"   - Endpoint: 127.0.0.1:{config['WSTUNNEL_PORT']}")
    print(f"   - MTU: {config.get('MTU_SIZE', '未设置')}")
    print(f"   - DNS: {config.get('PRIMARY_DNS', '未设置')}")
    print(
        f"   - PersistentKeepalive: {config.get('KEEPALIVE_INTERVAL', '未设置')}")
    print(f"   - AllowedIPs: {len(allowed_ips)}个去重IP")


def sync_proxy_config(config):
    """同步代理配置"""
    pac_path = os.path.join(SCRIPT_DIR, "proxy.pac")
    with open(pac_path, 'w', encoding='utf-8') as f:
        f.write(f"function FindProxyForURL(url, host) {{\n")
        f.write(
            f"    return 'SOCKS5 127.0.0.1:{
                config.get(
                    'SOCKS5_PORT',
                    '1081')};'\n")
        f.write("}}")


def main():
    print("🔄 开始同步全系统配置...")
    try:
        config = load_config()

        # 创建日志目录
        os.makedirs(LOG_DIR, exist_ok=True)
        log_file = os.path.join(
            LOG_DIR, f"sync_log_{
                datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

        with open(log_file, 'w', encoding='utf-8') as log:
            # 同步WireGuard配置
            log.write("=== 同步WireGuard配置 ===\n")
            sync_wireguard_config(config)
            log.write("WireGuard配置同步成功\n")

            # 同步代理配置
            log.write("\n=== 同步代理配置 ===\n")
            sync_proxy_config(config)
            log.write("代理配置同步成功\n")

            print(f"✅ 所有配置已同步完成，日志见: {log_file}")

    except Exception as e:
        print(f"[错误] 配置同步失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
