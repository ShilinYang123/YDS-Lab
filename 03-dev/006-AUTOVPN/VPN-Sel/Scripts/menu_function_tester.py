#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTOVPN菜单功能直接测试器
绕过交互式菜单，直接测试各个功能模块
"""

import os
import sys
import time
import subprocess
import socket
import re
from datetime import datetime

# 添加脚本目录到路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

# 导入菜单功能
from autovpn_menu import (
    load_config, check_network_status, is_process_running, 
    kill_process_by_name, check_and_display_service_status
)

class MenuFunctionTester:
    def __init__(self):
        self.test_results = []
        self.config = load_config()
        self.test_log = os.path.join(SCRIPT_DIR, "menu_function_test.log")
        
    def log_message(self, message, level="INFO"):
        """记录测试日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        
        with open(self.test_log, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')
    
    def run_command_with_timeout(self, command, timeout=10):
        """运行命令并设置超时"""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=timeout,
                cwd=SCRIPT_DIR
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
        """测试配置加载"""
        def load_test():
            config = load_config()
            return config is not None and len(config) > 0
        
        return self.test_function("配置加载功能", load_test)
    
    def test_network_ping(self):
        """测试网络ping功能"""
        def ping_test():
            ret_code, stdout, stderr = self.run_command_with_timeout("ping 8.8.8.8 -n 2")
            return ret_code == 0 and "TTL=" in stdout
        
        return self.test_function("网络ping测试", ping_test)
    
    def test_dns_resolution(self):
        """测试DNS解析"""
        def dns_test():
            ret_code, stdout, stderr = self.run_command_with_timeout("nslookup google.com")
            return ret_code == 0 and "Address:" in stdout
        
        return self.test_function("DNS解析测试", dns_test)
    
    def test_ipv6_ping(self):
        """测试IPv6 ping"""
        def ipv6_test():
            ret_code, stdout, stderr = self.run_command_with_timeout("ping ::1 -n 1")
            return ret_code == 0
        
        return self.test_function("IPv6回环测试", ipv6_test)
    
    def test_ipv6_dns(self):
        """测试IPv6 DNS"""
        def ipv6_dns_test():
            ret_code, stdout, stderr = self.run_command_with_timeout("nslookup -type=AAAA google.com")
            return ret_code == 0 and "AAAA" in stdout
        
        return self.test_function("IPv6 DNS测试", ipv6_dns_test)
    
    def test_port_checking(self):
        """测试端口检查功能"""
        def port_test():
            # 检查常见端口
            ports_to_check = [80, 443, 53]
            results = {}
            
            for port in ports_to_check:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex(('8.8.8.8', port))
                    sock.close()
                    results[port] = (result == 0)
                except:
                    results[port] = False
            
            return results
        
        result = self.test_function("端口连通性测试", port_test)
        if result:
            ports_status = port_test()
            for port, status in ports_status.items():
                self.log_message(f"端口 {port}: {'开放' if status else '关闭'}")
        return result
    
    def test_file_operations(self):
        """测试文件操作功能"""
        def file_test():
            test_file = os.path.join(SCRIPT_DIR, "test_file_operations.txt")
            
            try:
                # 测试写入
                with open(test_file, 'w', encoding='utf-8') as f:
                    f.write("测试文件操作\n")
                
                # 测试读取
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 测试删除
                os.remove(test_file)
                
                return len(content) > 0
                
            except Exception as e:
                # 清理测试文件
                if os.path.exists(test_file):
                    os.remove(test_file)
                return False
        
        return self.test_function("文件操作测试", file_test)
    
    def test_domain_parsing(self):
        """测试域名解析功能"""
        def domain_test():
            # 测试get_clean_ips_v2.py的基本功能
            ret_code, stdout, stderr = self.run_command_with_timeout(
                "python get_clean_ips_v2.py --help"
            )
            
            if ret_code != 0:
                # 如果没有help参数，测试基本导入
                try:
                    import get_clean_ips_v2
                    return True
                except:
                    return False
            else:
                return True
        
        return self.test_function("域名解析模块测试", domain_test)
    
    def test_ipv6_toggle(self):
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
    
    def test_hosts_file_access(self):
        """测试Hosts文件访问"""
        def hosts_test():
            hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
            
            try:
                # 测试读取
                with open(hosts_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 测试写入（临时操作）
                test_line = "# AUTOVPN测试写入\n"
                with open(hosts_path, 'a', encoding='utf-8') as f:
                    f.write(test_line)
                
                # 清理测试行
                with open(hosts_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                with open(hosts_path, 'w', encoding='utf-8') as f:
                    f.writelines([line for line in lines if line != test_line])
                
                return True
                
            except Exception as e:
                return False
        
        return self.test_function("Hosts文件访问测试", hosts_test)
    
    def test_service_status_checking(self):
        """测试服务状态检查"""
        def service_test():
            try:
                # 模拟服务状态检查
                wstunnel_running = is_process_running('wstunnel.exe')
                
                # 检查端口监听状态
                ret_code1, stdout1, stderr1 = self.run_command_with_timeout("netstat -an | findstr :1082")
                socks5_listening = ret_code1 == 0 and "LISTENING" in stdout1
                
                ret_code2, stdout2, stderr2 = self.run_command_with_timeout("netstat -an | findstr :8081")
                http_listening = ret_code2 == 0 and "LISTENING" in stdout2
                
                return {
                    'wstunnel_running': wstunnel_running,
                    'socks5_listening': socks5_listening,
                    'http_listening': http_listening
                }
                
            except Exception as e:
                return {'error': str(e)}
        
        result = self.test_function("服务状态检查", service_test)
        if result:
            service_status = service_test()
            self.log_message(f"服务状态: {service_status}")
        return result
    
    def test_config_file_integrity(self):
        """测试配置文件完整性"""
        def config_test():
            config_path = os.path.join(SCRIPT_DIR, "config.env")
            
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检查关键配置项
                required_keys = [
                    'SERVER_IP', 'SSH_PORT', 'SSH_USER', 'SSH_KEY_PATH',
                    'WG_PORT', 'WG_INTERFACE', 'PROXY_PORT', 'SOCKS5_PORT'
                ]
                
                missing_keys = []
                for key in required_keys:
                    if key not in content:
                        missing_keys.append(key)
                
                return len(missing_keys) == 0, missing_keys
                
            except Exception as e:
                return False, [str(e)]
        
        result = self.test_function("配置文件完整性检查", config_test)
        if result:
            success, missing_keys = config_test()
            if missing_keys:
                self.log_message(f"缺失的配置项: {missing_keys}")
        return result
    
    def test_script_dependencies(self):
        """测试脚本依赖"""
        def dependency_test():
            required_scripts = [
                "get_clean_ips_v2.py",
                "resolve_ip_remote.py",
                "update_hosts.py",
                "batch_domain_resolver.py"
            ]
            
            missing_scripts = []
            for script in required_scripts:
                script_path = os.path.join(SCRIPT_DIR, script)
                if not os.path.exists(script_path):
                    missing_scripts.append(script)
            
            return len(missing_scripts) == 0, missing_scripts
        
        result = self.test_function("脚本依赖检查", dependency_test)
        if result:
            success, missing_scripts = dependency_test()
            if missing_scripts:
                self.log_message(f"缺失的脚本: {missing_scripts}")
        return result
    
    def generate_test_report(self):
        """生成测试报告"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['success'])
        failed_tests = total_tests - passed_tests
        
        report = f"""
===========================================
AUTOVPN菜单功能直接测试报告
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
                report += f"    结果: {result['result']}\n"
        
        # 添加功能状态总结
        report += f"\n功能状态总结:\n"
        report += f"{'='*50}\n"
        
        # 检查关键功能状态
        network_ok = any(r['success'] for r in self.test_results if '网络' in r['name'])
        dns_ok = any(r['success'] for r in self.test_results if 'DNS' in r['name'])
        ipv6_ok = any(r['success'] for r in self.test_results if 'IPv6' in r['name'] and '开关' not in r['name'])
        config_ok = any(r['success'] for r in self.test_results if '配置' in r['name'])
        
        report += f"网络连接: {'✅正常' if network_ok else '❌异常'}\n"
        report += f"DNS解析: {'✅正常' if dns_ok else '❌异常'}\n"
        report += f"IPv6支持: {'✅正常' if ipv6_ok else '❌异常'}\n"
        report += f"配置文件: {'✅完整' if config_ok else '❌不完整'}\n"
        
        report += "\n===========================================\n"
        
        # 保存报告到文件
        report_file = os.path.join(SCRIPT_DIR, "menu_function_test_report.txt")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        self.log_message(f"测试报告已保存到: {report_file}")
        return report
    
    def run_all_tests(self):
        """运行所有测试"""
        self.log_message("开始AUTOVPN菜单功能直接测试...")
        
        # 基础功能测试
        self.test_config_loading()
        self.test_network_ping()
        self.test_dns_resolution()
        self.test_ipv6_ping()
        self.test_ipv6_dns()
        
        # 系统功能测试
        self.test_port_checking()
        self.test_file_operations()
        self.test_hosts_file_access()
        
        # 高级功能测试
        self.test_domain_parsing()
        self.test_ipv6_toggle()
        self.test_service_status_checking()
        self.test_config_file_integrity()
        self.test_script_dependencies()
        
        # 生成测试报告
        report = self.generate_test_report()
        print(report)
        
        self.log_message("菜单功能直接测试完成！")
        return self.test_results

def main():
    """主函数"""
    print("AUTOVPN菜单功能直接测试工具")
    print("=" * 50)
    
    tester = MenuFunctionTester()
    
    try:
        results = tester.run_all_tests()
        
        # 统计结果
        total = len(results)
        passed = sum(1 for r in results if r['success'])
        
        print(f"\n测试完成! 通过率: {passed}/{total} ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 所有功能测试通过! 系统运行正常")
        else:
            print("⚠️  部分功能测试失败，请查看详细报告")
        
        return 0 if passed == total else 1
        
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        return 1
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())