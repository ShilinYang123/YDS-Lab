#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
wstunnel WireGuard模式启动脚本
用于启动wstunnel UDP转发，供WireGuard使用
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
                'wstunnel_wireguard.log'),
            encoding='utf-8')])
logger = logging.getLogger('wstunnel_wireguard')

# 脚本路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.env")
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")

# 导入公共函数
from Scripts.common.utils import load_config, is_process_running, kill_process_by_name, is_port_in_use

# 确保日志目录存在
os.makedirs(LOGS_DIR, exist_ok=True)


def test_server_connectivity(server_ip, port=443):
    """测试服务器连通性"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)
            result = s.connect_ex((server_ip, port))
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


def start_wstunnel_wireguard(config):
    """启动wstunnel UDP转发"""
    # 从config.env加载配置
    server_ip = config.get('SERVER_IP', '127.0.0.1')
    socks5_port = int(config.get('WSTUNNEL_PORT', '1081'))
    server_port = int(config.get('SERVER_PORT', '443'))
    server_restrict_port = int(config.get('SERVER_RESTRICT_PORT', '51820'))
    prefix = config.get('PREFIX', 'vpn')

    # 如果端口已被占用，查找可用端口
    if is_port_in_use(socks5_port):
        logger.warning(f"端口 {socks5_port} 已被占用，尝试终止占用进程")
        kill_process_by_name('wstunnel.exe')
        time.sleep(1)

        # 再次检查端口
        if is_port_in_use(socks5_port):
            # 尝试寻找可用端口
            for test_port in range(socks5_port + 1, socks5_port + 10):
                if not is_port_in_use(test_port):
                    logger.info(f"使用备用端口: {test_port}")
                    socks5_port = test_port
                    break
            else:
                logger.error(f"无法找到可用端口，启动失败")
                return False

    # 测试服务器连通性
    if not test_server_connectivity(server_ip, server_port):
        logger.warning(f"无法连接到服务器 {server_ip}:{server_port}，但仍将尝试启动wstunnel")

    # 构建wstunnel命令
    wstunnel_exe = os.path.join(SCRIPT_DIR, "wstunnel.exe")
    if not os.path.exists(wstunnel_exe):
        logger.error(f"wstunnel.exe不存在: {wstunnel_exe}")
        return False

    # WireGuard模式使用UDP转发，ws协议（租用服务器限制）
    cmd = [
        wstunnel_exe,
        "--log-lvl",
        "DEBUG",
        "client",
        "-L",
        f"udp://127.0.0.1:{socks5_port}:{server_ip}:{server_restrict_port}",
        f"ws://{server_ip}:{server_port}"
    ]

    # 启动wstunnel进程
    try:
        logger.info(f"启动wstunnel UDP转发命令: {' '.join(cmd)}")

        log_file = os.path.join(
            LOGS_DIR, f"wstunnel_wireguard_{
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
            logger.info(f"WireGuard应使用Endpoint: 127.0.0.1:{socks5_port}")

            # 检查WireGuard配置
            check_wireguard_config(config, socks5_port)

            return True
        else:
            logger.error(f"wstunnel进程已退出，状态码: {process.returncode}")
            return False
    except Exception as e:
        logger.error(f"启动wstunnel失败: {e}")
        return False


def check_wireguard_config(config, wstunnel_port):
    """检查WireGuard配置是否正确"""
    wg_conf_path = config.get('WG_CONF_PATH', '')

    if not wg_conf_path or not os.path.exists(wg_conf_path):
        wg_dir = os.path.join(PROJECT_ROOT, "config", "wireguard", "client")
        if os.path.exists(wg_dir):
            for file in os.listdir(wg_dir):
                if file.endswith('.conf'):
                    wg_conf_path = os.path.join(wg_dir, file)
                    break

    if not wg_conf_path or not os.path.exists(wg_conf_path):
        logger.warning("无法找到WireGuard配置文件")
        return

    try:
        with open(wg_conf_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查Endpoint设置
        endpoint_match = re.search(
            r"Endpoint\s*=\s*127\.0\.0\.1:(\d+)", content)
        if endpoint_match:
            current_port = int(endpoint_match.group(1))
            if current_port != wstunnel_port:
                logger.warning(
                    f"WireGuard端口({current_port})与wstunnel端口({wstunnel_port})不一致")
                logger.warning(
                    f"WireGuard配置中的Endpoint端口 ({current_port}) 与当前wstunnel端口 ({wstunnel_port}) 不一致")
                logger.info(f"请更新WireGuard配置文件: {wg_conf_path}")
            else:
                logger.info(
                    f"WireGuard配置中的Endpoint端口与wstunnel端口一致: {wstunnel_port}")
        else:
            logger.warning(f"在WireGuard配置中未找到Endpoint设置")
    except Exception as e:
        logger.error(f"检查WireGuard配置失败: {e}")


def main():
    print("=" * 60)
    print("AUTOVPN - wstunnel WireGuard模式启动工具")
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

    # 启动wstunnel
    success = start_wstunnel_wireguard(config)

    if success:
        print("\nwstunnel WireGuard模式启动成功!")
        print(f"WireGuard应使用Endpoint: 127.0.0.1:{config.get('LOCAL_PORT')}")
        print("\n现在您可以启动WireGuard客户端并连接隧道")
    else:
        print("\nwstunnel启动失败，请检查日志了解详情")

    return success


if __name__ == "__main__":
    try:
        main()
        # 保持脚本运行，除非用户按Ctrl+C
        print("\n按Ctrl+C退出...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n用户中断，正在退出...")
        kill_process_by_name('wstunnel.exe')
        print("已终止wstunnel进程")
    except Exception as e:
        logger.error(f"脚本执行异常: {e}")
        print(f"发生错误: {e}")
        kill_process_by_name('wstunnel.exe')
        # 更新MTU和保活参数
        # 从config.env读取MTU配置
    from load_config import load_config
    env_config = load_config()
    config.mtu = int(env_config.get('MTU_SIZE', 1420))  # 从配置文件读取MTU值
    config.keepalive = int(
        env_config.get(
            'KEEPALIVE_INTERVAL',
            60))  # 从配置文件读取心跳间隔