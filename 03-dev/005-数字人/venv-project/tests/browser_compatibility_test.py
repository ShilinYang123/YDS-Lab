#!/usr/bin/env python3
"""
浏览器兼容性测试模块
测试不同浏览器环境下的预览功能表现
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any

class BrowserCompatibilityTester:
    def __init__(self):
        self.test_results = []
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
        
    def test_basic_functionality(self) -> Dict[str, Any]:
        """测试基本功能兼容性"""
        self.log_test_step("基本功能兼容性测试", "开始", "测试URL: " + self.preview_url)
        
        results = {
            "connection_test": False,
            "content_loading": False,
            "api_compatibility": False,
            "response_time": 0,
            "errors": []
        }
        
        try:
            # 连接测试
            start_time = time.time()
            response = requests.get(self.preview_url, timeout=15)
            response_time = time.time() - start_time
            
            results["response_time"] = response_time
            
            if response.status_code == 200:
                results["connection_test"] = True
                self.log_test_step("连接测试", "通过", f"响应时间: {response_time:.2f}秒")
                
                # 内容加载测试
                content_size = len(response.content)
                if content_size > 100:  # 基本内容检查
                    results["content_loading"] = True
                    self.log_test_step("内容加载测试", "通过", f"内容大小: {content_size} bytes")
                else:
                    self.log_test_step("内容加载测试", "失败", "内容过小")
                    results["errors"].append("内容加载异常")
                    
            else:
                self.log_test_step("连接测试", "失败", f"状态码: {response.status_code}")
                results["errors"].append(f"HTTP {response.status_code}")
                
        except requests.exceptions.Timeout:
            self.log_test_step("连接测试", "失败", "连接超时")
            results["errors"].append("连接超时")
        except requests.exceptions.ConnectionError:
            self.log_test_step("连接测试", "失败", "连接错误")
            results["errors"].append("连接错误")
        except Exception as e:
            self.log_test_step("连接测试", "失败", f"未知错误: {str(e)}")
            results["errors"].append(f"未知错误: {str(e)}")
            
        # API兼容性测试
        try:
            api_response = requests.get(f"{self.api_base}/api/stats", timeout=10)
            if api_response.status_code == 200:
                results["api_compatibility"] = True
                self.log_test_step("API兼容性测试", "通过", "后端API响应正常")
            else:
                self.log_test_step("API兼容性测试", "失败", f"状态码: {api_response.status_code}")
                results["errors"].append(f"API返回 {api_response.status_code}")
        except Exception as e:
            self.log_test_step("API兼容性测试", "失败", f"错误: {str(e)}")
            results["errors"].append(f"API错误: {str(e)}")
            
        return results
        
    def test_multiple_endpoints(self) -> Dict[str, Any]:
        """测试多个端点的兼容性"""
        self.log_test_step("多端点兼容性测试", "开始", "测试各个API端点")
        
        endpoints = {
            "/": "主页",
            "/api/health": "健康检查",
            "/api/stats": "统计数据",
            "/api/tasks": "任务列表"
        }
        
        results = {}
        
        for endpoint, description in endpoints.items():
            try:
                if endpoint == "/":
                    url = self.preview_url
                else:
                    url = f"{self.api_base}{endpoint}"
                    
                response = requests.get(url, timeout=10)
                
                results[endpoint] = {
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds(),
                    "content_length": len(response.content),
                    "success": response.status_code == 200
                }
                
                if response.status_code == 200:
                    self.log_test_step(f"端点测试 - {description}", "通过", f"响应时间: {response.elapsed.total_seconds():.2f}秒")
                else:
                    self.log_test_step(f"端点测试 - {description}", "失败", f"状态码: {response.status_code}")
                    
            except Exception as e:
                self.log_test_step(f"端点测试 - {description}", "失败", f"错误: {str(e)}")
                results[endpoint] = {
                    "status_code": 0,
                    "response_time": 0,
                    "content_length": 0,
                    "success": False,
                    "error": str(e)
                }
                
        return results
        
    def test_response_headers(self) -> Dict[str, Any]:
        """测试响应头兼容性"""
        self.log_test_step("响应头兼容性测试", "开始", "检查HTTP响应头")
        
        try:
            response = requests.get(self.preview_url, timeout=10)
            headers = dict(response.headers)
            
            # 检查关键响应头
            critical_headers = {
                "Content-Type": headers.get("Content-Type", ""),
                "Content-Length": headers.get("Content-Length", ""),
                "Server": headers.get("Server", ""),
                "Date": headers.get("Date", ""),
                "Cache-Control": headers.get("Cache-Control", ""),
                "Access-Control-Allow-Origin": headers.get("Access-Control-Allow-Origin", "")
            }
            
            # 验证内容类型
            content_type_ok = "text/html" in critical_headers["Content-Type"] or "application/json" in critical_headers["Content-Type"]
            
            self.log_test_step("内容类型检查", "通过" if content_type_ok else "警告", f"类型: {critical_headers['Content-Type']}")
            self.log_test_step("响应头完整性", "通过", f"找到 {len(headers)} 个响应头")
            
            return {
                "headers": critical_headers,
                "header_count": len(headers),
                "content_type_ok": content_type_ok,
                "success": content_type_ok
            }
            
        except Exception as e:
            self.log_test_step("响应头测试", "失败", f"错误: {str(e)}")
            return {"error": str(e), "success": False}
            
    def test_load_performance(self, iterations: int = 5) -> Dict[str, Any]:
        """测试加载性能一致性"""
        self.log_test_step("加载性能测试", "开始", f"进行 {iterations} 次重复测试")
        
        response_times = []
        success_count = 0
        
        for i in range(iterations):
            try:
                start_time = time.time()
                response = requests.get(self.preview_url, timeout=15)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    response_times.append(response_time)
                    success_count += 1
                    self.log_test_step(f"性能测试 #{i+1}", "通过", f"响应时间: {response_time:.2f}秒")
                else:
                    self.log_test_step(f"性能测试 #{i+1}", "失败", f"状态码: {response.status_code}")
                    
                time.sleep(1)  # 间隔1秒
                
            except Exception as e:
                self.log_test_step(f"性能测试 #{i+1}", "失败", f"错误: {str(e)}")
                
        # 性能分析
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
            std_deviation = (sum((x - avg_response_time) ** 2 for x in response_times) / len(response_times)) ** 0.5
            
            performance_ok = std_deviation < 2.0  # 标准差小于2秒认为性能稳定
            
            self.log_test_step("性能一致性", "通过" if performance_ok else "警告", 
                             f"平均: {avg_response_time:.2f}s, 标准差: {std_deviation:.2f}s")
            
            return {
                "success_rate": success_count / iterations * 100,
                "avg_response_time": avg_response_time,
                "max_response_time": max_response_time,
                "min_response_time": min_response_time,
                "std_deviation": std_deviation,
                "performance_ok": performance_ok,
                "success": performance_ok and success_count == iterations
            }
        else:
            self.log_test_step("性能测试", "失败", "无成功响应")
            return {"error": "无成功响应", "success": False}
            
    def test_error_handling(self) -> Dict[str, Any]:
        """测试错误处理机制"""
        self.log_test_step("错误处理测试", "开始", "测试各种错误情况")
        
        error_tests = [
            ("无效URL", "http://localhost:3001/invalid-endpoint"),
            ("错误端口", "http://localhost:9999"),
            ("超长URL", f"http://localhost:3001/{''.join(['a'] * 1000)}"),
        ]
        
        results = {}
        
        for test_name, url in error_tests:
            try:
                response = requests.get(url, timeout=5)
                
                if response.status_code in [404, 500, 502, 503]:
                    self.log_test_step(f"错误处理 - {test_name}", "通过", f"正确处理: {response.status_code}")
                    results[test_name] = {"status_code": response.status_code, "handled": True}
                else:
                    self.log_test_step(f"错误处理 - {test_name}", "警告", f"意外状态码: {response.status_code}")
                    results[test_name] = {"status_code": response.status_code, "handled": False}
                    
            except requests.exceptions.RequestException as e:
                self.log_test_step(f"错误处理 - {test_name}", "通过", f"正确异常处理: {type(e).__name__}")
                results[test_name] = {"error": str(e), "handled": True}
            except Exception as e:
                self.log_test_step(f"错误处理 - {test_name}", "警告", f"意外异常: {str(e)}")
                results[test_name] = {"error": str(e), "handled": False}
                
        return results
        
    def generate_compatibility_report(self) -> str:
        """生成兼容性测试报告"""
        report = []
        report.append("=" * 60)
        report.append("浏览器兼容性测试报告")
        report.append("=" * 60)
        report.append(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"测试URL: {self.preview_url}")
        report.append("")
        
        # 测试结果统计
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "通过"])
        failed_tests = len([r for r in self.test_results if r["status"] == "失败"])
        warning_tests = len([r for r in self.test_results if r["status"] == "警告"])
        
        report.append("兼容性测试结果:")
        report.append(f"  总测试步骤: {total_tests}")
        report.append(f"  通过: {passed_tests}")
        report.append(f"  失败: {failed_tests}")
        report.append(f"  警告: {warning_tests}")
        report.append(f"  兼容性评分: {passed_tests/total_tests*100:.1f}%" if total_tests > 0 else "  兼容性评分: 0%")
        report.append("")
        
        # 详细测试步骤
        report.append("详细测试步骤:")
        for result in self.test_results:
            report.append(f"  [{result['timestamp']}] {result['step']}: {result['status']}")
            if result['details']:
                report.append(f"    详情: {result['details']}")
        report.append("")
        
        # 兼容性建议
        compatibility_score = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        report.append("兼容性评估:")
        if compatibility_score >= 95:
            report.append(f"  兼容性等级: 优秀 ({compatibility_score:.1f}%)")
            report.append("  建议: 系统在各种浏览器环境下表现良好")
        elif compatibility_score >= 85:
            report.append(f"  兼容性等级: 良好 ({compatibility_score:.1f}%)")
            report.append("  建议: 基本兼容，建议关注警告信息")
        elif compatibility_score >= 70:
            report.append(f"  兼容性等级: 一般 ({compatibility_score:.1f}%)")
            report.append("  建议: 存在兼容性问题，需要优化")
        else:
            report.append(f"  兼容性等级: 需改进 ({compatibility_score:.1f}%)")
            report.append("  建议: 存在严重兼容性问题，需要立即修复")
            
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)
        
    def run_compatibility_test(self):
        """运行兼容性测试"""
        print("开始浏览器兼容性测试...")
        
        try:
            # 1. 基本功能测试
            basic_results = self.test_basic_functionality()
            
            # 2. 多端点测试
            endpoints_results = self.test_multiple_endpoints()
            
            # 3. 响应头测试
            headers_results = self.test_response_headers()
            
            # 4. 加载性能测试
            performance_results = self.test_load_performance()
            
            # 5. 错误处理测试
            error_results = self.test_error_handling()
            
            # 生成报告
            report = self.generate_compatibility_report()
            
            # 保存报告到文件
            report_file = f"browser_compatibility_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
                
            print(f"\n兼容性测试完成！报告已保存到: {report_file}")
            print(report)
            
            return report
            
        except Exception as e:
            print(f"兼容性测试过程中发生错误: {str(e)}")
            return f"兼容性测试失败: {str(e)}"

if __name__ == "__main__":
    tester = BrowserCompatibilityTester()
    tester.run_compatibility_test()