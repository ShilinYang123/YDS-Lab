#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTOVPN菜单功能测试运行器
用于自动测试菜单中的各项功能
"""

import os
import sys
import subprocess
import time
import json
import platform
import tempfile
from pathlib import Path

# 获取脚本目录和项目根目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# 添加脚本目录到Python路径
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

class MenuTester:
    def __init__(self):
        self.test_results = []
        self.config = {}
        self.load_config()
        
    def load_config(self):
        """加载配置文件"""
        config_path = os.path.join(SCRIPT_DIR, "config.env")
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        if '#' in value:
                            value = value.split('#')[0]
                        self.config[key.strip()] = value.strip()
        except Exception as e:
            print(f"[警告] 加载配置文件失败: {e}")
            self.config = {}
    
    def log_result(self, test_name, status, details=""):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "status": status,  # "PASS", "FAIL", "SKIP"
            "details": details,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.test_results.append(result)
        status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_symbol} {test_name}: {status}")
        if details:
            print(f"   详情: {details}")
    
    def test_config_loading(self):
        """测试配置加载功能"""
        print("\n=== 测试配置加载功能 ===")
        try:
            if self.config:
                self.log_result("配置加载", "PASS", f"成功加载 {len(self.config)} 个配置项")
            else:
                self.log_result("配置加载", "FAIL", "配置为空或未找到配置文件")
        except Exception as e:
            self.log_result("配置加载", "FAIL", str(e))
    
    def test_network_ping(self):
        """测试网络ping功能"""
        print("\n=== 测试网络ping功能 ===")
        try:
            result = subprocess.run(['ping', '-n', '1', '8.8.8.8'],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                self.log_result("网络ping测试", "PASS", "Google DNS连通正常")
            else:
                self.log_result("网络ping测试", "FAIL", "Google DNS不可达")
        except Exception as e:
            self.log_result("网络ping测试", "FAIL", str(e))
    
    def test_dns_resolution(self):
        """测试DNS解析功能"""
        print("\n=== 测试DNS解析功能 ===")
        try:
            result = subprocess.run(['nslookup', 'google.com'],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and 'Address:' in result.stdout:
                self.log_result("DNS解析测试", "PASS", "google.com解析正常")
            else:
                self.log_result("DNS解析测试", "FAIL", "DNS解析失败")
        except Exception as e:
            self.log_result("DNS解析测试", "FAIL", str(e))
    
    def test_ipv6_connectivity(self):
        """测试IPv6连通性"""
        print("\n=== 测试IPv6连通性 ===")
        try:
            # 测试IPv6回环地址
            result = subprocess.run(['ping', '-6', '-n', '1', '::1'],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                self.log_result("IPv6回环测试", "PASS", "IPv6回环地址连通正常")
            else:
                self.log_result("IPv6回环测试", "FAIL", "IPv6回环地址不可达")
                
            # 测试IPv6 DNS
            result = subprocess.run(['nslookup', '-type=AAAA', 'google.com'],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and 'AAAA' in result.stdout:
                self.log_result("IPv6 DNS测试", "PASS", "IPv6 DNS解析正常")
            else:
                self.log_result("IPv6 DNS测试", "FAIL", "IPv6 DNS解析失败")
        except Exception as e:
            self.log_result("IPv6连通性测试", "FAIL", str(e))
    
    def test_port_connectivity(self):
        """测试端口连通性"""
        print("\n=== 测试端口连通性 ===")
        try:
            import socket
            
            # 测试常用端口
            ports_to_test = [
                ("SOCKS5代理", int(self.config.get('SOCKS5_PORT', '1082'))),
                ("HTTP代理", int(self.config.get('HTTP_PORT', '8081'))),
                ("wstunnel", int(self.config.get('WSTUNNEL_PORT', '1081')))
            ]
            
            for service_name, port in ports_to_test:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.settimeout(3)
                        result = sock.connect_ex(('127.0.0.1', port))
                        if result == 0:
                            self.log_result(f"{service_name}端口测试", "PASS", f"端口{port}已监听")
                        else:
                            self.log_result(f"{service_name}端口测试", "FAIL", f"端口{port}未监听")
                except Exception as e:
                    self.log_result(f"{service_name}端口测试", "FAIL", str(e))
                    
        except Exception as e:
            self.log_result("端口连通性测试", "FAIL", str(e))
    
    def test_file_operations(self):
        """测试文件操作功能"""
        print("\n=== 测试文件操作功能 ===")
        try:
            # 测试创建临时文件
            test_file = os.path.join(SCRIPT_DIR, "test_temp.txt")
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write("测试内容")
            
            # 测试读取文件
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 测试删除文件
            os.remove(test_file)
            
            if content == "测试内容":
                self.log_result("文件操作测试", "PASS", "文件读写删除正常")
            else:
                self.log_result("文件操作测试", "FAIL", "文件内容不匹配")
                
        except Exception as e:
            self.log_result("文件操作测试", "FAIL", str(e))
    
    def test_hosts_file_access(self):
        """测试Hosts文件访问"""
        print("\n=== 测试Hosts文件访问 ===")
        try:
            hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
            if os.path.exists(hosts_path):
                # 测试读取权限
                with open(hosts_path, 'r', encoding='utf-8') as f:
                    content = f.read(100)  # 只读取前100字符
                
                # 测试写入权限（创建临时文件）
                temp_hosts = hosts_path + ".tmp"
                try:
                    with open(temp_hosts, 'w', encoding='utf-8') as f:
                        f.write("# 测试写入")
                    os.remove(temp_hosts)
                    self.log_result("Hosts文件访问测试", "PASS", "文件读写权限正常")
                except Exception as e:
                    self.log_result("Hosts文件访问测试", "FAIL", f"写入权限不足: {e}")
            else:
                self.log_result("Hosts文件访问测试", "FAIL", "Hosts文件不存在")
                
        except Exception as e:
            self.log_result("Hosts文件访问测试", "FAIL", str(e))
    
    def test_domain_resolution_module(self):
        """测试域名解析模块"""
        print("\n=== 测试域名解析模块 ===")
        try:
            resolve_script = os.path.join(SCRIPT_DIR, "resolve_ip_remote.py")
            if os.path.exists(resolve_script):
                self.log_result("域名解析模块测试", "PASS", f"解析脚本存在: {resolve_script}")
            else:
                self.log_result("域名解析模块测试", "FAIL", f"解析脚本不存在: {resolve_script}")
                
            # 检查域名列表文件
            domain_list_path = os.path.join(PROJECT_ROOT, "routes", "需要获取IP的域名列表.txt")
            if os.path.exists(domain_list_path):
                self.log_result("域名列表文件测试", "PASS", f"域名列表文件存在: {domain_list_path}")
            else:
                self.log_result("域名列表文件测试", "FAIL", f"域名列表文件不存在: {domain_list_path}")
                
        except Exception as e:
            self.log_result("域名解析模块测试", "FAIL", str(e))
    
    def test_ipv6_switch_function(self):
        """测试IPv6开关功能"""
        print("\n=== 测试IPv6开关功能 ===")
        try:
            config_path = os.path.join(SCRIPT_DIR, "config.env")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if 'IPv6_ENABLE' in content:
                    self.log_result("IPv6配置测试", "PASS", "IPv6开关配置存在")
                else:
                    self.log_result("IPv6配置测试", "FAIL", "IPv6开关配置不存在")
            else:
                self.log_result("IPv6配置测试", "FAIL", "配置文件不存在")
                
        except Exception as e:
            self.log_result("IPv6开关功能测试", "FAIL", str(e))
    
    def test_service_status_check(self):
        """测试服务状态检查"""
        print("\n=== 测试服务状态检查 ===")
        try:
            import psutil
            
            # 检查wstunnel进程
            wstunnel_running = False
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] and 'wstunnel' in proc.info['name'].lower():
                    wstunnel_running = True
                    break
            
            if wstunnel_running:
                self.log_result("wstunnel服务测试", "PASS", "wstunnel进程正在运行")
            else:
                self.log_result("wstunnel服务测试", "FAIL", "wstunnel进程未运行")
            
            # 检查privoxy进程
            privoxy_running = False
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] and 'privoxy' in proc.info['name'].lower():
                    privoxy_running = True
                    break
            
            if privoxy_running:
                self.log_result("privoxy服务测试", "PASS", "privoxy进程正在运行")
            else:
                self.log_result("privoxy服务测试", "FAIL", "privoxy进程未运行")
                
        except Exception as e:
            self.log_result("服务状态检查测试", "FAIL", str(e))
    
    def test_config_integrity(self):
        """测试配置文件完整性"""
        print("\n=== 测试配置文件完整性 ===")
        try:
            required_configs = [
                'SERVER_IP', 'SERVER_PORT', 'WSTUNNEL_PORT',
                'SOCKS5_PORT', 'HTTP_PORT', 'WG_CONF_PATH'
            ]
            
            missing_configs = []
            for config_key in required_configs:
                if config_key not in self.config or not self.config[config_key]:
                    missing_configs.append(config_key)
            
            if not missing_configs:
                self.log_result("配置文件完整性测试", "PASS", "所有必需配置项都存在")
            else:
                self.log_result("配置文件完整性测试", "FAIL", f"缺少配置项: {', '.join(missing_configs)}")
                
        except Exception as e:
            self.log_result("配置文件完整性测试", "FAIL", str(e))
    
    def test_script_dependencies(self):
        """测试脚本依赖"""
        print("\n=== 测试脚本依赖 ===")
        try:
            required_scripts = [
                "resolve_ip_remote.py",
                "update_hosts.py",
                "sync_config.py",
                "run_wireguard.py",
                "run_proxy.py"
            ]
            
            missing_scripts = []
            for script_name in required_scripts:
                script_path = os.path.join(SCRIPT_DIR, script_name)
                if not os.path.exists(script_path):
                    missing_scripts.append(script_name)
            
            if not missing_scripts:
                self.log_result("脚本依赖测试", "PASS", "所有必需脚本都存在")
            else:
                self.log_result("脚本依赖测试", "FAIL", f"缺少脚本: {', '.join(missing_scripts)}")
                
        except Exception as e:
            self.log_result("脚本依赖测试", "FAIL", str(e))
    
    def generate_report(self):
        """生成测试报告"""
        print("\n=== 测试报告 ===")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["status"] == "PASS")
        failed_tests = sum(1 for r in self.test_results if r["status"] == "FAIL")
        skipped_tests = sum(1 for r in self.test_results if r["status"] == "SKIP")
        
        print(f"总测试项: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {failed_tests}")
        print(f"跳过: {skipped_tests}")
        print(f"成功率: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%")
        
        # 保存详细报告
        report_path = os.path.join(SCRIPT_DIR, "menu_function_test_report.txt")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("AUTOVPN菜单功能测试报告\n")
            f.write("=" * 50 + "\n")
            f.write(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"总测试项: {total_tests}\n")
            f.write(f"通过: {passed_tests}\n")
            f.write(f"失败: {failed_tests}\n")
            f.write(f"跳过: {skipped_tests}\n")
            f.write(f"成功率: {(passed_tests/total_tests*100):.1f}%\n")
            f.write("\n详细测试结果:\n")
            f.write("-" * 50 + "\n")
            
            for result in self.test_results:
                status_symbol = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
                f.write(f"{status_symbol} {result['test_name']}: {result['status']}\n")
                if result["details"]:
                    f.write(f"   详情: {result['details']}\n")
                f.write("\n")
        
        print(f"\n详细报告已保存到: {report_path}")
        return report_path
    
    def run_all_tests(self):
        """运行所有测试"""
        print("开始AUTOVPN菜单功能测试...")
        print("=" * 50)
        
        # 基础功能测试
        self.test_config_loading()
        self.test_network_ping()
        self.test_dns_resolution()
        self.test_ipv6_connectivity()
        self.test_port_connectivity()
        self.test_file_operations()
        self.test_hosts_file_access()
        self.test_domain_resolution_module()
        self.test_ipv6_switch_function()
        self.test_service_status_check()
        self.test_config_integrity()
        self.test_script_dependencies()
        
        # 生成报告
        report_path = self.generate_report()
        
        return self.test_results, report_path

def main():
    """主函数"""
    tester = MenuTester()
    results, report_path = tester.run_all_tests()
    
    print(f"\n测试完成！报告已保存到: {report_path}")
    input("\n按Enter键退出...")

if __name__ == "__main__":
    if platform.system() == "Windows":
        os.system('chcp 65001 >nul')
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n\n测试过程中发生错误: {e}")