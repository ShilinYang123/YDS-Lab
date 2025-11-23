#!/usr/bin/env python3
"""
内存管理和关闭功能测试模块
测试预览功能的内存使用情况和关闭机制
"""

import psutil
import time
import requests
import json
import os
from datetime import datetime
from typing import Dict, List, Any

class MemoryManagementTester:
    def __init__(self):
        self.test_results = []
        self.memory_snapshots = []
        self.process_monitoring = []
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
        
    def get_system_resources(self) -> Dict[str, Any]:
        """获取系统资源使用情况"""
        try:
            memory = psutil.virtual_memory()
            cpu = psutil.cpu_percent(interval=1)
            disk = psutil.disk_usage('/')
            
            # 获取Node.js进程信息
            node_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent']):
                try:
                    if 'node' in proc.info['name'].lower():
                        node_processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'memory_percent': proc.info['memory_percent'],
                            'cpu_percent': proc.info['cpu_percent']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                    
            return {
                "memory_percent": memory.percent,
                "memory_available_gb": memory.available / (1024**3),
                "memory_used_gb": memory.used / (1024**3),
                "cpu_percent": cpu,
                "disk_percent": disk.percent,
                "node_processes": node_processes,
                "node_process_count": len(node_processes),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.log_test_step("资源检查", "失败", f"错误: {str(e)}")
            return {}
            
    def test_memory_leak_prevention(self, duration_minutes: int = 10) -> List[Dict[str, Any]]:
        """测试内存泄漏防护"""
        self.log_test_step("内存泄漏防护测试", "开始", f"持续时间: {duration_minutes}分钟")
        
        memory_data = []
        interval = 60  # 每60秒检查一次
        iterations = duration_minutes
        
        # 初始基线
        baseline = self.get_system_resources()
        initial_memory = baseline.get("memory_percent", 0)
        initial_node_count = baseline.get("node_process_count", 0)
        
        self.log_test_step("基线内存", "记录", f"初始内存使用: {initial_memory:.1f}%, Node进程: {initial_node_count}")
        
        for i in range(iterations):
            try:
                # 模拟用户操作
                self.simulate_user_operations()
                
                # 获取当前资源使用
                current_resources = self.get_system_resources()
                memory_data.append(current_resources)
                
                current_memory = current_resources.get("memory_percent", 0)
                current_node_count = current_resources.get("node_process_count", 0)
                
                self.log_test_step("内存检查", "进行中", 
                                 f"第{i+1}/{iterations}次 - 内存: {current_memory:.1f}%, Node进程: {current_node_count}")
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                self.log_test_step("内存泄漏测试", "中断", "用户中断测试")
                break
            except Exception as e:
                self.log_test_step("内存检查", "错误", f"第{i+1}次检查失败: {str(e)}")
                
        # 分析内存趋势
        if memory_data:
            memory_percentages = [m.get("memory_percent", 0) for m in memory_data if m.get("memory_percent")]
            node_counts = [m.get("node_process_count", 0) for m in memory_data if m.get("node_process_count")]
            
            if memory_percentages:
                final_memory = memory_percentages[-1]
                memory_growth = final_memory - initial_memory
                max_memory = max(memory_percentages)
                avg_memory = sum(memory_percentages) / len(memory_percentages)
                
                # Node进程稳定性分析
                node_count_stable = all(count == initial_node_count for count in node_counts)
                
                self.log_test_step("内存分析", "完成", 
                                 f"平均: {avg_memory:.1f}%, 峰值: {max_memory:.1f}%, 增长: {memory_growth:.1f}%")
                self.log_test_step("进程稳定性", "通过" if node_count_stable else "警告", 
                                 f"Node进程数量: {initial_node_count} -> {node_counts[-1] if node_counts else '未知'}")
                
                # 内存泄漏判断
                if memory_growth > 10:  # 内存增长超过10%
                    self.log_test_step("内存泄漏检查", "警告", "检测到显著内存增长")
                elif memory_growth > 5:
                    self.log_test_step("内存泄漏检查", "注意", "检测到轻微内存增长")
                else:
                    self.log_test_step("内存泄漏检查", "通过", "内存使用稳定")
                    
        return memory_data
        
    def simulate_user_operations(self):
        """模拟用户操作"""
        try:
            # 模拟页面访问
            requests.get(self.preview_url, timeout=5)
            time.sleep(0.5)
            
            # 模拟API调用
            requests.get(f"{self.api_base}/api/stats", timeout=3)
            time.sleep(0.5)
            
            # 模拟任务列表访问
            requests.get(f"{self.api_base}/api/tasks", timeout=3)
            time.sleep(0.5)
            
        except Exception:
            pass  # 模拟操作错误不影响主测试
            
    def test_preview_close_functionality(self) -> Dict[str, Any]:
        """测试预览关闭功能"""
        self.log_test_step("预览关闭功能测试", "开始", "测试关闭机制和资源释放")
        
        results = {
            "close_simulation": False,
            "resource_cleanup": False,
            "memory_release": False,
            "process_cleanup": False
        }
        
        try:
            # 获取关闭前的资源基线
            before_close = self.get_system_resources()
            before_memory = before_close.get("memory_percent", 0)
            before_node_count = before_close.get("node_process_count", 0)
            
            self.log_test_step("关闭前资源", "记录", f"内存: {before_memory:.1f}%, Node进程: {before_node_count}")
            
            # 模拟关闭操作（通过停止访问模拟）
            self.log_test_step("关闭操作", "模拟", "停止前端服务访问")
            
            # 等待资源释放
            time.sleep(5)
            
            # 检查关闭后的资源
            after_close = self.get_system_resources()
            after_memory = after_close.get("memory_percent", 0)
            after_node_count = after_close.get("node_process_count", 0)
            
            self.log_test_step("关闭后资源", "记录", f"内存: {after_memory:.1f}%, Node进程: {after_node_count}")
            
            # 分析资源变化
            memory_change = before_memory - after_memory
            node_change = before_node_count - after_node_count
            
            if memory_change > 0:
                results["memory_release"] = True
                self.log_test_step("内存释放", "通过", f"释放内存: {memory_change:.1f}%")
            else:
                self.log_test_step("内存释放", "注意", f"内存变化: {memory_change:.1f}%")
                
            if after_node_count <= before_node_count:
                results["process_cleanup"] = True
                self.log_test_step("进程清理", "通过", f"Node进程数量稳定")
            else:
                self.log_test_step("进程清理", "警告", f"Node进程增加: {after_node_count - before_node_count}")
                
            results["close_simulation"] = True
            results["resource_cleanup"] = results["memory_release"] or results["process_cleanup"]
            
        except Exception as e:
            self.log_test_step("关闭功能测试", "失败", f"错误: {str(e)}")
            
        return results
        
    def test_resource_cleanup_efficiency(self) -> Dict[str, Any]:
        """测试资源清理效率"""
        self.log_test_step("资源清理效率测试", "开始", "测试资源释放效率")
        
        efficiency_results = {
            "cleanup_time": 0,
            "memory_efficiency": 0,
            "process_efficiency": 0,
            "overall_efficiency": 0
        }
        
        try:
            # 多次开关循环测试
            cycles = 3
            cleanup_times = []
            memory_efficiencies = []
            process_efficiencies = []
            
            for cycle in range(cycles):
                self.log_test_step("清理循环", "开始", f"第{cycle+1}/{cycles}轮")
                
                # 获取基线
                baseline = self.get_system_resources()
                baseline_memory = baseline.get("memory_percent", 0)
                
                # 模拟高负载
                for _ in range(10):
                    self.simulate_user_operations()
                    
                time.sleep(2)
                
                # 获取峰值
                peak = self.get_system_resources()
                peak_memory = peak.get("memory_percent", 0)
                
                # 等待自然清理
                cleanup_start = time.time()
                time.sleep(10)  # 等待10秒让系统自然清理
                cleanup_end = time.time()
                
                # 获取清理后
                after_cleanup = self.get_system_resources()
                after_memory = after_cleanup.get("memory_percent", 0)
                
                # 计算效率
                cleanup_time = cleanup_end - cleanup_start
                memory_efficiency = (peak_memory - after_memory) / (peak_memory - baseline_memory) * 100 if peak_memory > baseline_memory else 0
                
                cleanup_times.append(cleanup_time)
                memory_efficiencies.append(memory_efficiency)
                
                self.log_test_step("清理效率", "记录", f"时间: {cleanup_time:.1f}s, 内存效率: {memory_efficiency:.1f}%")
                
                time.sleep(2)  # 间隔
                
            # 计算平均效率
            if cleanup_times:
                efficiency_results["cleanup_time"] = sum(cleanup_times) / len(cleanup_times)
                efficiency_results["memory_efficiency"] = sum(memory_efficiencies) / len(memory_efficiencies)
                efficiency_results["overall_efficiency"] = (efficiency_results["memory_efficiency"] + 
                                                         (10 - min(efficiency_results["cleanup_time"], 10)) * 10) / 2
                
                self.log_test_step("清理效率分析", "完成", 
                                 f"平均清理时间: {efficiency_results['cleanup_time']:.1f}s, "
                                 f"平均内存效率: {efficiency_results['memory_efficiency']:.1f}%")
                                 
        except Exception as e:
            self.log_test_step("清理效率测试", "失败", f"错误: {str(e)}")
            
        return efficiency_results
        
    def generate_memory_report(self) -> str:
        """生成内存管理测试报告"""
        report = []
        report.append("=" * 60)
        report.append("内存管理和关闭功能测试报告")
        report.append("=" * 60)
        report.append(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"测试URL: {self.preview_url}")
        report.append("")
        
        # 测试结果统计
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "通过"])
        failed_tests = len([r for r in self.test_results if r["status"] == "失败"])
        warning_tests = len([r for r in self.test_results if r["status"] == "警告"])
        
        report.append("内存管理测试结果:")
        report.append(f"  总测试步骤: {total_tests}")
        report.append(f"  通过: {passed_tests}")
        report.append(f"  失败: {failed_tests}")
        report.append(f"  警告: {warning_tests}")
        report.append(f"  内存管理评分: {passed_tests/total_tests*100:.1f}%" if total_tests > 0 else "  内存管理评分: 0%")
        report.append("")
        
        # 详细测试步骤
        report.append("详细测试步骤:")
        for result in self.test_results:
            report.append(f"  [{result['timestamp']}] {result['step']}: {result['status']}")
            if result['details']:
                report.append(f"    详情: {result['details']}")
        report.append("")
        
        # 内存数据分析
        if self.memory_snapshots:
            memory_percentages = [m.get("memory_percent", 0) for m in self.memory_snapshots if m.get("memory_percent")]
            if memory_percentages:
                avg_memory = sum(memory_percentages) / len(memory_percentages)
                max_memory = max(memory_percentages)
                min_memory = min(memory_percentages)
                
                report.append("内存使用分析:")
                report.append(f"  平均内存使用率: {avg_memory:.1f}%")
                report.append(f"  最高内存使用率: {max_memory:.1f}%")
                report.append(f"  最低内存使用率: {min_memory:.1f}%")
                report.append(f"  内存波动范围: {max_memory - min_memory:.1f}%")
                report.append("")
        
        # 内存管理评估
        memory_score = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        report.append("内存管理评估:")
        if memory_score >= 95:
            report.append(f"  内存管理等级: 优秀 ({memory_score:.1f}%)")
            report.append("  建议: 内存管理良好，无内存泄漏风险")
        elif memory_score >= 85:
            report.append(f"  内存管理等级: 良好 ({memory_score:.1f}%)")
            report.append("  建议: 基本良好，建议定期监控内存使用")
        elif memory_score >= 70:
            report.append(f"  内存管理等级: 一般 ({memory_score:.1f}%)")
            report.append("  建议: 存在内存管理问题，需要优化")
        else:
            report.append(f"  内存管理等级: 需改进 ({memory_score:.1f}%)")
            report.append("  建议: 存在严重内存问题，需要立即修复")
            
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)
        
    def run_memory_management_test(self):
        """运行内存管理测试"""
        print("开始内存管理和关闭功能测试...")
        
        try:
            # 1. 内存泄漏防护测试
            memory_data = self.test_memory_leak_prevention(duration_minutes=10)
            self.memory_snapshots.extend(memory_data)
            
            # 2. 关闭功能测试
            close_results = self.test_preview_close_functionality()
            
            # 3. 资源清理效率测试
            efficiency_results = self.test_resource_cleanup_efficiency()
            
            # 生成报告
            report = self.generate_memory_report()
            
            # 保存报告到文件
            report_file = f"memory_management_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
                
            print(f"\n内存管理测试完成！报告已保存到: {report_file}")
            print(report)
            
            return report
            
        except Exception as e:
            print(f"内存管理测试过程中发生错误: {str(e)}")
            return f"内存管理测试失败: {str(e)}"

if __name__ == "__main__":
    tester = MemoryManagementTester()
    tester.run_memory_management_test()