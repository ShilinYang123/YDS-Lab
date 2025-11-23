#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
wstunnel 代理模式启动脚本
用于启动wstunnel SOCKS5/HTTP代理服务
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

# 脚本路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.env")
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")

# 导入公共函数
from Scripts.common.utils import load_config, is_process_running, kill_process_by_name, is_port_in_use

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            os.path.join(
                LOGS_DIR,
                'wstunnel_proxy.log'),
            encoding='utf-8')])
logger = logging.getLogger('wstunnel_proxy')

# PAC文件模板
PAC_TEMPLATE = """
function FindProxyForURL(url, host) {
    // 本地地址直连
    if (isPlainHostName(host) ||
        isInNet(host, "10.0.0.0", "255.0.0.0") ||
        isInNet(host, "172.16.0.0", "255.240.0.0") ||
        isInNet(host, "192.168.0.0", "255.255.0.0") ||
        isInNet(host, "127.0.0.0", "255.0.0.0"))
        return "DIRECT";

    // 国内常见域名直连
    if (re.search(r'\\.cn$', host) ||
        /^.*\\.baidu\\.com$/.test(host) ||
        /^.*\\.qq\\.com$/.test(host) ||
        /^.*\\.163\\.com$/.test(host) ||
        /^.*\\.sina\\.com\\.cn$/.test(host) ||
        /^.*\\.weibo\\.com$/.test(host) ||
        /^.*\\.taobao\\.com$/.test(host) ||
        /^.*\\.tmall\\.com$/.test(host) ||
        /^.*\\.jd\\.com$/.test(host) ||
        /^.*\\.alipay\\.com$/.test(host))
        return "DIRECT";

    // 默认代理
    return "__PROXY__";
}
"""

# 确保日志目录存在
os.makedirs(LOGS_DIR, exist_ok=True)


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


def generate_pac_file(config):
    """生成PAC文件"""
    pac_dir = config.get('PAC_DIR', SCRIPT_DIR)
    socks5_port = config.get('SOCKS5_PORT', '1081')
    http_port = config.get('HTTP_PORT', '8081')
    
    # 根据IPv6开关选择监听地址
    ipv6_enable = config.get('IPv6_ENABLE', 'false').lower() == 'true'
    if ipv6_enable:
        socks5_addr = config.get('IPv6_PROXY_ADDR', '[::1]')
        http_addr = config.get('IPv6_PROXY_ADDR', '[::1]')
    else:
        socks5_addr = '127.0.0.1'
        http_addr = '127.0.0.1'

    # 生成全局代理PAC（所有请求走代理）
    global_pac_path = os.path.join(pac_dir, "PAC_全部走代理_自动生成.pac")
    try:
        with open(global_pac_path, 'w', encoding='utf-8') as f:
            f.write("""function FindProxyForURL(url, host) {
    return "SOCKS5 __SOCKS5_ADDR__:__SOCKS5_PORT__; PROXY __HTTP_ADDR__:__HTTP_PORT__; DIRECT";
}""".replace("__SOCKS5_PORT__", socks5_port).replace("__HTTP_PORT__", http_port)
               .replace("__SOCKS5_ADDR__", socks5_addr).replace("__HTTP_ADDR__", http_addr))
        logger.info(f"已生成全局代理PAC文件: {global_pac_path}")
    except Exception as e:
        logger.error(f"生成全局代理PAC文件失败: {e}")

    # 生成智能分流PAC（国内直连，境外走代理）
    smart_pac_path = os.path.join(pac_dir, "PAC_智能分流_自动生成.pac")
    try:
        # 使用模板并替换代理设置
        pac_content = PAC_TEMPLATE.replace(
            "__PROXY__",
            f"SOCKS5 {socks5_addr}:{socks5_port}; PROXY {http_addr}:{http_port}; DIRECT")

        with open(smart_pac_path, 'w', encoding='utf-8') as f:
            f.write(pac_content)
        logger.info(f"已生成智能分流PAC文件: {smart_pac_path}")
    except Exception as e:
        logger.error(f"生成智能分流PAC文件失败: {e}")

    # 生成直连PAC（所有请求直连）
    direct_pac_path = os.path.join(pac_dir, "PAC_全部直连_自动生成.pac")
    try:
        with open(direct_pac_path, 'w', encoding='utf-8') as f:
            f.write("""function FindProxyForURL(url, host) {
    return "DIRECT";
}""")
        logger.info(f"已生成直连PAC文件: {direct_pac_path}")
    except Exception as e:
        logger.error(f"生成直连PAC文件失败: {e}")

    return global_pac_path, smart_pac_path, direct_pac_path


def create_browser_config_guide(config):
    """创建浏览器配置指南"""
    socks5_port = config.get('SOCKS5_PORT', '1081')
    http_port = config.get('HTTP_PORT', '8081')
    
    # 根据IPv6开关选择监听地址
    ipv6_enable = config.get('IPv6_ENABLE', 'false').lower() == 'true'
    if ipv6_enable:
        socks5_addr = config.get('IPv6_PROXY_ADDR', '[::1]')
        http_addr = config.get('IPv6_PROXY_ADDR', '[::1]')
    else:
        socks5_addr = '127.0.0.1'
        http_addr = '127.0.0.1'
    
    guide_path = os.path.join(SCRIPT_DIR, "浏览器代理设置指南.md")

    try:
        with open(guide_path, 'w', encoding='utf-8') as f:
            f.write(f"""# 浏览器代理设置指南

## 代理信息

- SOCKS5代理: {socks5_addr}:{socks5_port}
- HTTP代理: {http_addr}:{http_port}
- IPv6模式: {'启用' if ipv6_enable else '禁用'}
- PAC文件路径: (本地生成的PAC文件位置)

## Google Chrome 设置方法

1. 打开Chrome，点击右上角的菜单按钮(⋮)，选择"设置"
2. 滚动到页面底部，点击"高级"
3. 在"系统"部分，点击"打开代理设置"
4. 在Windows的"Internet属性"窗口中，选择"连接"选项卡，然后点击"局域网设置"
5. 有两种设置方式:
   - **使用PAC自动配置**:
     - 勾选"使用自动配置脚本"
     - 在"地址"框中输入PAC文件的本地路径，如: file:///S:/YDS-Lab/03-dev/006-AUTOVPN/VPN-Sel/Scripts/wstunnel/PAC_智能分流_自动生成.pac
   - **手动设置代理**:
     - 勾选"为LAN使用代理服务器"
     - 点击"高级"
     - 在"SOCKS"字段输入: 127.0.0.1:{socks5_port}
     - 或在"HTTP"字段输入: 127.0.0.1:{http_port}
6. 点击"确定"应用设置

## Firefox 设置方法

1. 打开Firefox，点击右上角的菜单按钮(☰)，选择"设置"
2. 滚动到页面底部，在"网络设置"部分点击"设置..."
3. 有三种设置方式:
   - **使用PAC自动配置**:
     - 选择"自动代理配置URL"
     - 输入PAC文件的本地路径，如: file:///S:/YDS-Lab/03-dev/006-AUTOVPN/VPN-Sel/Scripts/wstunnel/PAC_智能分流_自动生成.pac
   - **手动配置代理**:
     - 选择"手动配置代理"
     - SOCKS主机: 127.0.0.1，端口: {socks5_port}，选择"SOCKS v5"
     - 或HTTP代理: 127.0.0.1，端口: {http_port}
   - **系统代理设置**: 选择"使用系统代理设置"
4. 点击"确定"应用设置

## Microsoft Edge 设置方法

1. 打开Edge，点击右上角的菜单按钮(…)，选择"设置"
2. 在左侧导航栏选择"系统和性能"
3. 在"代理"部分，点击"打开计算机的代理设置"
4. 按照Chrome的设置步骤4-6进行设置

## 系统全局代理设置 (Windows)

1. 打开Windows设置
2. 点击"网络和Internet"
3. 点击"代理"
4. 有两种设置方式:
   - **使用PAC自动配置**:
     - 在"自动代理设置"部分，打开"使用设置脚本"
     - 输入脚本地址: file:///S:/YDS-Lab/03-dev/006-AUTOVPN/VPN-Sel/Scripts/wstunnel/PAC_智能分流_自动生成.pac
   - **手动设置代理**:
     - 在"手动代理设置"部分，打开"使用代理服务器"
     - 输入地址: 127.0.0.1
     - 输入端口: {http_port} (HTTP代理)或 {socks5_port} (SOCKS5代理)
5. 点击"保存"应用设置

## 推荐的浏览器扩展

对于更灵活的代理控制，建议安装以下浏览器扩展之一:

1. **SwitchyOmega**: 最强大的代理管理扩展，支持多情景模式和自动切换
   - [Chrome版](https://chrome.google.com/webstore/detail/proxy-switchyomega/padekgcemlokbadohgkifijomclgjgif)
   - [Firefox版](https://addons.mozilla.org/en-US/firefox/addon/switchyomega/)

2. **Proxy SwitchySharp**: SwitchyOmega的前身，功能稍简单但易用
   - [Chrome版](https://chrome.google.com/webstore/detail/proxy-switchysharp/dpplabbmogkhghncfbfdeeokoefdjegm)

## SwitchyOmega 设置指南

1. 安装SwitchyOmega扩展
2. 点击扩展图标，选择"选项"
3. 创建新情景模式:
   - **直接连接**: 无需代理，直接连接
   - **SOCKS5代理**: 设置SOCKS代理 127.0.0.1:{socks5_port}
   - **HTTP代理**: 设置HTTP代理 127.0.0.1:{http_port}
   - **自动切换**: 创建规则，国内网站直连，国外网站使用代理
4. 可以导入在线规则列表实现自动分流

## 问题排查

如果遇到连接问题，请检查:

1. 确认wstunnel服务正在运行
2. 确认代理端口正确(SOCKS5: {socks5_port}, HTTP: {http_port})
3. 尝试不同的代理类型(SOCKS5/HTTP)
4. 检查PAC文件是否正确加载
5. 尝试禁用其他可能冲突的代理扩展
6. 查看浏览器开发者工具中的网络请求，检查是否通过代理
""")
        logger.info(f"已创建浏览器代理设置指南: {guide_path}")
        return guide_path
    except Exception as e:
        logger.error(f"创建浏览器代理设置指南失败: {e}")
        return None


def start_wstunnel_proxy(config):
    """启动wstunnel SOCKS5/HTTP代理"""
    server_ip = config.get('SERVER_IP', '192.210.206.52')
    # SOCKS5代理端口
    socks5_port = int(config.get('SOCKS5_PORT', '1082'))
    # HTTP代理端口
    http_port = int(config.get('HTTP_PORT', '8081'))
    server_port = int(config.get('SERVER_PORT', '443'))
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
    ipv6_enable = config.get('IPv6_ENABLE', 'false').lower() == 'true'
    if ipv6_enable:
        socks5_listen_addr = config.get('IPv6_PROXY_ADDR', '[::1]')
        http_listen_addr = config.get('IPv6_PROXY_ADDR', '[::1]')
    else:
        socks5_listen_addr = '127.0.0.1'
        http_listen_addr = '127.0.0.1'

    # 代理模式使用SOCKS5和HTTP代理
    cmd = [
        wstunnel_exe,
        "client",
        f"--http-upgrade-path-prefix={prefix}",
        "-L",
        f"socks5://{socks5_listen_addr}:{socks5_port}?login={user}&password={password}",
        "-L",
        f"http://{http_listen_addr}:{http_port}?login={user}&password={password}",
        f"ws://{server_ip}:{server_port}"
    ]

    # 启动wstunnel进程
    try:
        logger.info(f"启动wstunnel代理命令: {' '.join(cmd)}")

        log_file = os.path.join(
            LOGS_DIR, f"wstunnel_proxy_{
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
            logger.info(f"SOCKS5代理: {socks5_listen_addr}:{socks5_port}")
            logger.info(f"HTTP代理: {http_listen_addr}:{http_port}")
            logger.info(f"IPv6模式: {'启用' if ipv6_enable else '禁用'}")

            # 如果端口发生了变化，更新配置
            if socks5_port != int(
                config.get(
                    'SOCKS5_PORT',
                    '1081')) or http_port != int(
                config.get(
                    'HTTP_PORT',
                    '8081')):
                logger.info("端口发生变化，更新config.env")
                update_config_ports(config, socks5_port, http_port)

            # 生成PAC文件
            generate_pac_file(config)

            # 创建浏览器配置指南
            create_browser_config_guide(config)

            return True
        else:
            logger.error(f"wstunnel进程已退出，状态码: {process.returncode}")
            return False
    except Exception as e:
        logger.error(f"启动wstunnel失败: {e}")
        return False


def update_config_ports(config, socks5_port, http_port):
    """更新config.env中的端口"""
    try:
        config_content = []
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip().startswith('SOCKS5_PORT='):
                    line = f"SOCKS5_PORT={socks5_port}\n"
                elif line.strip().startswith('HTTP_PORT='):
                    line = f"HTTP_PORT={http_port}\n"
                config_content.append(line)

        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            f.writelines(config_content)

        logger.info(
            f"已更新config.env: SOCKS5_PORT={socks5_port}, HTTP_PORT={http_port}")
    except Exception as e:
        logger.error(f"更新config.env失败: {e}")


def display_proxy_info(config, socks5_port, http_port):
    """显示代理信息"""
    # 根据IPv6开关选择监听地址
    ipv6_enable = config.get('IPv6_ENABLE', 'false').lower() == 'true'
    if ipv6_enable:
        socks5_addr = config.get('IPv6_PROXY_ADDR', '[::1]')
        http_addr = config.get('IPv6_PROXY_ADDR', '[::1]')
    else:
        socks5_addr = '127.0.0.1'
        http_addr = '127.0.0.1'
    
    print("\n" + "=" * 60)
    print("SOCKS5代理已启动：")
    print(f"  地址: {socks5_addr}:{socks5_port}")
    print(f"  用户名: {config.get('USER', 'youruser')}")
    print(f"  密码: {config.get('PASS', 'yourpass')}")
    print("\nHTTP代理已启动：")
    print(f"  地址: {http_addr}:{http_port}")
    print(f"  用户名: {config.get('USER', 'youruser')}")
    print(f"  密码: {config.get('PASS', 'yourpass')}")
    print(f"\nIPv6模式: {'启用' if ipv6_enable else '禁用'}")
    print("\nPAC文件已生成：")
    print(
        f"  全局代理: {
            os.path.join(
                config.get(
                    'PAC_DIR',
                    SCRIPT_DIR),
                'PAC_全部走代理_自动生成.pac')}")
    print(
        f"  智能分流: {
            os.path.join(
                config.get(
                    'PAC_DIR',
                    SCRIPT_DIR),
                'PAC_智能分流_自动生成.pac')}")
    print(
        f"  全部直连: {
            os.path.join(
                config.get(
                    'PAC_DIR',
                    SCRIPT_DIR),
                'PAC_全部直连_自动生成.pac')}")
    print("\n浏览器配置指南：")
    print(f"  {os.path.join(SCRIPT_DIR, '浏览器代理设置指南.md')}")
    print("=" * 60)


def test_proxy_connection(socks5_port, http_port):
    """测试代理连接"""
    # 这里可以添加对代理的连接测试
    # 例如使用requests库通过代理发送请求
    # 但这需要额外的依赖，所以这里只做端口检查

    socks5_active = is_port_in_use(socks5_port)
    http_active = is_port_in_use(http_port)

    if socks5_active and http_active:
        logger.info(f"代理端口测试通过: SOCKS5({socks5_port})和HTTP({http_port})端口均已监听")
        return True
    else:
        if not socks5_active:
            logger.warning(f"SOCKS5端口 {socks5_port} 未在监听")
        if not http_active:
            logger.warning(f"HTTP端口 {http_port} 未在监听")
        return False


def main():
    print("=" * 60)
    print("AUTOVPN - wstunnel 代理模式启动工具")
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
    success = start_wstunnel_proxy(config)

    if success:
        socks5_port = int(config.get('SOCKS5_PORT', '1081'))
        http_port = int(config.get('HTTP_PORT', '8081'))
        display_proxy_info(config, socks5_port, http_port)

        # 测试代理连接
        if test_proxy_connection(socks5_port, http_port):
            print("\n代理连接测试通过!")
        else:
            print("\n警告: 代理连接测试失败，但服务已启动。请检查日志了解详情。")
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