#!/usr/bin/env python3
"""
前端预览功能稳定性测试框架
测试预览窗口的打开机制、兼容性、内存管理等
"""

import time
import psutil
import requests
import json
import os
from datetime import datetime
from typing import Dict, List, Any
import threading
import signal
import sys

class PreviewStabilityTester:
    def __init__(self):
        self.test_results = []
        self.memory_snapshots = []
        self.error_logs = []
        self.start_time = None
        self.test_duration = 0
        self.preview_url = "http://localhost:3001"
        self.api_base = "http://localhost:8000"
        
    def log_test_step(self, step: str, status: str, details: str = ""):
        """记录测试步骤"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "step": step,
            "status": status,
            "details": details
        }
        self.test_results.append(log_entry)
        print(f"[{timestamp}] {step}: {status} - {details}")
        
    def check_system_resources(self) -> Dict[str, Any]:
        """检查系统资源使用情况"""
        try:
            memory = psutil.virtual_memory()
            cpu = psutil.cpu_percent(interval=1)
            
            return {
                "memory_percent": memory.percent,
                "memory_available_gb": memory.available / (1024**3),
                "cpu_percent": cpu,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.log_test_step("资源检查", "失败", f"错误: {str(e)}")
            return {}
            
    def test_preview_window_open(self) -> bool:
        """测试预览窗口打开机制"""
        self.log_test_step("预览窗口打开测试", "开始", "测试URL: " + self.preview_url)
        
        try:
            # 测试基本连接
            response = requests.get(self.preview_url, timeout=10)
            
            if response.status_code == 200:
                self.log_test_step("预览窗口打开测试", "通过", f"状态码: {response.status_code}")
                
                # 检查响应内容
                content_size = len(response.content)
                self.log_test_step("内容检查", "通过", f"页面大小: {content_size} bytes")
                
                # 检查关键元素
                if "数字员工" in response.text:
                    self.log_test_step("内容验证", "通过", "找到关键标题")
                else:
                    self.log_test_step("内容验证", "警告", "未找到预期标题")
                    
                return True
            else:
                self.log_test_step("预览窗口打开测试", "失败", f"状态码: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test_step("预览窗口打开测试", "失败", f"网络错误: {str(e)}")
            return False
        except Exception as e:
            self.log_test_step("预览窗口打开测试", "失败", f"未知错误: {str(e)}")
            return False
            
    def test_api_endpoints(self) -> Dict[str, bool]:
        """测试API端点稳定性"""
        endpoints = {
            "/api/health": "健康检查",
            "/api/stats": "统计数据",
            "/api/tasks": "任务列表"
        }
        
        results = {}
        
        for endpoint, description in endpoints.items():
            try:
                url = f"{self.api_base}{endpoint}"
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    self.log_test_step(f"API测试 - {description}", "通过", endpoint)
                    results[endpoint] = True
                else:
                    self.log_test_step(f"API测试 - {description}", "失败", f"{endpoint} - 状态码: {response.status_code}")
                    results[endpoint] = False
                    
            except Exception as e:
                self.log_test_step(f"API测试 - {description}", "失败", f"{endpoint} - 错误: {str(e)}")
                results[endpoint] = False
                
        return results
        
    def test_memory_stability(self, duration_minutes: int = 5) -> List[Dict[str, Any]]:
        """测试内存稳定性"""
        self.log_test_step("内存稳定性测试", "开始", f"持续时间: {duration_minutes}分钟")
        
        memory_data = []
        interval = 30  # 每30秒检查一次
        iterations = (duration_minutes * 60) // interval
        
        for i in range(iterations):
            try:
                # 获取内存快照
                memory_info = self.check_system_resources()
                memory_data.append(memory_info)
                
                # 模拟用户操作
                self.simulate_user_actions()
                
                self.log_test_step("内存检查", "进行中", f"第{i+1}/{iterations}次 - 内存使用: {memory_info.get('memory_percent', 0):.1f}%")
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                self.log_test_step("内存稳定性测试", "中断", "用户中断测试")
                break
            except Exception as e:
                self.log_test_step("内存稳定性测试", "错误", f"第{i+1}次检查失败: {str(e)}")
                
        # 分析内存趋势
        if memory_data:
            memory_percentages = [m.get("memory_percent", 0) for m in memory_data if m.get("memory_percent")]
            if memory_percentages:
                avg_memory = sum(memory_percentages) / len(memory_percentages)
                max_memory = max(memory_percentages)
                min_memory = min(memory_percentages)
                
                self.log_test_step("内存分析", "完成", f"平均: {avg_memory:.1f}%, 最高: {max_memory:.1f}%, 最低: {min_memory:.1f}%")
                
                # 检查内存泄漏
                if max_memory - min_memory > 20:  # 内存波动超过20%
                    self.log_test_step("内存泄漏检查", "警告", "检测到较大内存波动")
                else:
                    self.log_test_step("内存泄漏检查", "通过", "内存使用稳定")
                    
        return memory_data
        
    def simulate_user_actions(self):
        """模拟用户操作"""
        try:
            # 模拟页面访问
            requests.get(self.preview_url, timeout=3)
            
            # 模拟API调用
            requests.get(f"{self.api_base}/api/stats", timeout=2)
            
        except Exception:
            pass  # 模拟操作错误不影响主测试
            
    def test_long_duration_stability(self, hours: int = 1):
        """长时间稳定性测试"""
        self.log_test_step("长时间稳定性测试", "开始", f"持续时间: {hours}小时")
        
        start_time = time.time()
        duration_seconds = hours * 3600
        check_interval = 300  # 每5分钟检查一次
        
        stability_score = 0
        total_checks = 0
        
        while (time.time() - start_time) < duration_seconds:
            try:
                # 定期检查
                response = requests.get(self.preview_url, timeout=10)
                
                if response.status_code == 200:
                    stability_score += 1
                    
                total_checks += 1
                
                # 记录资源使用
                resources = self.check_system_resources()
                self.memory_snapshots.append(resources)
                
                elapsed = time.time() - start_time
                self.log_test_step("长时间测试", "进行中", f"已运行: {elapsed/3600:.1f}小时, 稳定性: {stability_score/total_checks*100:.1f}%")
                
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                self.log_test_step("长时间稳定性测试", "中断", "用户中断测试")
                break
            except Exception as e:
                total_checks += 1
                self.log_test_step("长时间稳定性测试", "错误", f"检查失败: {str(e)}")
                time.sleep(check_interval)
                
        final_stability = (stability_score / total_checks * 100) if total_checks > 0 else 0
        self.log_test_step("长时间稳定性测试", "完成", f"最终稳定性: {final_stability:.1f}%")
        
        return final_stability
        
    def generate_test_report(self) -> str:
        """生成测试报告"""
        report = []
        report.append("=" * 60)
        report.append("前端预览功能稳定性测试报告")
        report.append("=" * 60)
        report.append(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"测试URL: {self.preview_url}")
        report.append(f"测试持续时间: {self.test_duration}秒")
        report.append("")
        
        # 测试结果统计
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "通过"])
        failed_tests = len([r for r in self.test_results if r["status"] == "失败"])
        warning_tests = len([r for r in self.test_results if r["status"] == "警告"])
        
        report.append("测试结果统计:")
        report.append(f"  总测试步骤: {total_tests}")
        report.append(f"  通过: {passed_tests}")
        report.append(f"  失败: {failed_tests}")
        report.append(f"  警告: {warning_tests}")
        report.append(f"  通过率: {passed_tests/total_tests*100:.1f}%" if total_tests > 0 else "  通过率: 0%")
        report.append("")
        
        # 详细测试步骤
        report.append("详细测试步骤:")
        for result in self.test_results:
            report.append(f"  [{result['timestamp']}] {result['step']}: {result['status']}")
            if result['details']:
                report.append(f"    详情: {result['details']}")
        report.append("")
        
        # 内存使用分析
        if self.memory_snapshots:
            memory_percentages = [m.get("memory_percent", 0) for m in self.memory_snapshots if m.get("memory_percent")]
            if memory_percentages:
                avg_memory = sum(memory_percentages) / len(memory_percentages)
                max_memory = max(memory_percentages)
                
                report.append("内存使用分析:")
                report.append(f"  平均内存使用率: {avg_memory:.1f}%")
                report.append(f"  最高内存使用率: {max_memory:.1f}%")
                report.append(f"  内存波动范围: {max_memory - min(memory_percentages):.1f}%")
                report.append("")
        
        # 稳定性评估
        stability_score = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        report.append("稳定性评估:")
        if stability_score >= 95:
            report.append(f"  稳定性等级: 优秀 ({stability_score:.1f}%)")
        elif stability_score >= 85:
            report.append(f"  稳定性等级: 良好 ({stability_score:.1f}%)")
        elif stability_score >= 70:
            report.append(f"  稳定性等级: 一般 ({stability_score:.1f}%)")
        else:
            report.append(f"  稳定性等级: 需改进 ({stability_score:.1f}%)")
        report.append("")
        
        # 建议
        report.append("改进建议:")
        if stability_score < 95:
            report.append("  - 建议增加服务器资源配置")
            report.append("  - 考虑添加负载均衡")
            
        if warning_tests > 0:
            report.append("  - 关注警告信息，及时处理潜在问题")
            
        if failed_tests > 0:
            report.append("  - 修复失败的测试用例")
            report.append("  - 检查网络连接和服务器状态")
        else:
            report.append("  - 系统运行稳定，建议定期监控")
            
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)
        
    def run_comprehensive_test(self):
        """运行综合稳定性测试"""
        print("开始前端预览功能稳定性测试...")
        self.start_time = time.time()
        
        try:
            # 1. 基础连接测试
            self.test_preview_window_open()
            
            # 2. API端点测试
            self.test_api_endpoints()
            
            # 3. 内存稳定性测试（5分钟）
            memory_data = self.test_memory_stability(duration_minutes=5)
            self.memory_snapshots.extend(memory_data)
            
            # 4. 长时间稳定性测试（30分钟）
            stability_score = self.test_long_duration_stability(hours=0.5)
            
            self.test_duration = time.time() - self.start_time
            
            # 生成报告
            report = self.generate_test_report()
            
            # 保存报告到文件
            report_file = f"preview_stability_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
                
            print(f"\n测试完成！报告已保存到: {report_file}")
            print(report)
            
            return report
            
        except KeyboardInterrupt:
            print("\n测试被用户中断")
            return "测试被中断"
        except Exception as e:
            print(f"测试过程中发生错误: {str(e)}")
            return f"测试失败: {str(e)}"

def main():
    """主函数"""
    tester = PreviewStabilityTester()
    
    # 设置信号处理
    def signal_handler(sig, frame):
        print('\n正在停止测试...')
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    
    # 运行测试
    report = tester.run_comprehensive_test()
    
    return report

if __name__ == "__main__":
    main()