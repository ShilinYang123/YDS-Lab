#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTOVPN菜单功能自动化测试脚本
自动测试所有菜单功能，无需人工干预
"""

import os
import sys
import time
import subprocess
import threading
import queue
import re
from datetime import datetime

# 添加脚本目录到路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

from autovpn_menu import load_config, is_process_running, kill_process_by_name

class AutoVPNMenuTester:
    def __init__(self):
        self.test_results = []
        self.config = load_config()
        self.test_log = os.path.join(SCRIPT_DIR, "autovpn_menu_test.log")
        self.original_config = None
        
    def log_message(self, message, level="INFO"):
        """记录测试日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        
        with open(self.test_log, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')
    
    def run_command_with_timeout(self, command, timeout=30, cwd=None):
        """运行命令并设置超时"""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=timeout,
                cwd=cwd or SCRIPT_DIR
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "命令执行超时"
        except Exception as e:
            return -1, "", str(e)
    
    def test_function(self, test_name, test_func, expected_result=True):
        """通用测试函数"""
        self.log_message(f"开始测试: {test_name}")
        try:
            start_time = time.time()
            result = test_func()
            end_time = time.time()
            
            success = (result == expected_result) if expected_result is not None else (result is not None)
            
            self.test_results.append({
                'name': test_name,
                'success': success,
                'result': result,
                'duration': end_time - start_time,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            status = "✅ 通过" if success else "❌ 失败"
            self.log_message(f"{test_name} - {status} (耗时: {end_time - start_time:.2f}s)")
            
            return success
            
        except Exception as e:
            self.test_results.append({
                'name': test_name,
                'success': False,
                'result': str(e),
                'duration': time.time() - start_time if 'start_time' in locals() else 0,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            self.log_message(f"{test_name} - ❌ 异常: {str(e)}", "ERROR")
            return False
    
    def test_config_loading(self):
        """测试配置加载功能"""
        def load_config_test():
            config = load_config()
            return config is not None and len(config) > 0
        
        return self.test_function("配置加载", load_config_test)
    
    def test_network_connectivity(self):
        """测试网络连通性"""
        def network_test():
            # 测试基本网络连接
            ret_code, stdout, stderr = self.run_command_with_timeout("ping 8.8.8.8 -n 2")
            return ret_code == 0
        
        return self.test_function("网络连通性检查", network_test)
    
    def test_dns_resolution(self):
        """测试DNS解析功能"""
        def dns_test():
            # 测试DNS解析
            ret_code, stdout, stderr = self.run_command_with_timeout("nslookup google.com")
            return ret_code == 0 and "Address:" in stdout
        
        return self.test_function("DNS解析功能", dns_test)
    
    def test_ipv6_connectivity(self):
        """测试IPv6连接性"""
        def ipv6_test():
            # 检查IPv6是否启用
            ret_code, stdout, stderr = self.run_command_with_timeout("ping ::1 -n 1")
            ipv6_enabled = ret_code == 0
            
            # 测试IPv6 DNS解析
            ret_code, stdout, stderr = self.run_command_with_timeout("nslookup -type=AAAA google.com")
            ipv6_dns = ret_code == 0 and "AAAA" in stdout
            
            return ipv6_enabled, ipv6_dns
        
        result = self.test_function("IPv6连接性检查", ipv6_test)
        if result:
            ipv6_enabled, ipv6_dns = ipv6_test()
            self.log_message(f"IPv6本地回环: {'✅' if ipv6_enabled else '❌'}, IPv6 DNS: {'✅' if ipv6_dns else '❌'}")
        return result
    
    def test_proxy_ports(self):
        """测试代理端口状态"""
        def proxy_test():
            # 检查SOCKS5端口 (1082)
            ret_code1, stdout1, stderr1 = self.run_command_with_timeout("netstat -an | findstr :1082")
            socks5_listening = ret_code1 == 0 and "LISTENING" in stdout1
            
            # 检查HTTP代理端口 (8081)
            ret_code2, stdout2, stderr2 = self.run_command_with_timeout("netstat -an | findstr :8081")
            http_listening = ret_code2 == 0 and "LISTENING" in stdout2
            
            return socks5_listening, http_listening
        
        result = self.test_function("代理端口检查", proxy_test)
        if result:
            socks5_listening, http_listening = proxy_test()
            self.log_message(f"SOCKS5端口(1082): {'✅监听' if socks5_listening else '❌未监听'}, HTTP端口(8081): {'✅监听' if http_listening else '❌未监听'}")
        return result
    
    def test_wstunnel_process(self):
        """测试wstunnel进程状态"""
        def wstunnel_test():
            return is_process_running('wstunnel.exe')
        
        return self.test_function("wstunnel进程检查", wstunnel_test)
    
    def test_domain_resolution_scripts(self):
        """测试域名解析脚本"""
        def resolution_scripts_test():
            # 检查主要解析脚本是否存在
            scripts = [
                "get_clean_ips_v2.py",
                "resolve_ip_remote.py", 
                "batch_domain_resolver.py"
            ]
            
            results = {}
            for script in scripts:
                script_path = os.path.join(SCRIPT_DIR, script)
                results[script] = os.path.exists(script_path)
            
            return all(results.values()), results
        
        result = self.test_function("域名解析脚本检查", resolution_scripts_test)
        if result:
            success, results = resolution_scripts_test()
            for script, exists in results.items():
                self.log_message(f"{script}: {'✅存在' if exists else '❌不存在'}")
        return result
    
    def test_config_files(self):
        """测试配置文件"""
        def config_files_test():
            config_path = os.path.join(SCRIPT_DIR, "config.env")
            domain_list_path = os.path.join(PROJECT_ROOT, "routes", "需要获取IP的域名列表.txt")
            
            config_exists = os.path.exists(config_path)
            domain_list_exists = os.path.exists(domain_list_path)
            
            if config_exists:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_content = f.read()
                    config_valid = len(config_content.strip()) > 0
            else:
                config_valid = False
            
            return config_exists and config_valid and domain_list_exists
        
        return self.test_function("配置文件检查", config_files_test)
    
    def test_hosts_file_operations(self):
        """测试Hosts文件操作"""
        def hosts_test():
            hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
            
            # 检查hosts文件是否存在且可读写
            if not os.path.exists(hosts_path):
                return False, "hosts文件不存在"
            
            try:
                # 测试读取权限
                with open(hosts_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 测试写入权限（通过临时操作）
                test_line = "# AUTOVPN测试写入\n"
                with open(hosts_path, 'a', encoding='utf-8') as f:
                    f.write(test_line)
                
                # 移除测试行
                with open(hosts_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                with open(hosts_path, 'w', encoding='utf-8') as f:
                    f.writelines([line for line in lines if line != test_line])
                
                return True, "hosts文件可读写"
                
            except Exception as e:
                return False, f"hosts文件操作失败: {str(e)}"
        
        result = self.test_function("Hosts文件操作检查", hosts_test)
        if result:
            success, message = hosts_test()
            self.log_message(f"Hosts文件状态: {message}")
        return result
    
    def test_single_domain_workflow(self):
        """测试单个域名完整流程"""
        def single_domain_test():
            test_domain = "cloudflare.com"
            
            # 1. 测试域名添加
            domain_file_path = os.path.join(PROJECT_ROOT, "routes", "需要获取IP的域名列表.txt")
            try:
                with open(domain_file_path, 'a', encoding='utf-8') as f:
                    f.write(f"\n{test_domain}")
                
                # 2. 测试域名解析
                ret_code, stdout, stderr = self.run_command_with_timeout(
                    f"python get_clean_ips_v2.py --domain {test_domain} --test"
                )
                
                # 3. 清理测试域名
                with open(domain_file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                with open(domain_file_path, 'w', encoding='utf-8') as f:
                    f.writelines([line for line in lines if test_domain not in line])
                
                return ret_code == 0 and len(stdout.strip()) > 0
                
            except Exception as e:
                return False
        
        return self.test_function("单个域名完整流程", single_domain_test)
    
    def test_ipv6_toggle_function(self):
        """测试IPv6开关功能"""
        def ipv6_toggle_test():
            config_path = os.path.join(SCRIPT_DIR, "config.env")
            
            try:
                # 读取当前配置
                with open(config_path, 'r', encoding='utf-8') as f:
                    original_content = f.read()
                
                # 获取当前IPv6状态
                current_ipv6 = 'IPv6_ENABLE=true' in original_content
                
                # 切换状态
                if current_ipv6:
                    new_content = original_content.replace('IPv6_ENABLE=true', 'IPv6_ENABLE=false')
                else:
                    new_content = original_content.replace('IPv6_ENABLE=false', 'IPv6_ENABLE=true')
                
                # 写回配置
                with open(config_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                # 验证切换
                with open(config_path, 'r', encoding='utf-8') as f:
                    new_config = f.read()
                
                # 恢复原始配置
                with open(config_path, 'w', encoding='utf-8') as f:
                    f.write(original_content)
                
                toggled_successfully = ('IPv6_ENABLE=true' in new_config) != current_ipv6
                return toggled_successfully
                
            except Exception as e:
                return False
        
        return self.test_function("IPv6开关功能", ipv6_toggle_test)
    
    def test_wireguard_config_access(self):
        """测试WireGuard配置访问"""
        def wireguard_test():
            wireguard_dir = os.path.join(PROJECT_ROOT, "config", "wireguard")
            if os.path.exists(wireguard_dir):
                # 检查是否有客户端配置文件
                client_dir = os.path.join(wireguard_dir, "client")
                if os.path.exists(client_dir):
                    files = os.listdir(client_dir)
                    return len(files) > 0, f"找到 {len(files)} 个配置文件"
                else:
                    return True, "客户端配置目录不存在（正常）"
            else:
                return False, "WireGuard配置目录不存在"
        
        result = self.test_function("WireGuard配置访问", wireguard_test)
        if result:
            success, message = wireguard_test()
            self.log_message(f"WireGuard配置: {message}")
        return result
    
    def generate_test_report(self):
        """生成测试报告"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['success'])
        failed_tests = total_tests - passed_tests
        
        report = f"""
===========================================
AUTOVPN菜单功能自动化测试报告
===========================================
测试时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
总测试项: {total_tests}
通过项数: {passed_tests}
失败项数: {failed_tests}
成功率: {(passed_tests/total_tests*100):.1f}%

详细测试结果:
===========================================
"""
        
        for result in self.test_results:
            status = "✅ 通过" if result['success'] else "❌ 失败"
            report += f"{status} {result['name']} (耗时: {result['duration']:.2f}s)\n"
            if not result['success']:
                report += f"    错误信息: {result['result']}\n"
        
        report += "\n===========================================\n"
        
        # 保存报告到文件
        report_file = os.path.join(SCRIPT_DIR, "autovpn_menu_test_report.txt")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        self.log_message(f"测试报告已保存到: {report_file}")
        return report
    
    def run_all_tests(self):
        """运行所有测试"""
        self.log_message("开始AUTOVPN菜单功能自动化测试...")
        
        # 基础功能测试
        self.test_config_loading()
        self.test_network_connectivity()
        self.test_dns_resolution()
        self.test_ipv6_connectivity()
        
        # 服务状态测试
        self.test_proxy_ports()
        self.test_wstunnel_process()
        
        # 文件和配置测试
        self.test_domain_resolution_scripts()
        self.test_config_files()
        self.test_hosts_file_operations()
        
        # 高级功能测试
        self.test_single_domain_workflow()
        self.test_ipv6_toggle_function()
        self.test_wireguard_config_access()
        
        # 生成测试报告
        report = self.generate_test_report()
        print(report)
        
        self.log_message("自动化测试完成！")
        return self.test_results

def main():
    """主函数"""
    print("AUTOVPN菜单功能自动化测试工具")
    print("=" * 50)
    
    tester = AutoVPNMenuTester()
    
    try:
        results = tester.run_all_tests()
        
        # 统计结果
        total = len(results)
        passed = sum(1 for r in results if r['success'])
        
        print(f"\n测试完成! 通过率: {passed}/{total} ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 所有测试通过! 系统运行正常")
        else:
            print("⚠️  部分测试失败，请查看详细报告")
        
        return 0 if passed == total else 1
        
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        return 1
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())