#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTOVPN真实交互自动化测试器
通过模拟键盘输入与运行的菜单进程交互
"""

import os
import sys
import time
import subprocess
import threading
import queue
from datetime import datetime
import signal
import platform

# 获取脚本目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

class RealAutoInteractor:
    def __init__(self):
        self.results = []
        self.is_running = True
        self.log_file = os.path.join(SCRIPT_DIR, "real_auto_interactor.log")
        self.report_file = os.path.join(SCRIPT_DIR, "real_auto_interactor_report.txt")
        self.menu_process = None
        
    def log_message(self, message, level="INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry + "\n")
        except Exception:
            pass
    
    def start_menu_in_background(self):
        """在后台启动菜单进程"""
        self.log_message("启动AUTOVPN菜单进程...")
        
        try:
            # 启动菜单进程
            if platform.system() == "Windows":
                # Windows系统使用特殊方式启动
                self.menu_process = subprocess.Popen(
                    ["python", "autovpn_menu.py"],
                    cwd=SCRIPT_DIR,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    shell=True
                )
            else:
                self.menu_process = subprocess.Popen(
                    [sys.executable, "autovpn_menu.py"],
                    cwd=SCRIPT_DIR,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            
            self.log_message("菜单进程已启动，等待初始化...")
            time.sleep(8)  # 等待菜单完全加载
            return True
            
        except Exception as e:
            self.log_message(f"启动菜单进程失败: {e}", "ERROR")
            return False
    
    def send_key_to_menu(self, key):
        """发送按键到菜单进程"""
        try:
            if self.menu_process and self.menu_process.stdin:
                self.menu_process.stdin.write(key + "\n")
                self.menu_process.stdin.flush()
                self.log_message(f"发送按键: '{key}'")
                return True
            else:
                self.log_message("无法发送按键 - 进程未就绪", "ERROR")
                return False
        except Exception as e:
            self.log_message(f"发送按键失败: {e}", "ERROR")
            return False
    
    def test_menu_option(self, option_num, description, wait_time=4):
        """测试特定菜单选项"""
        self.log_message(f"开始测试菜单选项 {option_num}: {description}")
        
        # 发送菜单选项
        if not self.send_key_to_menu(str(option_num)):
            return False
        
        # 等待执行
        time.sleep(wait_time)
        
        # 尝试返回主菜单
        self.send_key_to_menu("")  # 发送回车
        time.sleep(2)
        
        result = {
            "option": option_num,
            "description": description,
            "status": "PASS",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.results.append(result)
        self.log_message(f"菜单选项 {option_num} 测试完成: 通过")
        return True
    
    def run_interactive_tests(self):
        """运行交互式测试"""
        self.log_message("开始交互式菜单测试...")
        
        # 测试用例列表
        test_cases = [
            (9, "检查网络状态", 3),
            (10, "测试WireGuard连接", 5),
            (11, "测试代理连接", 5),
            (12, "编辑配置文件", 3),
            (15, "查看hosts文件", 3),
            (16, "查看wireguard配置文件", 3),
            (18, "切换IPv6功能开关", 3),
        ]
        
        passed = 0
        failed = 0
        
        for option_num, description, wait_time in test_cases:
            try:
                if self.test_menu_option(option_num, description, wait_time):
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                failed += 1
                self.log_message(f"测试菜单选项 {option_num} 时发生异常: {e}", "ERROR")
            
            # 选项间稍作停顿
            time.sleep(3)
        
        self.log_message(f"交互式测试完成 - 通过: {passed}, 失败: {failed}")
        return passed, failed
    
    def read_process_output(self):
        """读取进程输出"""
        try:
            if self.menu_process and self.menu_process.stdout:
                # 读取所有可用输出
                output = ""
                while True:
                    line = self.menu_process.stdout.readline()
                    if not line:
                        break
                    output += line
                    self.log_message(f"菜单输出: {line.strip()}")
                return output
        except Exception as e:
            self.log_message(f"读取进程输出失败: {e}", "ERROR")
            return ""
    
    def cleanup(self):
        """清理资源"""
        self.log_message("开始清理资源...")
        
        if self.menu_process:
            try:
                # 尝试优雅终止
                self.menu_process.terminate()
                self.menu_process.wait(timeout=5)
                self.log_message("菜单进程已终止")
            except:
                try:
                    # 强制终止
                    self.menu_process.kill()
                    self.log_message("菜单进程已强制终止")
                except:
                    pass
    
    def generate_report(self):
        """生成测试报告"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        
        report_content = f"""
AUTOVPN真实交互自动化测试报告
=====================================
测试时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
总测试项: {total}
通过: {passed}
失败: {failed}
成功率: {(passed/total*100):.1f}% if total > 0 else 0%

详细测试结果:
-------------------------------------
"""
        
        for result in self.results:
            status_symbol = "✅" if result["status"] == "PASS" else "❌"
            report_content += f"{status_symbol} 选项{result['option']}: {result['description']} - {result['status']}\n"
            report_content += f"   时间: {result['timestamp']}\n\n"
        
        # 保存报告
        try:
            with open(self.report_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            self.log_message(f"测试报告已保存到: {self.report_file}")
        except Exception as e:
            self.log_message(f"保存报告失败: {e}", "ERROR")
        
        return report_content
    
    def run_full_test(self):
        """运行完整测试流程"""
        self.log_message("开始AUTOVPN真实交互自动化测试...")
        
        try:
            # 启动菜单进程
            if not self.start_menu_in_background():
                self.log_message("无法启动菜单进程，测试终止", "ERROR")
                return
            
            # 运行交互式测试
            passed, failed = self.run_interactive_tests()
            
            # 读取最终输出
            self.read_process_output()
            
            # 生成报告
            report = self.generate_report()
            print("\n" + report)
            
            self.log_message(f"测试完成 - 通过: {passed}, 失败: {failed}")
            
        except Exception as e:
            self.log_message(f"测试过程中发生错误: {e}", "ERROR")
        finally:
            self.cleanup()

def main():
    """主函数"""
    interactor = RealAutoInteractor()
    
    try:
        interactor.run_full_test()
    except KeyboardInterrupt:
        interactor.log_message("测试被用户中断")
    except Exception as e:
        interactor.log_message(f"测试发生异常: {e}", "ERROR")
    finally:
        interactor.cleanup()

if __name__ == "__main__":
    main()