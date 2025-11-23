import pytest
import asyncio
import httpx
import json
from datetime import datetime, timedelta
import time
import psutil
import requests
from typing import Dict, List, Optional
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SystemTestSuite:
    """数字员工系统测试套件"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        self.test_results = {
            "functional": {"passed": 0, "failed": 0, "total": 0},
            "performance": {"passed": 0, "failed": 0, "total": 0},
            "security": {"passed": 0, "failed": 0, "total": 0},
            "compatibility": {"passed": 0, "failed": 0, "total": 0},
            "ux": {"passed": 0, "failed": 0, "total": 0}
        }
        self.defects = []
        self.start_time = None
        
    def log_test_result(self, test_type: str, test_name: str, passed: bool, details: str = ""):
        """记录测试结果"""
        self.test_results[test_type]["total"] += 1
        if passed:
            self.test_results[test_type]["passed"] += 1
            logger.info(f"✅ {test_name} - 通过")
        else:
            self.test_results[test_type]["failed"] += 1
            logger.error(f"❌ {test_name} - 失败: {details}")
            self.defects.append({
                "test_type": test_type,
                "test_name": test_name,
                "severity": self._determine_severity(test_name),
                "details": details,
                "timestamp": datetime.now().isoformat()
            })
    
    def _determine_severity(self, test_name: str) -> str:
        """确定缺陷严重程度"""
        if "critical" in test_name.lower() or "阻塞" in test_name:
            return "P0 - 阻塞性"
        elif "major" in test_name.lower() or "严重" in test_name:
            return "P1 - 严重"
        elif "minor" in test_name.lower() or "一般" in test_name:
            return "P2 - 一般"
        else:
            return "P3 - 轻微"

    # ==================== 功能测试 ====================
    
    def test_api_health_check(self):
        """测试API健康检查"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.log_test_result("functional", "API健康检查", True)
                    return True
                else:
                    self.log_test_result("functional", "API健康检查", False, f"状态异常: {data}")
                    return False
            else:
                self.log_test_result("functional", "API健康检查", False, f"HTTP状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test_result("functional", "API健康检查", False, f"异常: {str(e)}")
            return False
    
    def test_api_root_endpoint(self):
        """测试API根端点"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "version" in data:
                    self.log_test_result("functional", "API根端点", True)
                    return True
                else:
                    self.log_test_result("functional", "API根端点", False, f"响应格式错误: {data}")
                    return False
            else:
                self.log_test_result("functional", "API根端点", False, f"HTTP状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test_result("functional", "API根端点", False, f"异常: {str(e)}")
            return False
    
    def test_task_creation(self):
        """测试任务创建功能"""
        test_task = {
            "name": "测试任务-功能测试",
            "description": "这是一个自动化测试任务",
            "task_type": "full_pipeline",
            "input_text": "你好，这是一个测试文本",
            "is_public": False
        }
        
        try:
            response = requests.post(f"{self.base_url}/api/tasks", json=test_task, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if data.get("id") and data.get("name") == test_task["name"]:
                    self.log_test_result("functional", "任务创建功能", True)
                    return data["id"]
                else:
                    self.log_test_result("functional", "任务创建功能", False, f"响应数据错误: {data}")
                    return None
            else:
                self.log_test_result("functional", "任务创建功能", False, f"HTTP状态码: {response.status_code}")
                return None
        except Exception as e:
            self.log_test_result("functional", "任务创建功能", False, f"异常: {str(e)}")
            return None
    
    def test_task_list_retrieval(self):
        """测试任务列表获取功能"""
        try:
            response = requests.get(f"{self.base_url}/api/tasks", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test_result("functional", "任务列表获取", True)
                    return True
                else:
                    self.log_test_result("functional", "任务列表获取", False, f"响应格式错误: {data}")
                    return False
            else:
                self.log_test_result("functional", "任务列表获取", False, f"HTTP状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test_result("functional", "任务列表获取", False, f"异常: {str(e)}")
            return False
    
    def test_task_detail_retrieval(self, task_id: str):
        """测试任务详情获取功能"""
        try:
            response = requests.get(f"{self.base_url}/api/tasks/{task_id}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("id") == task_id:
                    self.log_test_result("functional", "任务详情获取", True)
                    return True
                else:
                    self.log_test_result("functional", "任务详情获取", False, f"任务ID不匹配: {data}")
                    return False
            elif response.status_code == 404:
                self.log_test_result("functional", "任务详情获取", False, "任务不存在")
                return False
            else:
                self.log_test_result("functional", "任务详情获取", False, f"HTTP状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test_result("functional", "任务详情获取", False, f"异常: {str(e)}")
            return False
    
    def test_task_cancellation(self, task_id: str):
        """测试任务取消功能"""
        try:
            response = requests.post(f"{self.base_url}/api/tasks/{task_id}/cancel", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "message" in data:
                    self.log_test_result("functional", "任务取消功能", True)
                    return True
                else:
                    self.log_test_result("functional", "任务取消功能", False, f"响应格式错误: {data}")
                    return False
            else:
                self.log_test_result("functional", "任务取消功能", False, f"HTTP状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test_result("functional", "任务取消功能", False, f"异常: {str(e)}")
            return False
    
    def test_statistics_endpoint(self):
        """测试统计信息端点"""
        try:
            response = requests.get(f"{self.base_url}/api/stats", timeout=10)
            if response.status_code == 200:
                data = response.json()
                required_fields = ["total_tasks", "pending_tasks", "processing_tasks", "completed_tasks", "failed_tasks", "success_rate"]
                if all(field in data for field in required_fields):
                    self.log_test_result("functional", "统计信息端点", True)
                    return True
                else:
                    self.log_test_result("functional", "统计信息端点", False, f"缺少必要字段: {data}")
                    return False
            else:
                self.log_test_result("functional", "统计信息端点", False, f"HTTP状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test_result("functional", "统计信息端点", False, f"异常: {str(e)}")
            return False
    
    def test_queue_status_endpoint(self):
        """测试队列状态端点"""
        try:
            response = requests.get(f"{self.base_url}/api/queue/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                required_fields = ["queue_length", "processing_tasks", "timestamp"]
                if all(field in data for field in required_fields):
                    self.log_test_result("functional", "队列状态端点", True)
                    return True
                else:
                    self.log_test_result("functional", "队列状态端点", False, f"缺少必要字段: {data}")
                    return False
            else:
                self.log_test_result("functional", "队列状态端点", False, f"HTTP状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test_result("functional", "队列状态端点", False, f"异常: {str(e)}")
            return False
    
    def test_boundary_conditions(self):
        """测试边界条件"""
        # 测试空任务名称
        empty_name_task = {
            "name": "",
            "task_type": "full_pipeline",
            "input_text": "测试文本"
        }
        
        try:
            response = requests.post(f"{self.base_url}/api/tasks", json=empty_name_task, timeout=10)
            if response.status_code == 422:  # 应该返回验证错误
                self.log_test_result("functional", "边界条件-空任务名称", True)
            else:
                self.log_test_result("functional", "边界条件-空任务名称", False, f"期望422，实际: {response.status_code}")
        except Exception as e:
            self.log_test_result("functional", "边界条件-空任务名称", False, f"异常: {str(e)}")
        
        # 测试超长任务名称
        long_name_task = {
            "name": "测试任务" + "测" * 200,  # 超长的任务名称
            "task_type": "full_pipeline",
            "input_text": "测试文本"
        }
        
        try:
            response = requests.post(f"{self.base_url}/api/tasks", json=long_name_task, timeout=10)
            if response.status_code in [200, 422]:  # 应该正常处理或返回验证错误
                self.log_test_result("functional", "边界条件-超长任务名称", True)
            else:
                self.log_test_result("functional", "边界条件-超长任务名称", False, f"意外状态码: {response.status_code}")
        except Exception as e:
            self.log_test_result("functional", "边界条件-超长任务名称", False, f"异常: {str(e)}")
    
    def test_invalid_task_id(self):
        """测试无效任务ID处理"""
        invalid_id = "invalid-task-id-12345"
        try:
            response = requests.get(f"{self.base_url}/api/tasks/{invalid_id}", timeout=10)
            if response.status_code == 404:
                self.log_test_result("functional", "无效任务ID处理", True)
                return True
            else:
                self.log_test_result("functional", "无效任务ID处理", False, f"期望404，实际: {response.status_code}")
                return False
        except Exception as e:
            self.log_test_result("functional", "无效任务ID处理", False, f"异常: {str(e)}")
            return False

    # ==================== 性能测试 ====================
    
    def test_api_response_time(self):
        """测试API响应时间"""
        test_cases = [
            ("/", "根端点"),
            ("/health", "健康检查"),
            ("/api/tasks", "任务列表"),
            ("/api/stats", "统计信息"),
            ("/api/queue/status", "队列状态")
        ]
        
        for endpoint, name in test_cases:
            try:
                start_time = time.time()
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # 转换为毫秒
                
                if response_time <= 500:  # 要求响应时间 ≤ 500ms
                    self.log_test_result("performance", f"API响应时间-{name}", True, f"{response_time:.2f}ms")
                else:
                    self.log_test_result("performance", f"API响应时间-{name}", False, f"{response_time:.2f}ms (超过500ms)")
            except Exception as e:
                self.log_test_result("performance", f"API响应时间-{name}", False, f"异常: {str(e)}")
    
    def test_concurrent_api_calls(self):
        """测试并发API调用"""
        import threading
        
        results = []
        errors = []
        
        def make_api_call():
            try:
                response = requests.get(f"{self.base_url}/api/tasks", timeout=10)
                if response.status_code == 200:
                    results.append("success")
                else:
                    errors.append(f"HTTP {response.status_code}")
            except Exception as e:
                errors.append(str(e))
        
        # 启动10个并发线程
        threads = []
        for i in range(10):
            thread = threading.Thread(target=make_api_call)
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        success_rate = len(results) / 10 * 100
        if success_rate >= 90:  # 要求成功率 ≥ 90%
            self.log_test_result("performance", "并发API调用", True, f"成功率: {success_rate:.1f}%")
        else:
            self.log_test_result("performance", "并发API调用", False, f"成功率: {success_rate:.1f}% (低于90%)")
    
    def test_memory_usage(self):
        """测试内存使用情况"""
        try:
            # 获取当前Python进程的内存使用
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024  # 转换为MB
            
            if memory_mb <= 500:  # 要求内存使用 ≤ 500MB
                self.log_test_result("performance", "内存使用", True, f"{memory_mb:.2f}MB")
            else:
                self.log_test_result("performance", "内存使用", False, f"{memory_mb:.2f}MB (超过500MB)")
        except Exception as e:
            self.log_test_result("performance", "内存使用", False, f"异常: {str(e)}")
    
    def test_cpu_usage(self):
        """测试CPU使用情况"""
        try:
            # 获取CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            if cpu_percent <= 80:  # 要求CPU使用率 ≤ 80%
                self.log_test_result("performance", "CPU使用", True, f"{cpu_percent:.1f}%")
            else:
                self.log_test_result("performance", "CPU使用", False, f"{cpu_percent:.1f}% (超过80%)")
        except Exception as e:
            self.log_test_result("performance", "CPU使用", False, f"异常: {str(e)}")

    # ==================== 安全测试 ====================
    
    def test_sql_injection_prevention(self):
        """测试SQL注入防护"""
        malicious_input = "'; DROP TABLE tasks; --"
        test_task = {
            "name": malicious_input,
            "task_type": "full_pipeline",
            "input_text": "测试文本"
        }
        
        try:
            response = requests.post(f"{self.base_url}/api/tasks", json=test_task, timeout=10)
            if response.status_code in [200, 422]:  # 应该正常处理或返回验证错误
                # 检查任务是否被创建
                if response.status_code == 200:
                    data = response.json()
                    task_id = data.get("id")
                    if task_id:
                        # 验证任务没有被恶意执行
                        detail_response = requests.get(f"{self.base_url}/api/tasks/{task_id}", timeout=10)
                        if detail_response.status_code == 200:
                            self.log_test_result("security", "SQL注入防护", True)
                            # 清理测试任务
                            requests.delete(f"{self.base_url}/api/tasks/{task_id}", timeout=10)
                        else:
                            self.log_test_result("security", "SQL注入防护", False, "无法验证任务状态")
                    else:
                        self.log_test_result("security", "SQL注入防护", False, "未返回任务ID")
                else:
                    self.log_test_result("security", "SQL注入防护", True, "输入被正确验证")
            else:
                self.log_test_result("security", "SQL注入防护", False, f"意外状态码: {response.status_code}")
        except Exception as e:
            self.log_test_result("security", "SQL注入防护", False, f"异常: {str(e)}")
    
    def test_xss_prevention(self):
        """测试XSS防护"""
        xss_payload = "<script>alert('XSS')</script>"
        test_task = {
            "name": "测试任务",
            "description": xss_payload,
            "task_type": "full_pipeline",
            "input_text": "测试文本"
        }
        
        try:
            response = requests.post(f"{self.base_url}/api/tasks", json=test_task, timeout=10)
            if response.status_code == 200:
                data = response.json()
                task_id = data.get("id")
                if task_id:
                    # 检查返回的数据是否被正确转义
                    detail_response = requests.get(f"{self.base_url}/api/tasks/{task_id}", timeout=10)
                    if detail_response.status_code == 200:
                        task_data = detail_response.json()
                        description = task_data.get("description", "")
                        if "<script>" not in description or "&lt;script&gt;" in description:
                            self.log_test_result("security", "XSS防护", True)
                        else:
                            self.log_test_result("security", "XSS防护", False, "XSS payload未被转义")
                        # 清理测试任务
                        requests.delete(f"{self.base_url}/api/tasks/{task_id}", timeout=10)
                    else:
                        self.log_test_result("security", "XSS防护", False, "无法获取任务详情")
                else:
                    self.log_test_result("security", "XSS防护", False, "未返回任务ID")
            else:
                self.log_test_result("security", "XSS防护", False, f"HTTP状态码: {response.status_code}")
        except Exception as e:
            self.log_test_result("security", "XSS防护", False, f"异常: {str(e)}")
    
    def test_authentication_bypass(self):
        """测试认证绕过防护"""
        # 尝试访问需要认证的端点（假设存在）
        protected_endpoints = [
            "/api/admin/users",
            "/api/admin/config",
            "/api/internal/status"
        ]
        
        for endpoint in protected_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                if response.status_code == 404:  # 端点不存在是正常的
                    self.log_test_result("security", f"认证绕过-{endpoint}", True, "端点不存在")
                elif response.status_code == 401:  # 需要认证
                    self.log_test_result("security", f"认证绕过-{endpoint}", True, "正确要求认证")
                elif response.status_code == 403:  # 无权限
                    self.log_test_result("security", f"认证绕过-{endpoint}", True, "正确拒绝访问")
                else:
                    self.log_test_result("security", f"认证绕过-{endpoint}", False, f"意外状态码: {response.status_code}")
            except Exception as e:
                self.log_test_result("security", f"认证绕过-{endpoint}", False, f"异常: {str(e)}")
    
    def test_data_validation(self):
        """测试数据验证机制"""
        invalid_inputs = [
            {"name": None, "task_type": "full_pipeline"},  # None值
            {"name": 123, "task_type": "full_pipeline"},   # 数字类型
            {"name": "", "task_type": "invalid_type"},     # 空字符串和无效类型
            {"task_type": "full_pipeline"},                 # 缺少必填字段
        ]
        
        for i, invalid_input in enumerate(invalid_inputs):
            try:
                response = requests.post(f"{self.base_url}/api/tasks", json=invalid_input, timeout=10)
                if response.status_code == 422:  # 应该返回验证错误
                    self.log_test_result("security", f"数据验证-无效输入{i+1}", True)
                else:
                    self.log_test_result("security", f"数据验证-无效输入{i+1}", False, f"期望422，实际: {response.status_code}")
            except Exception as e:
                self.log_test_result("security", f"数据验证-无效输入{i+1}", False, f"异常: {str(e)}")

    # ==================== 兼容性测试 ====================
    
    def test_api_content_type(self):
        """测试API内容类型兼容性"""
        headers_list = [
            {"Content-Type": "application/json"},
            {"Content-Type": "application/json; charset=utf-8"},
            {"Accept": "application/json"},
            {"Accept": "application/json, text/plain"},
        ]
        
        test_task = {
            "name": "兼容性测试任务",
            "task_type": "full_pipeline",
            "input_text": "测试文本"
        }
        
        for i, headers in enumerate(headers_list):
            try:
                response = requests.post(f"{self.base_url}/api/tasks", json=test_task, headers=headers, timeout=10)
                if response.status_code == 200:
                    self.log_test_result("compatibility", f"API内容类型-场景{i+1}", True)
                else:
                    self.log_test_result("compatibility", f"API内容类型-场景{i+1}", False, f"HTTP状态码: {response.status_code}")
            except Exception as e:
                self.log_test_result("compatibility", f"API内容类型-场景{i+1}", False, f"异常: {str(e)}")
    
    def test_cors_headers(self):
        """测试CORS跨域支持"""
        try:
            # 发送OPTIONS预检请求
            response = requests.options(f"{self.base_url}/api/tasks", timeout=10)
            if response.status_code == 200:
                cors_headers = {
                    "Access-Control-Allow-Origin",
                    "Access-Control-Allow-Methods",
                    "Access-Control-Allow-Headers"
                }
                if all(header in response.headers for header in cors_headers):
                    self.log_test_result("compatibility", "CORS跨域支持", True)
                else:
                    missing = cors_headers - set(response.headers.keys())
                    self.log_test_result("compatibility", "CORS跨域支持", False, f"缺少CORS头: {missing}")
            else:
                self.log_test_result("compatibility", "CORS跨域支持", False, f"OPTIONS请求状态码: {response.status_code}")
        except Exception as e:
            self.log_test_result("compatibility", "CORS跨域支持", False, f"异常: {str(e)}")
    
    def test_json_encoding(self):
        """测试JSON编码兼容性"""
        test_data = {
            "name": "Unicode测试任务",
            "description": "测试中文支持：这是一个测试任务",
            "task_type": "full_pipeline",
            "input_text": "测试Unicode字符：你好世界 🌍 Ñoël"
        }
        
        try:
            response = requests.post(f"{self.base_url}/api/tasks", json=test_data, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("name") == test_data["name"]:
                    self.log_test_result("compatibility", "JSON编码兼容性", True)
                else:
                    self.log_test_result("compatibility", "JSON编码兼容性", False, f"Unicode字符处理错误")
            else:
                self.log_test_result("compatibility", "JSON编码兼容性", False, f"HTTP状态码: {response.status_code}")
        except Exception as e:
            self.log_test_result("compatibility", "JSON编码兼容性", False, f"异常: {str(e)}")

    # ==================== 用户体验测试 ====================
    
    def test_error_message_clarity(self):
        """测试错误消息清晰度"""
        test_cases = [
            ("/api/tasks/invalid-id", "无效任务ID"),
            ("/api/nonexistent-endpoint", "不存在端点"),
            ("", "根路径")
        ]
        
        for endpoint, description in test_cases:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                if response.status_code != 200:
                    data = response.json()
                    # 检查是否有清晰的错误消息
                    if "detail" in data or "message" in data or "error" in data:
                        self.log_test_result("ux", f"错误消息清晰度-{description}", True)
                    else:
                        self.log_test_result("ux", f"错误消息清晰度-{description}", False, "缺少错误消息")
                else:
                    self.log_test_result("ux", f"错误消息清晰度-{description}", True, "端点正常访问")
            except Exception as e:
                self.log_test_result("ux", f"错误消息清晰度-{description}", False, f"异常: {str(e)}")
    
    def test_api_documentation_accessibility(self):
        """测试API文档可访问性"""
        try:
            response = requests.get(f"{self.base_url}/docs", timeout=10)
            if response.status_code == 200:
                content = response.text
                if "FastAPI" in content and "swagger" in content.lower():
                    self.log_test_result("ux", "API文档可访问性", True)
                else:
                    self.log_test_result("ux", "API文档可访问性", False, "文档内容不完整")
            else:
                self.log_test_result("ux", "API文档可访问性", False, f"HTTP状态码: {response.status_code}")
        except Exception as e:
            self.log_test_result("ux", "API文档可访问性", False, f"异常: {str(e)}")
    
    def test_response_consistency(self):
        """测试响应一致性"""
        try:
            # 多次调用同一个端点，检查响应格式一致性
            responses = []
            for i in range(3):
                response = requests.get(f"{self.base_url}/api/stats", timeout=10)
                if response.status_code == 200:
                    responses.append(response.json())
                else:
                    self.log_test_result("ux", "响应一致性", False, f"第{i+1}次调用失败")
                    return
            
            # 检查响应格式是否一致
            if len(responses) == 3:
                first_keys = set(responses[0].keys())
                consistent = all(set(response.keys()) == first_keys for response in responses[1:])
                
                if consistent:
                    self.log_test_result("ux", "响应一致性", True)
                else:
                    self.log_test_result("ux", "响应一致性", False, "响应格式不一致")
            else:
                self.log_test_result("ux", "响应一致性", False, "响应数量不足")
        except Exception as e:
            self.log_test_result("ux", "响应一致性", False, f"异常: {str(e)}")

    # ==================== 主测试执行 ====================
    
    def run_all_tests(self):
        """运行所有测试"""
        self.start_time = time.time()
        logger.info("🚀 开始执行全面系统测试...")
        
        # 功能测试
        logger.info("\n📋 功能测试")
        logger.info("=" * 50)
        task_id = self.test_task_creation()
        self.test_api_health_check()
        self.test_api_root_endpoint()
        self.test_task_list_retrieval()
        if task_id:
            self.test_task_detail_retrieval(task_id)
            self.test_task_cancellation(task_id)
        self.test_statistics_endpoint()
        self.test_queue_status_endpoint()
        self.test_boundary_conditions()
        self.test_invalid_task_id()
        
        # 性能测试
        logger.info("\n⚡ 性能测试")
        logger.info("=" * 50)
        self.test_api_response_time()
        self.test_concurrent_api_calls()
        self.test_memory_usage()
        self.test_cpu_usage()
        
        # 安全测试
        logger.info("\n🔒 安全测试")
        logger.info("=" * 50)
        self.test_sql_injection_prevention()
        self.test_xss_prevention()
        self.test_authentication_bypass()
        self.test_data_validation()
        
        # 兼容性测试
        logger.info("\n🌐 兼容性测试")
        logger.info("=" * 50)
        self.test_api_content_type()
        self.test_cors_headers()
        self.test_json_encoding()
        
        # 用户体验测试
        logger.info("\n👤 用户体验测试")
        logger.info("=" * 50)
        self.test_error_message_clarity()
        self.test_api_documentation_accessibility()
        self.test_response_consistency()
        
        # 生成测试报告
        self.generate_test_report()
    
    def generate_test_report(self):
        """生成测试报告"""
        end_time = time.time()
        total_time = end_time - self.start_time
        
        logger.info("\n📊 测试报告")
        logger.info("=" * 60)
        logger.info(f"测试开始时间: {datetime.fromtimestamp(self.start_time).strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"测试结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"测试总耗时: {total_time:.2f}秒")
        logger.info("=" * 60)
        
        # 测试结果统计
        logger.info("\n📈 测试结果统计")
        logger.info("-" * 40)
        
        total_passed = 0
        total_failed = 0
        total_tests = 0
        
        for test_type, results in self.test_results.items():
            passed = results["passed"]
            failed = results["failed"]
            total = results["total"]
            
            total_passed += passed
            total_failed += failed
            total_tests += total
            
            if total > 0:
                pass_rate = (passed / total) * 100
                logger.info(f"{test_type.upper()}测试:")
                logger.info(f"  总测试数: {total}")
                logger.info(f"  通过数: {passed}")
                logger.info(f"  失败数: {failed}")
                logger.info(f"  通过率: {pass_rate:.1f}%")
                logger.info("")
        
        # 总体统计
        if total_tests > 0:
            overall_pass_rate = (total_passed / total_tests) * 100
            logger.info("=" * 40)
            logger.info(f"总体统计:")
            logger.info(f"  总测试数: {total_tests}")
            logger.info(f"  总通过数: {total_passed}")
            logger.info(f"  总失败数: {total_failed}")
            logger.info(f"  总体通过率: {overall_pass_rate:.1f}%")
            logger.info("=" * 40)
        
        # 缺陷统计
        if self.defects:
            logger.info("\n🐛 缺陷统计")
            logger.info("-" * 40)
            
            severity_counts = {}
            for defect in self.defects:
                severity = defect["severity"]
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            for severity, count in severity_counts.items():
                logger.info(f"{severity}: {count}个")
            
            logger.info(f"总缺陷数: {len(self.defects)}个")
        else:
            logger.info("\n✅ 未发现缺陷")
        
        # 测试结论
        logger.info("\n🎯 测试结论")
        logger.info("=" * 60)
        
        if total_tests > 0 and overall_pass_rate >= 95 and len(self.defects) == 0:
            logger.info("✅ 系统测试通过 - 质量优秀")
        elif total_tests > 0 and overall_pass_rate >= 90 and len([d for d in self.defects if "P0" in d["severity"] or "P1" in d["severity"]]) == 0:
            logger.info("✅ 系统测试通过 - 质量良好")
        elif total_tests > 0 and overall_pass_rate >= 80:
            logger.info("⚠️ 系统测试有条件通过 - 需要修复主要缺陷")
        else:
            logger.info("❌ 系统测试未通过 - 需要修复缺陷后重新测试")
        
        logger.info("=" * 60)
        
        # 保存测试报告到文件
        self.save_test_report_to_file()
    
    def save_test_report_to_file(self):
        """保存测试报告到文件"""
        report_data = {
            "test_summary": {
                "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
                "end_time": datetime.now().isoformat(),
                "total_tests": sum(results["total"] for results in self.test_results.values()),
                "total_passed": sum(results["passed"] for results in self.test_results.values()),
                "total_failed": sum(results["failed"] for results in self.test_results.values())
            },
            "test_results": self.test_results,
            "defects": self.defects,
            "test_coverage": self._calculate_coverage()
        }
        
        try:
            with open("test-report.json", "w", encoding="utf-8") as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            logger.info(f"\n📄 测试报告已保存到: test-report.json")
        except Exception as e:
            logger.error(f"保存测试报告失败: {str(e)}")
    
    def _calculate_coverage(self) -> dict:
        """计算测试覆盖率"""
        return {
            "functional_coverage": f"{(self.test_results['functional']['passed'] / max(self.test_results['functional']['total'], 1)) * 100:.1f}%",
            "performance_coverage": f"{(self.test_results['performance']['passed'] / max(self.test_results['performance']['total'], 1)) * 100:.1f}%",
            "security_coverage": f"{(self.test_results['security']['passed'] / max(self.test_results['security']['total'], 1)) * 100:.1f}%",
            "compatibility_coverage": f"{(self.test_results['compatibility']['passed'] / max(self.test_results['compatibility']['total'], 1)) * 100:.1f}%",
            "ux_coverage": f"{(self.test_results['ux']['passed'] / max(self.test_results['ux']['total'], 1)) * 100:.1f}%"
        }

if __name__ == "__main__":
    # 运行测试
    test_suite = SystemTestSuite()
    test_suite.run_all_tests()