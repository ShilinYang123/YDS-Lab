#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
wstunnel 综合模式启动脚本
同时支持WireGuard和代理模式
"""

import os
import sys
import time
import socket
import subprocess
import configparser
import signal
import re
import datetime
import logging
import shutil

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            os.path.join(
                os.path.dirname(
                    os.path.abspath(__file__)),
                '..',
                'logs',
                'wstunnel_combined.log'),
            encoding='utf-8')])
logger = logging.getLogger('wstunnel_combined')

# 脚本路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.env")
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")

# 导入公共函数
from Scripts.common.utils import load_config, is_process_running, kill_process_by_name, is_port_in_use

# 导入代理模式和WireGuard模式的函数
sys.path.append(SCRIPT_DIR)
try:
    from wstunnel_proxy import generate_pac_file, create_browser_config_guide, display_proxy_info, test_proxy_connection
    from wstunnel_wireguard import check_wireguard_config
except ImportError:
    # 如果无法导入，定义一些基本函数
    def generate_pac_file(config):
        return None, None, None

    def create_browser_config_guide(config):
        return None

    def display_proxy_info(config, socks5_port, http_port):
        print(f"SOCKS5代理: 127.0.0.1:{socks5_port}")
        print(f"HTTP代理: 127.0.0.1:{http_port}")

    def test_proxy_connection(socks5_port, http_port):
        return is_port_in_use(socks5_port) and is_port_in_use(http_port)

    def check_wireguard_config(config, socks5_port):
        pass


def test_server_connectivity(server_ip, port=443):
    """测试服务器连通性"""
    try:
        # 根据IPv6开关选择合适的socket类型
        config = load_config()
        ipv6_enable = config.get('IPv6_ENABLE', 'false').lower() == 'true'
        
        if ipv6_enable and ':' in server_ip:
            # IPv6地址
            sock_type = socket.AF_INET6
            addr = (server_ip, port, 0, 0)
        else:
            # IPv4地址
            sock_type = socket.AF_INET
            addr = (server_ip, port)
            
        with socket.socket(sock_type, socket.SOCK_STREAM) as s:
            s.settimeout(5)
            result = s.connect_ex(addr)
            if result == 0:
                logger.info(f"服务器连通性测试通过: {server_ip}:{port}")
                return True
            else:
                logger.warning(
                    f"服务器连通性测试失败: {server_ip}:{port}, 错误代码: {result}")
                return False
    except Exception as e:
        logger.error(f"服务器连通性测试异常: {e}")
        return False


def start_wstunnel_combined(config):
    """启动wstunnel综合模式(同时支持WireGuard和代理)"""
    # IPv6开关配置
    ipv6_enable = config.get('IPv6_ENABLE', 'false').lower() == 'true'
    ipv6_prefer = config.get('IPv6_PREFER', 'false').lower() == 'true'
    ipv6_fallback = config.get('IPv6_FALLBACK', 'true').lower() == 'true'
    
    # 根据IPv6开关选择服务器地址
    if ipv6_enable:
        server_ip = config.get('SERVER_IPV6', config.get('SERVER_IP', '192.210.206.52'))
        # IPv6监听地址
        ipv6_listen_addr = config.get('IPv6_LISTEN_ADDR', '[::1]')
        ipv6_proxy_addr = config.get('IPv6_PROXY_ADDR', '[::]')
    else:
        server_ip = config.get('SERVER_IP', '192.210.206.52')
        # IPv4监听地址
        ipv4_listen_addr = '127.0.0.1'
        ipv4_proxy_addr = '127.0.0.1'
    
    # UDP转发端口(WireGuard模式)
    wstunnel_port = int(config.get('WSTUNNEL_PORT', '1081'))
    # SOCKS5代理端口
    socks5_port = int(config.get('SOCKS5_PORT', '1082'))
    # HTTP代理端口
    http_port = int(config.get('HTTP_PORT', '8081'))
    server_port = int(config.get('SERVER_PORT', '443'))
    server_restrict_port = int(config.get('SERVER_RESTRICT_PORT', '8443'))
    prefix = config.get('PREFIX', 'xYz123AbC')
    user = config.get('USER', 'youruser')
    password = config.get('PASS', 'yourpass')

    # 检查SOCKS5端口
    if is_port_in_use(socks5_port):
        logger.warning(f"SOCKS5端口 {socks5_port} 已被占用，尝试终止占用进程")
        kill_process_by_name('wstunnel.exe')
        time.sleep(1)

        # 再次检查端口
        if is_port_in_use(socks5_port):
            # 尝试寻找可用端口
            for test_port in range(socks5_port + 1, socks5_port + 10):
                if not is_port_in_use(test_port):
                    logger.info(f"使用备用SOCKS5端口: {test_port}")
                    socks5_port = test_port
                    break
            else:
                logger.error(f"无法找到可用的SOCKS5端口，启动失败")
                return False

    # 检查HTTP端口
    if is_port_in_use(http_port):
        logger.warning(f"HTTP端口 {http_port} 已被占用，尝试终止占用进程")
        # 我们已经在SOCKS5端口检查中终止了wstunnel.exe，这里检查其他可能的进程

        # 再次检查端口
        if is_port_in_use(http_port):
            # 尝试寻找可用端口
            for test_port in range(http_port + 1, http_port + 10):
                if not is_port_in_use(test_port):
                    logger.info(f"使用备用HTTP端口: {test_port}")
                    http_port = test_port
                    break
            else:
                logger.error(f"无法找到可用的HTTP端口，启动失败")
                return False

    # 测试服务器连通性
    if not test_server_connectivity(server_ip, server_port):
        logger.warning(f"无法连接到服务器 {server_ip}:{server_port}，但仍将尝试启动wstunnel")

    # 构建wstunnel命令
    wstunnel_exe = os.path.join(SCRIPT_DIR, "wstunnel.exe")
    if not os.path.exists(wstunnel_exe):
        logger.error(f"wstunnel.exe不存在: {wstunnel_exe}")
        return False

    # 根据IPv6开关构建监听地址
    if ipv6_enable:
        udp_listen_addr = ipv6_listen_addr
        socks5_listen_addr = ipv6_proxy_addr
        http_listen_addr = ipv6_proxy_addr
        server_local_addr = ipv6_listen_addr
    else:
        udp_listen_addr = '127.0.0.1'
        socks5_listen_addr = '127.0.0.1'
        http_listen_addr = '127.0.0.1'
        server_local_addr = '127.0.0.1'

    # 综合模式命令，同时包含UDP转发(WireGuard)和代理(SOCKS5/HTTP)
    cmd = [
        wstunnel_exe,
        "--log-lvl",
        "DEBUG",
        "client",
        "-L",
        # WireGuard模式
        f"udp://{udp_listen_addr}:{wstunnel_port}:{server_local_addr}:{server_restrict_port}",
        "-L",
        f"socks5://{socks5_listen_addr}:{socks5_port}",
        "-L",
        # HTTP代理
        f"http://{http_listen_addr}:{http_port}?login={user}&password={password}",
        f"ws://{server_ip}:{server_port}"
    ]

    # 启动wstunnel进程
    try:
        logger.info(f"启动wstunnel综合模式命令: {' '.join(cmd)}")

        log_file = os.path.join(
            LOGS_DIR, f"wstunnel_combined_{
                datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        with open(log_file, 'w', encoding='utf-8') as f:
            process = subprocess.Popen(
                cmd,
                stdout=f,
                stderr=f,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )

        # 等待进程启动
        time.sleep(2)

        # 检查进程是否成功启动
        if process.poll() is None:
            logger.info(f"wstunnel启动成功，进程ID: {process.pid}")
            logger.info(f"IPv6模式: {'启用' if ipv6_enable else '禁用'}")
            logger.info(f"WireGuard UDP转发: {udp_listen_addr}:{wstunnel_port}")
            logger.info(f"SOCKS5代理: {socks5_listen_addr}:{socks5_port}")
            logger.info(f"HTTP代理: {http_listen_addr}:{http_port}")
            logger.info(f"服务器地址: {server_ip}:{server_port}")

            # 检查WireGuard配置
            check_wireguard_config(config, wstunnel_port)

            # 生成PAC文件
            # 修改配置对象以反映SOCKS5代理端口的变化
            proxy_config = config.copy()
            proxy_config['SOCKS5_PORT'] = str(socks5_port + 1)
            generate_pac_file(proxy_config)

            # 创建浏览器配置指南
            create_browser_config_guide(proxy_config)

            return True, socks5_port, socks5_port + 1, http_port
        else:
            logger.error(f"wstunnel进程已退出，状态码: {process.returncode}")
            return False, 0, 0, 0
    except Exception as e:
        logger.error(f"启动wstunnel失败: {e}")
        return False, 0, 0, 0


def display_combined_info(config, wireguard_port, socks5_port, http_port):
    """显示综合模式信息"""
    # 获取IPv6配置
    ipv6_enable = config.get('IPv6_ENABLE', 'false').lower() == 'true'
    
    if ipv6_enable:
        ipv6_listen_addr = config.get('IPv6_LISTEN_ADDR', '[::1]')
        ipv6_proxy_addr = config.get('IPv6_PROXY_ADDR', '[::]')
        wireguard_addr = ipv6_listen_addr
        socks5_addr = ipv6_proxy_addr
        http_addr = ipv6_proxy_addr
    else:
        wireguard_addr = '127.0.0.1'
        socks5_addr = '127.0.0.1'
        http_addr = '127.0.0.1'
    
    print("\n" + "=" * 60)
    print("WireGuard UDP转发已启动：")
    print(f"  端口: {wireguard_addr}:{wireguard_port}")
    print(f"  WireGuard配置文件中的Endpoint应设为: {wireguard_addr}:{wireguard_port}")
    print(f"  IPv6模式: {'启用' if ipv6_enable else '禁用'}")

    print("\nSOCKS5代理已启动：")
    print(f"  地址: {socks5_addr}:{socks5_port}")
    print(f"  用户名: {config.get('USER', 'youruser')}")
    print(f"  密码: {config.get('PASS', 'yourpass')}")

    print("\nHTTP代理已启动：")
    print(f"  地址: {http_addr}:{http_port}")
    print(f"  用户名: {config.get('USER', 'youruser')}")
    print(f"  密码: {config.get('PASS', 'yourpass')}")

    print("\nPAC文件已生成：")
    proxy_config = config.copy()
    proxy_config['SOCKS5_PORT'] = str(socks5_port)
    global_pac_path, smart_pac_path, direct_pac_path = generate_pac_file(
        proxy_config)
    if global_pac_path:
        print(f"  全局代理: {global_pac_path}")
    if smart_pac_path:
        print(f"  智能分流: {smart_pac_path}")
    if direct_pac_path:
        print(f"  全部直连: {direct_pac_path}")

    print("\n浏览器配置指南：")
    guide_path = create_browser_config_guide(proxy_config)
    if guide_path:
        print(f"  {guide_path}")
    print("=" * 60)


def main():
    print("=" * 60)
    print("AUTOVPN - wstunnel 综合模式启动工具")
    print("同时支持WireGuard和代理模式")
    print("=" * 60)

    # 加载配置
    config = load_config()
    if not config:
        print("错误: 无法加载配置文件，启动操作取消")
        return False

    # 终止已有wstunnel进程
    if is_process_running('wstunnel.exe'):
        print("发现正在运行的wstunnel进程，正在终止...")
        kill_process_by_name('wstunnel.exe')

    # 启动wstunnel综合模式
    success, wireguard_port, socks5_port, http_port = start_wstunnel_combined(
        config)

    if success:
        display_combined_info(config, wireguard_port, socks5_port, http_port)

        # 测试代理连接
        if test_proxy_connection(socks5_port, http_port):
            print("\n代理连接测试通过!")
        else:
            print("\n警告: 代理连接测试失败，但服务已启动。请检查日志了解详情。")

        print("\n现在您可以:")
        print("1. 启动WireGuard客户端并连接隧道")
        print("2. 配置浏览器或应用程序使用SOCKS5/HTTP代理")
        print("3. 使用PAC文件实现自动分流")
    else:
        print("\nwstunnel启动失败，请检查日志了解详情")

    return success


if __name__ == "__main__":
    try:
        if not main():
            input("\n按Enter键退出...")
        # 保持脚本运行，除非用户按Ctrl+C
        print("\n按Ctrl+C退出...")
        if main():
            print("\n服务运行中，按Ctrl+C退出...")
            while True:
                time.sleep(1)
        else:
            input("\n按Enter键退出...")
    except KeyboardInterrupt:
        print("\n用户中断，正在退出...")
        kill_process_by_name('wstunnel.exe')
        print("已终止wstunnel进程")
    except Exception as e:
        logger.error(f"脚本执行异常: {e}")
        print(f"发生错误: {e}")
        kill_process_by_name('wstunnel.exe')