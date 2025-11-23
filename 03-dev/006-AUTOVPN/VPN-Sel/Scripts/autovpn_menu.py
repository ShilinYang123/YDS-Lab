#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutoVPN 主菜单脚本
提供统一的VPN管理界面
"""

import os
import sys
import subprocess
import time
import json
import platform
import psutil
import shutil
import re
import tempfile
import socket
from pathlib import Path

# 最近一次服务状态的纯文本，用于控制台标题与输入提示
LAST_STATUS_PLAIN = ""

# 获取脚本目录和项目根目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.env")

# 添加脚本目录到Python路径
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

def test_server_connectivity_menu(config):
    """测试服务器连通性菜单"""
    server_ip = config.get('SERVER_IP', '192.210.206.52')
    server_port = int(config.get('SERVER_PORT', '443'))

    print(f"\n正在测试服务器连通性: {server_ip}:{server_port}")

    # 使用telnet测试端口连通性
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((server_ip, server_port))
        sock.close()

        if result == 0:
            print(f"[√] 服务器 {server_ip}:{server_port} 连通正常")
        else:
            print(f"[×] 服务器 {server_ip}:{server_port} 连接失败")
    except Exception as e:
        print(f"[×] 测试连接时发生错误: {e}")

    # 使用ping测试网络延迟
    try:
        if platform.system() == "Windows":
            ping_cmd = f"ping -n 4 {server_ip}"
        else:
            ping_cmd = f"ping -c 4 {server_ip}"

        result = subprocess.run(
            ping_cmd,
            shell=True,
            capture_output=True,
            text=True)
        if result.returncode == 0:
            print(f"[√] Ping {server_ip} 成功")
            # 提取延迟信息
            if "平均" in result.stdout:
                lines = result.stdout.split('\n')
                for line in lines:
                    if "平均" in line:
                        print(f"    {line.strip()}")
        else:
            print(f"[×] Ping {server_ip} 失败")
    except Exception as e:
        print(f"[×] Ping测试时发生错误: {e}")

def load_config():
    """加载config.env配置文件"""
    config = {}
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
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
        print(f"[警告] 配置文件不存在: {CONFIG_PATH}")
        return {}
    except Exception as e:
        print(f"[错误] 读取配置文件失败: {e}")
        return {}

def clear_screen():
    """清屏函数"""
    os.system('cls' if os.name == 'nt' else 'clear')

def is_process_running(process_name):
    """检查进程是否正在运行"""
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] and process_name.lower() in proc.info['name'].lower():
                return True
        return False
    except Exception:
        return False

def kill_process_by_name(process_name):
    """根据进程名终止进程"""
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] and process_name.lower() in proc.info['name'].lower():
                proc.terminate()
                print(f"已终止进程: {proc.info['name']} (PID: {proc.info['pid']})")
    except Exception as e:
        print(f"终止进程时发生错误: {e}")

def check_and_display_service_status():
    """检查并显示服务状态"""
    global LAST_STATUS_PLAIN
    try:
        # 重新加载配置以获取最新端口信息
        current_config = load_config()  # 重新加载最新配置

        socks5_port = int(current_config.get('SOCKS5_PORT', '1081'))
        http_port = int(current_config.get('HTTP_PORT', '8081'))

        # 检查各种服务状态
        wstunnel_running = is_process_running('wstunnel.exe')
        privoxy_running = is_process_running('privoxy.exe')

        # 检查端口占用情况
        def is_port_in_use(port):
            try:
                for conn in psutil.net_connections():
                    try:
                        if conn.laddr and conn.laddr.port == port:
                            return True
                    except (AttributeError, TypeError):
                        pass
                return False
            except Exception:
                return False

        socks5_port_used = is_port_in_use(socks5_port)
        http_port_used = is_port_in_use(http_port)

        # 显示状态 - 使用绿色圆点表示运行，白色圆点表示未运行
        green_check = "\033[92m●\033[0m"  # 绿色圆点(有色)
        white_cross = "\033[97m●\033[0m"   # 白色圆点(有色)
        dot_ok = "●"  # 纯文本圆点

        wstunnel_col = f"{green_check if wstunnel_running else white_cross} wstunnel进程({current_config.get('WSTUNNEL_PORT', '1081')}/UDP)"
        socks5_col = f"{green_check if socks5_port_used else white_cross} SOCKS5代理({socks5_port})"
        http_col = f"{green_check if http_port_used else white_cross} HTTP代理({http_port})"
        privoxy_col = f"{green_check if privoxy_running else white_cross} Privoxy进程"
        
        # 纯文本（不带ANSI），用于窗口标题与输入提示
        wstunnel_plain = f"{dot_ok if wstunnel_running else '○'}wstunnel({current_config.get('WSTUNNEL_PORT', '1081')})"
        socks5_plain = f"{dot_ok if socks5_port_used else '○'}SOCKS5({socks5_port})"
        http_plain = f"{dot_ok if http_port_used else '○'}HTTP({http_port})"
        privoxy_plain = f"{dot_ok if privoxy_running else '○'}Privoxy"
        LAST_STATUS_PLAIN = f"{wstunnel_plain} · {socks5_plain} · {http_plain} · {privoxy_plain}"
        
        # 获取IPv6状态
        ipv6_enabled = current_config.get('IPv6_ENABLE', 'false').lower() == 'true'
        ipv6_status = f"\033[92m开启\033[0m" if ipv6_enabled else f"\033[97m关闭\033[0m"
        ipv6_plain = "开启" if ipv6_enabled else "关闭"
        
        # 打印彩色服务状态信息（包含IPv6状态）
        print("服务状态: " + wstunnel_col + " " + socks5_col + " " + http_col + " " + privoxy_col)
        print("IPv6状态: " + ipv6_status)

        # 更新Windows控制台标题，保持随时可见
        if os.name == 'nt':
            try:
                os.system(f"title AUTOVPN 管理面板 - {LAST_STATUS_PLAIN} - IPv6:{ipv6_plain}")
            except Exception:
                pass
    except Exception as e:
        # 出错时也不要影响主菜单渲染
        print(f"服务状态: [获取失败] {e}")
    finally:
        # 强制刷新，确保立即显示
        sys.stdout.flush()

def check_network_status(config):
    """检查网络状态"""
    print("\n" + "=" * 50)
    print("           网络状态检查")
    print("=" * 50)

    # 检查基本网络连接
    print("\n1. 检查基本网络连接...")
    try:
        result = subprocess.run(['ping', '-n', '1', '8.8.8.8'],
                                capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("[√] 基本网络连接正常")
        else:
            print("[×] 基本网络连接异常")
    except Exception as e:
        print(f"[×] 网络连接检查失败: {e}")

    # 检查代理端口
    print("\n2. 检查代理端口状态...")
    socks5_port = int(config.get('SOCKS5_PORT', '1081'))
    http_port = int(config.get('HTTP_PORT', '8081'))

    try:
        # 检查SOCKS5端口
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(3)
            result = sock.connect_ex(('127.0.0.1', socks5_port))
            if result == 0:
                print(f"[√] SOCKS5代理端口 {socks5_port} 已开启")
            else:
                print(f"[×] SOCKS5代理端口 {socks5_port} 未开启")
    except Exception as e:
        print(f"[×] SOCKS5端口检查失败: {e}")

    try:
        # 检查HTTP端口
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(3)
            result = sock.connect_ex(('127.0.0.1', http_port))
            if result == 0:
                print(f"[√] HTTP代理端口 {http_port} 已开启")
            else:
                print(f"[×] HTTP代理端口 {http_port} 未开启")
    except Exception as e:
        print(f"[×] HTTP端口检查失败: {e}")
    
    # 等待用户查看结果
    input("\n按Enter键继续...")

def run_wireguard_test():
    """测试WireGuard连接"""
    print("\n正在测试WireGuard连接...")
    try:
        # 检查是否能访问Google
        result = subprocess.run(['ping', '-n', '1', '8.8.8.8'],
                                capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("[√] WireGuard连接正常")
        else:
            print("[×] WireGuard连接异常")
    except Exception as e:
        print(f"[×] WireGuard测试失败: {e}")
    
    # 等待用户查看结果
    input("\n按Enter键继续...")

def run_proxy_test():
    """测试代理连接"""
    print("\n正在测试代理连接...")
    try:
        # 使用curl测试代理连接
        curl_cmd = "curl -x socks5://127.0.0.1:1081 http://www.google.com --connect-timeout 10 -m 15"
        result = subprocess.run(curl_cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("[√] 代理连接正常")
        else:
            print("[×] 代理连接异常")
    except Exception as e:
        print(f"[×] 代理测试失败: {e}")
    
    # 等待用户查看结果
    input("\n按Enter键继续...")

def edit_config():
    """编辑配置文件"""
    print("\n正在编辑配置文件...")
    try:
        if platform.system() == "Windows":
            subprocess.run(['notepad', CONFIG_PATH])
        else:
            subprocess.run(['nano', CONFIG_PATH])
        print("配置文件编辑完成")
    except Exception as e:
        print(f"[错误] 编辑配置文件失败: {e}")
    
    # 等待用户查看结果
    input("\n按Enter键继续...")

def run_sync_config():
    """同步配置到WireGuard"""
    print("\n正在同步配置到WireGuard...")
    try:
        sync_script = os.path.join(SCRIPT_DIR, "sync_config.py")
        if os.path.exists(sync_script):
            result = subprocess.run([sys.executable, sync_script], cwd=SCRIPT_DIR)
            if result.returncode == 0:
                print("✅ 配置同步成功")
            else:
                print("[×] 配置同步失败")
        else:
            print(f"[错误] 同步脚本不存在: {sync_script}")
    except Exception as e:
        print(f"[错误] 同步配置失败: {e}")
    
    # 等待用户查看结果
    input("\n按Enter键继续...")

def check_and_install_wireguard():
    """检测并安装WireGuard"""
    print("\n正在检测WireGuard安装状态...")
    
    # 检查WireGuard是否已安装
    wireguard_installed = False
    
    # 方法1: 检查程序文件夹
    program_files = os.environ.get('ProgramFiles', 'C:\\Program Files')
    wireguard_path = os.path.join(program_files, 'WireGuard')
    if os.path.exists(wireguard_path):
        wireguard_installed = True
    
    # 方法2: 检查WireGuard服务
    if not wireguard_installed:
        try:
            result = subprocess.run(
                ['sc', 'query', 'WireGuardManager'], 
                capture_output=True, 
                text=True
            )
            if result.returncode == 0 and 'RUNNING' in result.stdout:
                wireguard_installed = True
        except Exception:
            pass
    
    if wireguard_installed:
        print("✅ WireGuard已安装在系统中")
    else:
        print("❌ 未检测到WireGuard，准备安装...")
        
        # 安装WireGuard
        installer_path = os.path.join(PROJECT_ROOT, "Installers", "wireguard-amd64.msi")
        if os.path.exists(installer_path):
            print(f"找到安装包: {installer_path}")
            print("正在启动安装程序...")
            try:
                # 使用msiexec安装
                result = subprocess.run(
                    ['msiexec', '/i', installer_path, '/quiet', '/norestart'], 
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    print("✅ WireGuard安装成功！")
                else:
                    print(f"❌ 安装失败，错误代码: {result.returncode}")
                    print("请手动安装WireGuard。")
            except Exception as e:
                print(f"❌ 安装过程中发生错误: {e}")
                print("请手动安装WireGuard。")
        else:
            print(f"❌ 未找到安装包: {installer_path}")
            print("请手动下载并安装WireGuard。")
    
    # 等待用户查看结果
    input("\n按Enter键继续...")

def view_hosts_file():
    """查看hosts文件内容"""
    print("\n正在查看hosts文件内容...")
    try:
        hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
        if os.path.exists(hosts_path):
            with open(hosts_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print("\n" + "=" * 60)
                print("                    HOSTS文件内容")
                print("=" * 60)
                print(content)
        else:
            print(f"[错误] hosts文件不存在: {hosts_path}")
    except Exception as e:
        print(f"[错误] 读取hosts文件失败: {e}")
    
    # 等待用户查看结果
    input("\n按Enter键继续...")

def view_wireguard_config():
    """查看WireGuard配置文件"""
    print("\n正在查看WireGuard配置文件...")
    try:
        # 从config.env获取WireGuard配置文件路径
        config = load_config()
        wg_conf_path = config.get('WG_CONF_PATH')
        
        if wg_conf_path and os.path.exists(wg_conf_path):
            with open(wg_conf_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print("\n" + "=" * 60)
                print(f"                WireGuard配置文件 ({os.path.basename(wg_conf_path)})")
                print("=" * 60)
                print(content)
        else:
            print(f"[错误] WireGuard配置文件不存在: {wg_conf_path}")
    except Exception as e:
        print(f"[错误] 读取WireGuard配置文件失败: {e}")
    
    # 等待用户查看结果
    input("\n按Enter键继续...")

def show_help():
    """显示帮助信息"""
    clear_screen()
    print("\n" + "=" * 60)
    print("                    AUTOVPN 使用帮助")
    print("=" * 60)
    print(" 1. 启动wstunnel  - 启动wstunnel服务")
    print(" 2. WireGuard模式 - 启动WireGuard模式(UDP转发)")
    print(" 3. 代理模式     - 启动代理模式(SOCKS5/HTTP)")
    print(" 4. 综合模式     - 同时支持WireGuard和代理")
    print(" 5. 添加域名     - 手动添加需要解析的域名")
    print(" 6. 域名解析     - 解析域名列表中的所有域名")
    print(" 7. 更新Hosts    - 将解析结果更新到系统Hosts文件")
    print(" 8. 清空Hosts    - 清空Hosts文件中的AUTOVPN条目")
    print(" 9. 网络测试     - 测试网络连通性和代理状态")
    print("10. WireGuard测试 - 测试WireGuard连接")
    print("11. 代理测试     - 测试SOCKS5和HTTP代理")
    print("12. 编辑配置     - 编辑服务器连接配置")
    print("13. 同步配置     - 同步WireGuard配置文件")
    print("14. 生成报告     - 生成系统和服务状态报告")
    print("15. 查看hosts文件 - 显示当前hosts文件内容")
    print("16. 查看wireguard配置文件 - 显示WireGuard配置文件")
    print("17. 单域名处理   - 添加并解析单个域名")
    print("\n推荐域名列表:")
    print(" - AI编程常用: github.com, huggingface.co, google.com")
    print(" - 海外电商: amazon.com, ebay.com, aliexpress.com")
    print("=" * 60)
    input("\n按Enter键继续...")

def stop_all_services():
    """停止所有服务"""
    print("\n正在停止所有服务...")
    try:
        # 停止wstunnel
        kill_process_by_name('wstunnel.exe')
        # 停止privoxy
        kill_process_by_name('privoxy.exe')
        print("✅ 所有服务已停止")
    except Exception as e:
        print(f"[错误] 停止服务失败: {e}")

def run_wireguard_mode(config):
    """运行WireGuard模式"""
    print("\n启动WireGuard模式...")
    try:
        wg_script = os.path.join(SCRIPT_DIR, "run_wireguard.py")
        if os.path.exists(wg_script):
            subprocess.Popen(
                [sys.executable, wg_script],
                cwd=SCRIPT_DIR,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            time.sleep(2)  # 等待服务启动
            print("✅ WireGuard模式已启动")
        else:
            print(f"[错误] WireGuard脚本不存在: {wg_script}")
    except Exception as e:
        print(f"[错误] 启动WireGuard模式失败: {e}")
    input("按Enter键继续...")

def run_proxy_mode(config):
    """运行代理模式"""
    print("\n启动代理模式...")
    try:
        proxy_script = os.path.join(SCRIPT_DIR, "run_proxy.py")
        if os.path.exists(proxy_script):
            subprocess.Popen(
                [sys.executable, proxy_script],
                cwd=SCRIPT_DIR,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            time.sleep(2)  # 等待服务启动
            print("✅ 代理模式已启动")
        else:
            print(f"[错误] 代理脚本不存在: {proxy_script}")
    except Exception as e:
        print(f"[错误] 启动代理模式失败: {e}")
    input("按Enter键继续...")

def run_combined_mode(config):
    """运行综合模式"""
    print("\n启动综合模式...")
    try:
        # 使用综合模式脚本
        combined_script = os.path.join(SCRIPT_DIR, "run_combined.py")
        if os.path.exists(combined_script):
            subprocess.Popen(
                [sys.executable, combined_script],
                cwd=SCRIPT_DIR,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            time.sleep(2)  # 等待服务启动
            print("✅ 综合模式已启动")
        else:
            print(f"[错误] 综合模式脚本不存在: {combined_script}")
            
            # 如果综合模式脚本不存在，尝试分别启动WireGuard和代理
            print("尝试分别启动WireGuard和代理模式...")
            # 启动WireGuard
            try:
                wg_script = os.path.join(SCRIPT_DIR, "run_wireguard.py")
                if os.path.exists(wg_script):
                    subprocess.Popen(
                        [sys.executable, wg_script],
                        cwd=SCRIPT_DIR,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    time.sleep(2)  # 等待服务启动
                    print("✅ WireGuard模式已启动")
                else:
                    print(f"[错误] WireGuard脚本不存在: {wg_script}")
            except Exception as e:
                print(f"[错误] 启动WireGuard模式失败: {e}")
            
            # 启动代理
            try:
                proxy_script = os.path.join(SCRIPT_DIR, "run_proxy.py")
                if os.path.exists(proxy_script):
                    subprocess.Popen(
                        [sys.executable, proxy_script],
                        cwd=SCRIPT_DIR,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    time.sleep(2)  # 等待服务启动
                    print("✅ 代理模式已启动")
                else:
                    print(f"[错误] 代理脚本不存在: {proxy_script}")
            except Exception as e:
                print(f"[错误] 启动代理模式失败: {e}")
    except Exception as e:
        print(f"[错误] 启动综合模式失败: {e}")
    input("按Enter键继续...")

def process_pasted_domains(domain_input, config):
    """处理用户粘贴的域名列表"""
    print("\n正在处理粘贴的域名列表...")
    
    if domain_input:
        # 处理粘贴的多行或多域名输入
        # 支持换行符和空格分隔的域名
        import re
        import sys
        import subprocess
        import os
        
        # 如果输入包含换行符，先处理多行输入
        if '\n' in domain_input:
            lines = domain_input.split('\n')
            # 合并所有行并用空格分隔，确保每行都被正确处理
            domain_input = ' '.join([line.strip() for line in lines if line.strip()])
            print(f"检测到多行输入，已合并处理 {len(lines)} 行内容")
        
        # 按空格分割域名
        raw_domains = domain_input.split()
        
        processed_domains = []
        for domain in raw_domains:
            if not domain:
                continue
            # 去掉http://和https://前缀
            domain = domain.replace('http://', '').replace('https://', '')
            # 去掉末尾的斜杠和路径
            domain = domain.split('/')[0]
            # 去掉反斜杠（修复通配符域名格式）
            domain = domain.replace('\\', '')
            # 去掉查询参数
            domain = domain.split('?')[0]
            # 去掉锚点
            domain = domain.split('#')[0]
            # 去掉端口号
            domain = domain.split(':')[0]
            
            if domain and domain not in processed_domains:
                processed_domains.append(domain)

        if not processed_domains:
            print("未找到有效的域名格式")
            return

        # 读取现有域名列表，避免重复
        domain_file_path = os.path.join(
            PROJECT_ROOT, "routes", "需要获取IP的域名列表.txt")
        existing_domains = set()

        try:
            with open(domain_file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        existing_domains.add(line)
        except FileNotFoundError:
            pass

        # 添加新域名
        new_domains = []
        for domain in processed_domains:
            if domain not in existing_domains:
                new_domains.append(domain)

        if new_domains:
            # 确保目录存在
            os.makedirs(os.path.dirname(domain_file_path), exist_ok=True)
            
            with open(domain_file_path, "a", encoding="utf-8") as f:
                for domain in new_domains:
                    f.write(f"\n{domain}")
            print(f"✅ 已添加 {len(new_domains)} 个新域名到列表")

            # 专业级域名文件整理
            print("正在进行专业级域名文件整理...")
            try:
                with open(domain_file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                # 高级域名清理和去重
                clean_domains = set()
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    # 处理行内注释（去掉#及其后面的内容）
                    if '#' in line:
                        line = line.split('#')[0].strip()

                    # 处理多种分隔符：空格、制表符、逗号、分号
                    import re
                    domains_in_line = re.split(r'[\s,;]+', line)

                    for domain in domains_in_line:
                        if not domain:
                            continue

                        # 全面清理域名格式
                        domain = domain.strip()
                        # 去掉协议前缀
                        domain = re.sub(r'^https?://', '', domain)
                        # 去掉反斜杠（通配符修复）
                        domain = domain.replace('\\', '')
                        # 去掉路径部分（保留域名主体）
                        domain = domain.split('/')[0]
                        # 去掉端口号
                        domain = domain.split(':')[0]
                        # 去掉查询参数
                        domain = domain.split('?')[0]
                        # 去掉锚点
                        domain = domain.split('#')[0]
                        # 去掉多余的点
                        domain = domain.strip('.')

                        # 验证域名格式（基本验证）
                        if domain and (
                                '.' in domain or domain.startswith('*')):
                            # 确保通配符格式正确
                            if domain.startswith(
                                    '*') and not domain.startswith('*.'):
                                domain = '*.' + domain[1:]

                            clean_domains.add(domain.lower())

                # 重写文件，按字母顺序排序
                with open(domain_file_path, "w", encoding="utf-8") as f:
                    f.write("# 需要获取IP的域名列表\n")
                    f.write("# 每行一个域名，支持通配符格式（如 *.example.com）\n")
                    f.write("# 自动清理：去除协议、路径、端口、注释等\n\n")

                    # 分类排序：通配符域名在前，普通域名在后
                    wildcard_domains = sorted(
                        [d for d in clean_domains if d.startswith('*')])
                    normal_domains = sorted(
                        [d for d in clean_domains if not d.startswith('*')])

                    for domain in wildcard_domains + normal_domains:
                        f.write(f"{domain}\n")

                print(f"✅ 域名文件整理完成，共处理 {len(clean_domains)} 个有效域名")
                print("   - 已去除行内注释")
                print("   - 已分割多域名行")
                print("   - 已清理URL路径和参数")
                print("   - 已修复通配符格式")
                print("   - 已按类型和字母顺序排序")

                # 提示用户可以进行域名解析
                print("\n✅ 域名已添加到列表，请选择菜单选项6来解析域名IP地址")
                print("   或选择菜单选项16来添加单个域名并完成全流程")

            except Exception as e:
                print(f"整理域名文件时出错: {e}")
        else:
            print("没有新域名需要添加")
    else:
        print("未输入域名")

def resolve_single_domain_ip(domain):
    """通过境外服务器解析单个域名获取IP地址"""
    try:
        # 复用现有的远程解析脚本
        resolve_script = os.path.join(SCRIPT_DIR, "resolve_ip_remote.py")
        if not os.path.exists(resolve_script):
            print(f"[错误] 解析脚本不存在: {resolve_script}")
            return None
            
        # 定义文件路径
        domain_file_path = os.path.join(PROJECT_ROOT, "routes", "需要获取IP的域名列表.txt")
        backup_domain_file_path = os.path.join(PROJECT_ROOT, "routes", "需要获取IP的域名列表_backup.txt")
        
        # 1. 备份现有的域名列表文件
        existing_domains = []
        if os.path.exists(domain_file_path):
            with open(domain_file_path, 'r', encoding='utf-8') as f:
                existing_domains = [line.strip() for line in f.readlines() if line.strip() and not line.startswith('#')]
            # 创建备份
            shutil.copy2(domain_file_path, backup_domain_file_path)
        
        # 2. 将该单个域名覆盖整个域名列表文件的内容
        with open(domain_file_path, 'w', encoding='utf-8') as f:
            f.write("# 需要获取IP的域名列表\n")
            f.write("# 每行一个域名，支持通配符格式（如 *.example.com）\n")
            f.write("# 自动清理：去除协议、路径、端口、注释等\n\n")
            f.write(f"{domain}\n")
            
        # 执行远程解析
        result = subprocess.run(
            [sys.executable, resolve_script],
            cwd=SCRIPT_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )
        
        # 3. 解析完成后，恢复备份的域名列表文件
        ip = None
        if os.path.exists(backup_domain_file_path):
            shutil.move(backup_domain_file_path, domain_file_path)
        else:
            # 如果没有备份文件，创建一个新的空列表文件
            with open(domain_file_path, 'w', encoding='utf-8') as f:
                f.write("# 需要获取IP的域名列表\n")
                f.write("# 每行一个域名，支持通配符格式（如 *.example.com）\n")
                f.write("# 自动清理：去除协议、路径、端口、注释等\n\n")
        
        # 4. 将该单个域名添加到列表末尾（如果它不在列表中）
        if domain not in existing_domains:
            with open(domain_file_path, 'a', encoding='utf-8') as f:
                f.write(f"{domain}\n")
        
        # 读取解析结果
        temp_ip_file = os.path.join(PROJECT_ROOT, "routes", "常用境外IP.txt")
        if os.path.exists(temp_ip_file):
            with open(temp_ip_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines:
                    if domain in line:
                        ip = line.split()[0]
                        return ip
                        
        return ip
    except Exception as e:
        print(f"[错误] 域名解析失败: {e}")
        # 确保即使出错也恢复域名列表
        domain_file_path = os.path.join(PROJECT_ROOT, "routes", "需要获取IP的域名列表.txt")
        backup_domain_file_path = os.path.join(PROJECT_ROOT, "routes", "需要获取IP的域名列表_backup.txt")
        if os.path.exists(backup_domain_file_path):
            shutil.move(backup_domain_file_path, domain_file_path)
        elif os.path.exists(domain_file_path):
            # 如果没有备份文件，创建一个新的空列表文件
            with open(domain_file_path, 'w', encoding='utf-8') as f:
                f.write("# 需要获取IP的域名列表\n")
                f.write("# 每行一个域名，支持通配符格式（如 *.example.com）\n")
                f.write("# 自动清理：去除协议、路径、端口、注释等\n\n")
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
        allowed_ips_match = re.search(r"^AllowedIPs\s*=\s*(.*)$", content, re.MULTILINE)
        if not allowed_ips_match:
            print("[错误] 未找到AllowedIPs配置项")
            return False
            
        # 获取现有的IP列表
        existing_ips = [ip.strip() for ip in allowed_ips_match.group(1).split(',')]
        
        # 添加新的IP（带/32后缀）
        new_ip_entry = f"{ip}/32"
        if new_ip_entry not in existing_ips:
            existing_ips.append(new_ip_entry)
            # 更新配置内容
            new_allowed_ips = ", ".join(existing_ips)
            content = re.sub(r"^AllowedIPs\s*=\s*.*$", 
                           f"AllowedIPs = {new_allowed_ips}", 
                           content, flags=re.MULTILINE)
            
            # 写入更新后的配置
            with open(wg_conf_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
        return True
    except Exception as e:
        print(f"[错误] 更新WireGuard配置失败: {e}")
        return False

def main_menu():
    """主菜单函数"""
    first_render = True
    while True:
        clear_screen()
        print("=" * 50)
        print("           AUTOVPN 管理面板")
        print("=" * 50)
        check_and_display_service_status()
        print("=" * 50)

        # 首次渲染后短暂停顿，避免首屏状态条被闪掉
        if first_render:
            sys.stdout.flush()
            try:
                time.sleep(0.12)
            except Exception:
                pass
            first_render = False

        # 强制刷新输出缓冲区
        sys.stdout.flush()

        # 加载配置
        config = load_config()

        # 核心功能模块
        print("1.启动wstunnel服务")
        print("2.启动WireGuard模式 (UDP转发)")
        print("3.启动代理模式 (SOCKS5/HTTP)")
        print("4.启动综合模式 (同时支持WireGuard和代理)")
        print("=" * 50)

        # 配置管理模块
        print("5.补充待解析域名")
        print("6.解析域名列表")
        print("7.更新Hosts文件")
        print("8.同步到wireguard配置")
        print("=" * 50)

        # 测试与工具模块
        print("9.检查网络状态")
        print("10.测试WireGuard连接")
        print("11.测试代理连接")
        print("12.编辑配置文件")
        print("13.检测并安装WireGuard")
        print("=" * 50)

        # 系统管理模块
        print("14.清空Hosts文件")
        print("15.查看hosts文件")
        print("16.查看wireguard配置文件")
        print("17.添加单个域名并完成全流程")
        print("18.切换IPv6功能开关")
        print("=" * 50)

        # 确保菜单显示完成
        sys.stdout.flush()
        
        # 获取用户输入，增强处理粘贴文本的能力
        try:
            raw_input = input("请选择功能 [0-18]: ").strip()
            
            # 如果用户直接按回车，跳过本次循环
            if not raw_input:
                print("\n请输入有效选项")
                input("按Enter键继续...")
                continue
            
            # 检查是否是用户粘贴了域名列表（仅在主菜单选择阶段）
            # 改进的粘贴检测逻辑：
            # 1. 检查是否包含多个域名（通过空格、换行、制表符分隔）
            # 2. 检查是否包含常见的域名后缀
            # 3. 检查是否包含协议或看起来像域名的文本
            if ('\n' in raw_input or raw_input.count(' ') > 2 or 
                any(suffix in raw_input for suffix in ['.com', '.org', '.net', '.edu', '.gov', '.cn', '.io', '.ai']) or
                'http://' in raw_input or 'https://' in raw_input):
                
                # 如果看起来像粘贴的域名列表，询问用户是否要添加这些域名
                if len(raw_input) > 30 or raw_input.count('\n') > 0 or raw_input.count(' ') > 2:
                    print("\n检测到您可能粘贴了域名列表，是否要将这些域名添加到解析列表中？")
                    # 获取确认输入并只取第一个字符
                    confirm_input = input("请输入 'y' 确认，或输入菜单选项编号: ").strip().lower()
                    
                    # 如果用户直接按回车或输入为空，提示重新输入
                    if not confirm_input:
                        print("\n请输入有效选项")
                        input("按Enter键继续...")
                        continue
                    
                    # 如果用户输入的是'y'或'yes'，直接处理域名
                    if confirm_input.startswith('y'):
                        # 调用选项5的功能来处理域名
                        process_pasted_domains(raw_input, config)
                        input("按Enter键继续...")
                        continue  # 处理完后直接继续主菜单循环
                    # 如果用户输入的是有效的菜单选项编号，使用该选项
                    elif confirm_input in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17']:
                        choice = confirm_input
                    # 如果用户输入了其他内容，提示错误并重新开始循环
                    else:
                        print(f"\n无效输入: '{confirm_input}'，请输入 'y' 或 0-16之间的数字")
                        input("按Enter键继续...")
                        continue
                else:
                    # 清理输入，只取第一个有效的数字作为选择
                    choice = ''.join(filter(str.isdigit, raw_input.split()[0] if raw_input.split() else ''))
            else:
                # 清理输入，只取第一个有效的数字作为选择
                choice = ''.join(filter(str.isdigit, raw_input.split()[0] if raw_input.split() else ''))
            
            # 验证输入是否为有效选择
            if choice not in [
                '0',
                '1',
                '2',
                '3',
                '4',
                '5',
                '6',
                '7',
                '8',
                '9',
                '10',
                '11',
                '12',
                '13',
                '14',
                '15',
                '16',
                '17',
                '18']:
                print(f"\n无效输入: '{raw_input}'，请输入0-18之间的数字")
                input("按Enter键继续...")
                continue
        except (EOFError, KeyboardInterrupt):
            print("\n程序被中断")
            break
        except Exception as e:
            print(f"\n输入错误: {e}")
            input("按Enter键继续...")
            continue

        if choice == '1':
            # 启动wstunnel服务
            try:
                wstunnel_script = os.path.join(SCRIPT_DIR, "wstunnel_client.py")
                if os.path.exists(wstunnel_script):
                    print("正在启动wstunnel服务...")
                    result = subprocess.run([sys.executable, wstunnel_script], cwd=SCRIPT_DIR)
                    if result.returncode == 0:
                        print("✅ wstunnel服务已启动")
                    else:
                        print("❌ wstunnel服务启动失败，请检查日志")
                else:
                    print(f"[错误] wstunnel客户端脚本不存在: {wstunnel_script}")
            except Exception as e:
                print(f"[错误] 启动wstunnel服务失败: {e}")
            input("按Enter键继续...")

        elif choice == '2':
            run_wireguard_mode(config)
        elif choice == '3':
            print("\n启动代理模式...")
            run_proxy_mode(config)
            print("✅ 代理模式已启动。")
        elif choice == '4':
            run_combined_mode(config)
        elif choice == '5':
            print("\n=== 添加域名到解析列表 ===")
            print("1. 手动输入域名")
            print("2. 从推荐列表添加")
            sub_choice = input("请选择添加方式 (1-2, 默认为1): ").strip()
            
            if sub_choice == '2':
                # 从推荐列表添加域名
                try:
                    add_recommended_script = os.path.join(SCRIPT_DIR, "add_recommended_domains.py")
                    if os.path.exists(add_recommended_script):
                        subprocess.run([sys.executable, add_recommended_script], cwd=SCRIPT_DIR)
                    else:
                        print(f"[错误] 添加推荐域名脚本不存在: {add_recommended_script}")
                except Exception as e:
                    print(f"[错误] 执行添加推荐域名脚本失败: {e}")
            else:
                # 手动输入域名（原有功能）
                print("\n请输入要添加的域名（多个域名请用空格分隔，输入完成后按Enter键）:")
                print("如果要粘贴多行域名，请粘贴后按Enter键两次结束输入")
                domain_lines = []
                while True:
                    line = input().strip()
                    if not line and domain_lines:  # 如果输入空行且已有内容，则结束输入
                        break
                    if line:  # 只添加非空行
                        domain_lines.append(line)
                
                domain_input = '\n'.join(domain_lines)
                if domain_input:
                    process_pasted_domains(domain_input, config)
                else:
                    print("未输入域名")
            input("按Enter键继续...")
        elif choice == '6':
            print("\n正在解析域名列表...")
            try:
                # 自动检测域名数量并选择合适的解析模式
                domain_list_path = os.path.join(PROJECT_ROOT, "routes", "需要获取IP的域名列表.txt")
                if os.path.exists(domain_list_path):
                    with open(domain_list_path, 'r', encoding='utf-8') as f:
                        domain_count = len([line for line in f.readlines() 
                                          if line.strip() and not line.startswith('#')])
                    
                    if domain_count > 20:
                        # 自动使用批量解析模式，无需用户确认
                        print(f"检测到域名列表包含 {domain_count} 个域名，自动使用批量解析模式...")
                        batch_resolver = os.path.join(SCRIPT_DIR, "batch_domain_resolver.py")
                        if os.path.exists(batch_resolver):
                            subprocess.run([sys.executable, batch_resolver], cwd=SCRIPT_DIR)
                        else:
                            print(f"[错误] 批量解析脚本不存在: {batch_resolver}")
                        return  # 处理完成直接返回
                
                # 域名数量较少时使用原有的解析方式
                resolve_script = os.path.join(SCRIPT_DIR, "resolve_ip_remote.py")
                if os.path.exists(resolve_script):
                    subprocess.run([sys.executable, resolve_script], cwd=SCRIPT_DIR)
                else:
                    print(f"[错误] 解析脚本不存在: {resolve_script}")
            except Exception as e:
                print(f"[错误] 执行域名解析失败: {e}")
        elif choice == '7':
            print("\n正在更新Hosts文件...")
            try:
                update_script = os.path.join(SCRIPT_DIR, "update_hosts.py")
                if os.path.exists(update_script):
                    subprocess.run(
                        [sys.executable, update_script], cwd=SCRIPT_DIR)
                else:
                    print(f"[错误] 更新脚本不存在: {update_script}")
            except Exception as e:
                print(f"[错误] 更新Hosts文件失败: {e}")
        elif choice == '8':
            run_sync_config()
            # 统一换行 -> 删除，避免多余空白
            # print("\n")
        elif choice == '9':
            check_network_status(config)
        elif choice == '10':
            run_wireguard_test()
        elif choice == '11':
            run_proxy_test()
        elif choice == '12':
            edit_config()
        elif choice == '13':
            check_and_install_wireguard()
            # 统一换行 -> 删除
            # print("\n")
        elif choice == '14':
            print("\n正在清空Hosts文件...")
            try:
                hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
                if os.path.exists(hosts_path):
                    with open(hosts_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    # 过滤掉AUTOVPN部分
                    new_lines = []
                    skip_mode = False
                    for line in lines:
                        if line.strip() == '# AUTOVPN自动写入':
                            skip_mode = True
                            continue
                        if skip_mode and (line.startswith('#') or line.strip() == ''):
                            skip_mode = False
                        if not skip_mode:
                            new_lines.append(line)
                    
                    with open(hosts_path, 'w', encoding='utf-8') as f:
                        f.writelines(new_lines)
                    print("✅ Hosts文件已清空AUTOVPN部分")
                else:
                    print(f"[错误] hosts文件不存在: {hosts_path}")
            except Exception as e:
                print(f"[错误] 清空hosts文件失败: {e}")
            input("按Enter键继续...")
        elif choice == '15':
            view_hosts_file()
        elif choice == '16':
            view_wireguard_config()
        elif choice == '17':
            print("\n=== 添加单个域名并完成全流程 ===")
            print("请输入要添加的域名:")
            domain = input().strip()
            if domain:
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
            else:
                print("未输入域名")
            input("按Enter键继续...")
        
        elif choice == '18':
            # 直接切换IPv6状态
            try:
                current_config = load_config()
                current_ipv6 = current_config.get('IPv6_ENABLE', 'false').lower() == 'true'
                new_state = 'false' if current_ipv6 else 'true'
                
                # 更新配置文件
                config_path = os.path.join(SCRIPT_DIR, 'config.env')
                if os.path.exists(config_path):
                    with open(config_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 替换IPv6_ENABLE值
                    content = re.sub(r'IPv6_ENABLE=.*', f'IPv6_ENABLE={new_state}', content)
                    
                    with open(config_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    status_text = "关闭" if current_ipv6 else "开启"
                    print(f"✅ IPv6功能已{status_text}")
                else:
                    print("[错误] 配置文件不存在")
                    
            except Exception as e:
                print(f"[错误] 切换IPv6状态失败: {e}")
            
            # 直接返回菜单，不暂停
            continue
        
        # 其余分支各自包含必要的暂停逻辑；不要在此处放置脱离条件的暂停
        elif choice == '0':
            print("\n感谢使用AUTOVPN！")
            break
        else:
            print(f"\n无效选择: {choice}")
            input("按Enter键继续...")


if __name__ == "__main__":
    if platform.system() == "Windows":
        # 设置控制台代码页为UTF-8，确保中文正常显示
        os.system('chcp 65001 >nul')

    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\n程序被用户中断，正在退出...")
    except Exception as e:
        print(f"\n\n发生错误: {e}")
        print("请检查日志文件了解详情")

    # 在退出前询问是否终止所有服务
    try:
        if is_process_running('wstunnel.exe'):
            choice = input("\n是否终止所有wstunnel服务? (y/n): ").strip().lower()
            if choice == 'y':
                kill_process_by_name('wstunnel.exe')
                print("已终止所有wstunnel服务")
    except (KeyboardInterrupt, Exception):
        pass  # 忽略退出时的异常
    print("\nAUTOVPN已退出")