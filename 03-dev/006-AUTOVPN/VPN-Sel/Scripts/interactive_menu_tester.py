#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTOVPN交互式菜单自动测试器
模拟用户输入，自动测试所有菜单选项
"""

import os
import sys
import time
import subprocess
import threading
import re
from datetime import datetime

# 添加脚本目录到路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

class InteractiveMenuTester:
    def __init__(self):
        self.test_results = []
        self.menu_process = None
        self.output_queue = queue.Queue()
        self.test_log = os.path.join(SCRIPT_DIR, "interactive_menu_test.log")
        
    def log_message(self, message, level="INFO"):
        """记录测试日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        
        with open(self.test_log, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')
    
    def start_menu_process(self):
        """启动菜单进程"""
        self.log_message("启动AUTOVPN菜单进程...")
        
        # 使用subprocess启动菜单
        self.menu_process = subprocess.Popen(
            [sys.executable, "autovpn_menu.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=SCRIPT_DIR,
            encoding='utf-8'
        )
        
        # 等待菜单启动
        time.sleep(3)
        self.log_message("菜单进程启动完成")
        
    def send_menu_choice(self, choice, wait_time=2):
        """发送菜单选择"""
        if self.menu_process and self.menu_process.stdin:
            self.log_message(f"发送菜单选择: {choice}")
            self.menu_process.stdin.write(f"{choice}\n")
            self.menu_process.stdin.flush()
            time.sleep(wait_time)
            return True
        return False
    
    def read_process_output(self, timeout=5):
        """读取进程输出"""
        output = ""
        try:
            # 读取标准输出
            while True:
                line = self.menu_process.stdout.readline()
                if not line:
                    break
                output += line
                if "按Enter键继续" in line or "功能选择" in line:
                    break
        except:
            pass
        
        return output
    
    def test_menu_option(self, option_num, option_name, expected_keywords=None, input_after="\n"):
        """测试特定菜单选项"""
        self.log_message(f"测试菜单选项 {option_num}: {option_name}")
        
        start_time = time.time()
        success = False
        error_msg = ""
        
        try:
            # 发送菜单选择
            if self.send_menu_choice(option_num, wait_time=3):
                # 读取输出
                output = self.read_process_output(timeout=5)
                
                # 如果需要额外输入
                if input_after:
                    self.menu_process.stdin.write(input_after)
                    self.menu_process.stdin.flush()
                    time.sleep(2)
                
                # 检查预期关键词
                if expected_keywords:
                    all_found = all(keyword in output for keyword in expected_keywords)
                    if all_found:
                        success = True
                    else:
                        error_msg = f"未找到预期关键词: {expected_keywords}"
                else:
                    # 如果没有特定关键词，检查是否有错误信息
                    if "错误" in output or "失败" in output:
                        error_msg = "检测到错误信息"
                    elif len(output.strip()) > 0:
                        success = True
                    else:
                        error_msg = "无输出内容"
                
                self.log_message(f"选项 {option_num} 输出:\n{output[:500]}...")
                
            else:
                error_msg = "无法发送菜单选择"
                
        except Exception as e:
            error_msg = f"异常: {str(e)}"
        
        end_time = time.time()
        
        # 记录测试结果
        self.test_results.append({
            'option': option_num,
            'name': option_name,
            'success': success,
            'duration': end_time - start_time,
            'error': error_msg,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        status = "✅ 通过" if success else "❌ 失败"
        self.log_message(f"选项 {option_num} - {status} (耗时: {end_time - start_time:.2f}s)")
        if not success:
            self.log_message(f"失败原因: {error_msg}", "ERROR")
        
        return success
    
    def run_menu_tests(self):
        """运行所有菜单测试"""
        self.log_message("开始交互式菜单测试...")
        
        try:
            # 启动菜单
            self.start_menu_process()
            
            # 等待菜单完全启动
            time.sleep(5)
            
            # 定义要测试的菜单选项
            menu_tests = [
                ("9", "网络状态检查", None),
                ("10", "WireGuard连接测试", None),
                ("11", "代理连接测试", None),
                ("15", "查看Hosts文件", ["hosts", "文件"]),
                ("16", "查看WireGuard配置", None),
                ("18", "IPv6开关切换", None),
            ]
            
            # 测试每个选项
            for option_num, option_name, keywords in menu_tests:
                self.test_menu_option(option_num, option_name, keywords)
                time.sleep(1)  # 选项间等待
            
            # 测试特殊选项
            self.test_special_options()
            
            # 退出菜单
            self.log_message("测试完成，退出菜单...")
            self.send_menu_choice("0", wait_time=2)
            
            # 等待进程结束
            if self.menu_process:
                self.menu_process.terminate()
                self.menu_process.wait(timeout=5)
            
        except Exception as e:
            self.log_message(f"测试过程中发生错误: {e}", "ERROR")
        finally:
            # 确保进程被终止
            if self.menu_process and self.menu_process.poll() is None:
                self.menu_process.kill()
                self.menu_process.wait()
    
    def test_special_options(self):
        """测试特殊选项"""
        self.log_message("测试特殊功能选项...")
        
        # 测试配置加载（选项12）
        self.test_menu_option("12", "编辑配置", None, input_after="\x1b\x1b")  # ESC键模拟退出
        
        # 测试配置同步（选项8）
        self.test_menu_option("8", "配置同步", None)
        
        # 测试清空Hosts（选项14）
        self.test_menu_option("14", "清空Hosts文件", None, input_after="\n")
    
    def test_domain_functions(self):
        """测试域名相关功能"""
        self.log_message("测试域名解析功能...")
        
        # 创建测试域名文件
        test_domain_file = os.path.join(SCRIPT_DIR, "test_domains_menu.txt")
        with open(test_domain_file, 'w', encoding='utf-8') as f:
            f.write("cloudflare.com\ngoogle.com\n")
        
        try:
            # 测试域名解析（选项6）
            self.test_menu_option("6", "域名解析", None)
            
            # 测试更新Hosts（选项7）
            self.test_menu_option("7", "更新Hosts文件", None)
            
        finally:
            # 清理测试文件
            if os.path.exists(test_domain_file):
                os.remove(test_domain_file)
    
    def generate_test_report(self):
        """生成测试报告"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['success'])
        failed_tests = total_tests - passed_tests
        
        report = f"""
===========================================
AUTOVPN交互式菜单测试报告
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
            report += f"选项 {result['option']} - {status} - {result['name']} (耗时: {result['duration']:.2f}s)\n"
            if not result['success'] and result['error']:
                report += f"    错误: {result['error']}\n"
        
        report += "\n===========================================\n"
        
        # 保存报告到文件
        report_file = os.path.join(SCRIPT_DIR, "interactive_menu_test_report.txt")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        self.log_message(f"测试报告已保存到: {report_file}")
        return report
    
    def run_full_test(self):
        """运行完整测试"""
        self.log_message("开始AUTOVPN交互式菜单完整测试...")
        
        try:
            # 运行基础菜单测试
            self.run_menu_tests()
            
            # 测试域名功能
            self.test_domain_functions()
            
            # 生成测试报告
            report = self.generate_test_report()
            print(report)
            
            self.log_message("交互式菜单测试完成！")
            
        except Exception as e:
            self.log_message(f"测试失败: {e}", "ERROR")
            return False
        
        return True

def main():
    """主函数"""
    print("AUTOVPN交互式菜单自动测试工具")
    print("=" * 50)
    
    tester = InteractiveMenuTester()
    
    try:
        success = tester.run_full_test()
        
        # 统计结果
        total = len(tester.test_results)
        passed = sum(1 for r in tester.test_results if r['success'])
        
        print(f"\n测试完成! 通过率: {passed}/{total} ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 所有菜单功能测试通过!")
        else:
            print("⚠️  部分菜单功能测试失败，请查看详细报告")
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        return 1
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        return 1

if __name__ == "__main__":
    # 修复导入问题
    try:
        import queue
    except ImportError:
        import Queue as queue
    
    sys.exit(main())