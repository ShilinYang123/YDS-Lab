#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NSSM wstunnel服务管理脚本
用于将wstunnel安装为Windows系统服务
"""

import os
import subprocess
import platform
import time
import sys
import traceback

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 定义常量
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
NSSM_EXE = os.path.join(SCRIPT_DIR, 'nssm.exe')
SERVICE_NAME = 'wstunnel'  # 修改服务名称
WSTUNNEL_EXE = os.path.join(SCRIPT_DIR, 'wstunnel.exe')

# 导入配置加载函数和公共函数
from Scripts.common.utils import load_config, is_process_running, kill_process_by_name, is_port_in_use


def get_service_status():
    """获取服务状态：('stopped', 'running', 'not_exist')"""
    try:
        result = subprocess.run(['sc',
                                 'query',
                                 SERVICE_NAME],
                                capture_output=True,
                                text=True,
                                check=False,
                                encoding='utf-8',
                                errors='ignore')
        output = result.stdout.lower()

        if 'running' in output:
            return 'running'
        elif 'stopped' in output:
            return 'stopped'
        return 'not_exist'
    except Exception as e:
        return 'error'


def check_service_exists():
    try:
        output = subprocess.check_output(
            [os.path.join(SCRIPT_DIR, 'nssm.exe'), 'status', SERVICE_NAME], text=True)
        return 'SERVICE_RUNNING' in output or 'SERVICE_STOPPED' in output
    except subprocess.CalledProcessError:
        return False


# 增强型结果追踪
add_result = {
    'stage': 'precheck',
    'status': 'pending',
    'details': ['开始服务安装流程']
}


def service_exists():
    return get_service_status() != 'not_exist'


def add_service():
    """添加wstunnel服务"""
    try:
        if service_exists():
            print("服务已存在，无需重复添加")
            return False

        # 加载主配置文件
        config = load_config()

        # 从配置文件获取参数，如果不存在则使用默认值
        wstunnel_port = config.get('WSTUNNEL_PORT', '1081')
        server_restrict_port = config.get('SERVER_RESTRICT_PORT', '8443')
        server_ip = config.get('SERVER_IP', '192.210.206.52')
        server_port = config.get('SERVER_PORT', '443')

        # 检查端口是否被占用
        if is_port_in_use(int(wstunnel_port)):
            print(f"端口 {wstunnel_port} 已被占用，尝试终止占用进程")
            kill_process_by_name('wstunnel.exe')
            time.sleep(1)

        # 构建wstunnel启动命令 - 修正为UDP协议以支持WireGuard
        wstunnel_cmd = f"--log-lvl DEBUG client -L udp://127.0.0.1:{wstunnel_port}:127.0.0.1:{server_restrict_port} ws://{server_ip}:{server_port}"

        # 配置文件强制校验
        if not os.path.exists(os.path.join(SCRIPT_DIR, 'config.env')):
            open(os.path.join(SCRIPT_DIR, 'config.env'), 'a').close()

        # 服务存在性检查
        if check_service_exists():
            uninstall_wstunnel_service()

        # 初始化操作结果
        # 强化结果变量管理
        global add_result
        add_result = {'stage': 'precheck', 'status': 'pending', 'details': []}

        # 分阶段记录安装过程
        add_result['details'].append('开始服务安装流程')

        try:
            if not os.path.exists(WSTUNNEL_EXE):
                raise FileNotFoundError(f'找不到wstunnel可执行文件: {WSTUNNEL_EXE}')

            add_result['details'].append('校验可执行文件通过')
            subprocess.run([NSSM_EXE, "install", SERVICE_NAME,
                           WSTUNNEL_EXE], check=True, timeout=30)
            add_result['status'] = 'success'
        except subprocess.CalledProcessError as e:
            add_result.update(
                {'status': 'error', 'message': f'NSSM安装失败: {str(e)}'})
        except Exception as e:
            add_result.update({'status': 'critical',
                               'message': f'系统异常: {traceback.format_exc()}'})
        subprocess.run([NSSM_EXE, "set", SERVICE_NAME,
                       "AppDirectory", SCRIPT_DIR], check=True)
        subprocess.run([NSSM_EXE,
                        "set",
                        SERVICE_NAME,
                        "DisplayName",
                        "AUTOVPN wstunnel Service"],
                       check=True)
        subprocess.run([NSSM_EXE,
                        "set",
                        SERVICE_NAME,
                        "Description",
                        "AUTOVPN wstunnel Service for WireGuard traffic obfuscation"],
                       check=True)
        subprocess.run([NSSM_EXE, "set", SERVICE_NAME,
                       "AppParameters", wstunnel_cmd], check=True)
        return True
    except FileNotFoundError:
        print(f"错误: {NSSM_EXE} 或 {WSTUNNEL_EXE} 未找到。请确保路径正确。")
        return False
    except Exception as e:
        error_exception_str = str(e)
        safe_exception_str = error_exception_str.encode(
            'utf-8', 'ignore').decode('utf-8', 'replace')
        print(f"添加服务时发生意外错误: {safe_exception_str}")
        return False


def remove_service():
    try:
        result = subprocess.run([NSSM_EXE,
                                 'remove',
                                 SERVICE_NAME,
                                 'confirm'],
                                capture_output=True,
                                text=True,
                                encoding='utf-8',
                                errors='ignore')
        if result.returncode == 0:
            print("已移除wstunnel系统服务。")
            return True
        else:
            error_message = result.stderr
            if error_message:
                safe_error_message = error_message.encode(
                    'utf-8', 'ignore').decode('utf-8', 'replace')
            else:
                safe_error_message = "(无详细错误信息)"
            print(f"移除服务失败: {safe_error_message}")
            return False
    except Exception as e:
        error_exception_str = str(e)
        safe_exception_str = error_exception_str.encode(
            'utf-8', 'ignore').decode('utf-8', 'replace')
        print(f"移除服务时出错: {safe_exception_str}")
        return False


def main():
    if not os.path.exists(NSSM_EXE):
        print("nssm.exe不存在！")
        return
    print("正在配置wstunnel系统服务...\n")
    print("检测wstunnel服务状态...")
    exists = service_exists()
    if exists:
        print("wstunnel服务已存在。是否移除？(y/n)")
        if input().strip().lower() == 'y':
            remove_service()
    else:
        print("wstunnel服务不存在。是否添加？(y/n)")
        if input().strip().lower() == 'y':
            add_service()


if __name__ == "__main__":
    main()