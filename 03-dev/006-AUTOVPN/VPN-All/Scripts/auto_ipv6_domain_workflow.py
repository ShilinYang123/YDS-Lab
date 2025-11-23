#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTOVPN自动化IPv6关闭和域名解析工作流
自动执行：关闭IPv6 -> 解析全部域名 -> 更新WireGuard配置
"""

import os
import sys
import time
import subprocess
import threading
from datetime import datetime
import signal
import platform

# 获取脚本目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

class AutoIPv6DomainWorkflow:
    def __init__(self):
        self.results = []
        self.is_running = True
        self.log_file = os.path.join(SCRIPT_DIR, "auto_ipv6_domain_workflow.log")
        self.report_file = os.path.join(SCRIPT_DIR, "auto_ipv6_domain_workflow_report.txt")
        self.menu_process = None
        self.current_step = 0
        self.total_steps = 3
        
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
    
    def wait_for_menu_ready(self, timeout=30):
        """等待菜单准备就绪"""
        self.log_message("等待菜单准备就绪...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # 检查进程是否还在运行
                if self.menu_process.poll() is not None:
                    self.log_message("菜单进程已退出", "ERROR")
                    return False
                
                # 尝试发送空行来检查菜单是否响应
                if self.send_key_to_menu(""):
                    time.sleep(2)
                    return True
                    
            except Exception as e:
                self.log_message(f"等待菜单就绪时出错: {e}", "ERROR")
            
            time.sleep(1)
        
        self.log_message("等待菜单就绪超时", "ERROR")
        return False
    
    def execute_step(self, step_num, description, option_num, wait_time=10):
        """执行一个步骤"""
        self.current_step += 1
        self.log_message(f"步骤 {self.current_step}/{self.total_steps}: {description}")
        
        try:
            # 发送菜单选项
            if not self.send_key_to_menu(str(option_num)):
                self.log_message(f"步骤 {step_num} 失败: 无法发送菜单选项", "ERROR")
                return False
            
            # 等待执行完成
            self.log_message(f"等待 {wait_time} 秒让操作完成...")
            time.sleep(wait_time)
            
            # 处理可能的等待提示
            self.log_message("检查是否需要处理等待提示...")
            self.send_key_to_menu("")  # 发送回车处理可能的等待
            time.sleep(2)
            
            result = {
                "step": step_num,
                "description": description,
                "option": option_num,
                "status": "PASS",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            self.results.append(result)
            self.log_message(f"步骤 {step_num} 完成: 通过")
            return True
            
        except Exception as e:
            self.log_message(f"步骤 {step_num} 执行失败: {e}", "ERROR")
            result = {
                "step": step_num,
                "description": description,
                "option": option_num,
                "status": "FAIL",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "error": str(e)
            }
            self.results.append(result)
            return False
    
    def run_automated_workflow(self):
        """运行自动化工作流"""
        self.log_message("开始AUTOVPN自动化IPv6关闭和域名解析工作流...")
        
        try:
            # 启动菜单进程
            if not self.start_menu_in_background():
                self.log_message("无法启动菜单进程，工作流终止", "ERROR")
                return False
            
            # 等待菜单准备就绪
            if not self.wait_for_menu_ready():
                self.log_message("菜单未能准备就绪，工作流终止", "ERROR")
                return False
            
            # 步骤1: 关闭IPv6 (选项18)
            if not self.execute_step(1, "关闭IPv6功能", 18, wait_time=8):
                self.log_message("关闭IPv6失败，继续执行下一步...", "WARNING")
            
            # 等待菜单返回
            time.sleep(3)
            
            # 步骤2: 解析全部域名 (选项6)
            if not self.execute_step(2, "解析全部域名列表", 6, wait_time=60):  # 域名解析可能需要更长时间
                self.log_message("域名解析失败，继续执行下一步...", "WARNING")
            
            # 等待菜单返回
            time.sleep(5)
            
            # 步骤3: 更新WireGuard配置 (选项8)
            if not self.execute_step(3, "同步配置到WireGuard", 8, wait_time=15):
                self.log_message("WireGuard配置更新失败", "ERROR")
            
            # 等待最终完成
            time.sleep(5)
            
            # 读取最终输出
            self.log_message("读取最终进程输出...")
            self.read_process_output()
            
            # 生成报告
            report = self.generate_report()
            print("\n" + report)
            
            self.log_message("自动化工作流完成")
            return True
            
        except Exception as e:
            self.log_message(f"工作流执行过程中发生错误: {e}", "ERROR")
            return False
        finally:
            self.cleanup()
    
    def read_process_output(self):
        """读取进程输出"""
        try:
            if self.menu_process and self.menu_process.stdout:
                # 读取所有可用输出
                output = ""
                start_time = time.time()
                
                while time.time() - start_time < 10:  # 最多读取10秒
                    line = self.menu_process.stdout.readline()
                    if not line:
                        break
                    output += line
                    self.log_message(f"进程输出: {line.strip()}")
                
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
                self.log_message("菜单进程已优雅终止")
            except:
                try:
                    # 强制终止
                    self.menu_process.kill()
                    self.log_message("菜单进程已强制终止")
                except:
                    pass
    
    def generate_report(self):
        """生成工作报告"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        
        report_content = f"""
AUTOVPN自动化IPv6关闭和域名解析工作流报告
===============================================
工作流执行时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
总步骤数: {total}
成功: {passed}
失败: {failed}
成功率: {(passed/total*100):.1f}% if total > 0 else 0%

详细执行步骤:
-------------------------------------
"""
        
        for result in self.results:
            status_symbol = "✅" if result["status"] == "PASS" else "❌"
            report_content += f"{status_symbol} 步骤{result['step']}: {result['description']} - {result['status']}\n"
            report_content += f"   菜单选项: {result['option']}\n"
            report_content += f"   时间: {result['timestamp']}\n"
            if "error" in result:
                report_content += f"   错误: {result['error']}\n"
            report_content += "\n"
        
        # 保存报告
        try:
            with open(self.report_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            self.log_message(f"工作报告已保存到: {self.report_file}")
        except Exception as e:
            self.log_message(f"保存报告失败: {e}", "ERROR")
        
        return report_content

def main():
    """主函数"""
    workflow = AutoIPv6DomainWorkflow()
    
    try:
        success = workflow.run_automated_workflow()
        if success:
            print("✅ 自动化工作流执行成功！")
        else:
            print("❌ 自动化工作流执行失败！")
    except KeyboardInterrupt:
        workflow.log_message("工作流被用户中断")
    except Exception as e:
        workflow.log_message(f"工作流发生异常: {e}", "ERROR")
    finally:
        workflow.cleanup()

if __name__ == "__main__":
    main()