#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
wstunnel 客户端启动脚本
用于启动wstunnel服务
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
                'wstunnel_client.log'),
            encoding='utf-8')])
logger = logging.getLogger('wstunnel_client')

# 脚本路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.env")
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")

# 导入公共函数
from Scripts.common.utils import load_config, is_process_running, kill_process_by_name, is_port_in_use

# 确保日志目录存在
os.makedirs(LOGS_DIR, exist_ok=True)

def check_wstunnel_service():
    """检查wstunnel服务状态"""
    try:
        # 检查wstunnel服务是否存在并运行
        result = subprocess.run('sc query wstunnel', shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
        if result.returncode == 0 and 'RUNNING' in result.stdout:
            logger.info("检测到wstunnel系统服务正在运行")
            return True
        return False
    except Exception as e:
        logger.error(f"检查wstunnel服务状态时出错: {e}")
        return False

def stop_wstunnel_service():
    """停止wstunnel系统服务"""
    try:
        logger.info("尝试停止wstunnel系统服务")
        result = subprocess.run('sc stop wstunnel', shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
        if result.returncode == 0:
            logger.info("已发送停止wstunnel服务的命令")
            # 等待服务停止
            for _ in range(5):  # 最多等待5秒
                time.sleep(1)
                check_result = subprocess.run('sc query wstunnel', shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
                if 'STOPPED' in check_result.stdout or check_result.returncode != 0:
                    logger.info("wstunnel服务已停止")
                    return True
            logger.warning("等待wstunnel服务停止超时")
            return False
        else:
            logger.error(f"停止wstunnel服务失败: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"停止wstunnel服务时出错: {e}")
        return False

def start_wstunnel_client():
    """启动wstunnel客户端"""
    logger.info("正在启动wstunnel客户端...")
    
    # 加载配置
    config = load_config()
    
    # 获取配置参数
    wstunnel_port = config.get('WSTUNNEL_PORT', '1081')
    server_restrict_port = config.get('SERVER_RESTRICT_PORT', '8443')
    server_ip = config.get('SERVER_IP', '192.210.206.52')
    server_port = config.get('SERVER_PORT', '443')
    
    # 检查wstunnel系统服务
    if check_wstunnel_service():
        logger.info("检测到wstunnel作为系统服务运行，尝试停止服务")
        if not stop_wstunnel_service():
            logger.error("无法停止wstunnel系统服务，请手动停止后再试")
            return False
    
    # 检查wstunnel进程是否已经在运行
    if is_process_running('wstunnel.exe'):
        logger.info("wstunnel进程已经在运行，先停止现有进程")
        kill_process_by_name('wstunnel.exe')
        time.sleep(1)  # 等待进程完全终止
        
    # 检查端口是否被占用
    if is_port_in_use(int(wstunnel_port)):
        logger.info(f"端口 {wstunnel_port} 已被占用，尝试释放")
        # 在Windows上使用netstat查找占用端口的进程
        try:
            cmd = f'netstat -ano | findstr :{wstunnel_port}'
            result = subprocess.check_output(cmd, shell=True, text=True, encoding='utf-8', errors='replace')
            lines = result.strip().split('\n')
            for line in lines:
                if f':{wstunnel_port}' in line:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        logger.info(f"找到占用端口 {wstunnel_port} 的进程 PID: {pid}")
                        # 终止进程
                        subprocess.run(f'taskkill /F /PID {pid}', shell=True, capture_output=True)
                        logger.info(f"已终止进程 PID: {pid}")
                        time.sleep(1)  # 等待端口释放
        except Exception as e:
            logger.error(f"尝试释放端口时出错: {e}")
            # 继续执行，即使释放端口失败
    
    # 构建wstunnel命令
    wstunnel_exe = os.path.join(SCRIPT_DIR, "wstunnel.exe")
    if not os.path.exists(wstunnel_exe):
        logger.error(f"wstunnel.exe不存在: {wstunnel_exe}")
        return False
    
    # 构建wstunnel命令行参数
    cmd = [
        wstunnel_exe,
        "--log-lvl", "DEBUG",
        "client",
        "-L", f"udp://127.0.0.1:{wstunnel_port}:127.0.0.1:{server_restrict_port}",
        f"ws://{server_ip}:{server_port}"
    ]
    
    try:
        # 启动wstunnel进程
        logger.info(f"启动命令: {' '.join(cmd)}")
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace',
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        # 等待进程启动
        time.sleep(2)
        
        # 检查进程是否成功启动
        if process.poll() is None:
            logger.info("wstunnel客户端启动成功")
            return True
        else:
            try:
                stdout, stderr = process.communicate(timeout=1)
                logger.error(f"wstunnel客户端启动失败: {stderr}")
            except Exception as e:
                logger.error(f"获取进程输出时发生错误: {e}")
            return False
    except Exception as e:
        logger.error(f"启动wstunnel客户端时发生错误: {e}")
        return False

def main():
    """主函数"""
    print("="*60)
    print("          AUTOVPN - wstunnel客户端启动工具")
    print("="*60)
    
    success = start_wstunnel_client()
    
    if success:
        print("\n✅ wstunnel客户端已成功启动")
        return 0
    else:
        print("\n❌ wstunnel客户端启动失败，请检查日志")
        return 1

if __name__ == "__main__":
    sys.exit(main())