#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YDS-Lab API客户端工具
提供HTTP请求、API测试、接口管理和文档生成功能
适配YDS-Lab项目结构和AI Agent协作需求
"""

import os
import sys
import json
import yaml
import time
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from urllib.parse import urljoin, urlparse
import threading

try:
    import requests
    from requests.adapters import HTTPAdapter
    from requests.packages.urllib3.util.retry import Retry
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False

@dataclass
class APIEndpoint:
    """API端点配置"""
    name: str
    url: str
    method: str = 'GET'
    headers: Dict[str, str] = None
    params: Dict[str, Any] = None
    data: Dict[str, Any] = None
    auth: Dict[str, str] = None
    timeout: int = 30
    description: str = ''
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {}
        if self.params is None:
            self.params = {}
        if self.data is None:
            self.data = {}
        if self.auth is None:
            self.auth = {}

@dataclass
class APIResponse:
    """API响应"""
    success: bool
    status_code: int = None
    headers: Dict[str, str] = None
    data: Any = None
    text: str = None
    json_data: Dict = None
    response_time: float = 0
    error: str = None
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {}

@dataclass
class TestCase:
    """测试用例"""
    name: str
    endpoint: str
    expected_status: int = 200
    expected_data: Dict = None
    assertions: List[str] = None
    setup: Dict[str, Any] = None
    teardown: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.expected_data is None:
            self.expected_data = {}
        if self.assertions is None:
            self.assertions = []
        if self.setup is None:
            self.setup = {}
        if self.teardown is None:
            self.teardown = {}

@dataclass
class TestResult:
    """测试结果"""
    test_case: str
    success: bool
    response: APIResponse = None
    assertions_passed: int = 0
    assertions_failed: int = 0
    error: str = None
    execution_time: float = 0

class APIClient:
    """API客户端"""
    
    def __init__(self, project_root: str = None):
        """初始化API客户端"""
        if project_root is None:
            self.project_root = Path(__file__).parent.parent.parent
        else:
            self.project_root = Path(project_root)
        
        self.config_dir = self.project_root / "Struc" / "GeneralOffice" / "config"
        self.data_dir = self.project_root / "data" / "api"
        self.logs_dir = self.project_root / "logs" / "api"
        self.reports_dir = self.project_root / "reports" / "api"
        
        # 创建目录
        for directory in [self.data_dir, self.logs_dir, self.reports_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # 加载配置
        self.config = self._load_config()
        self.endpoints = self._load_endpoints()
        self.test_cases = self._load_test_cases()
        
        # 初始化会话
        self.session = None
        self.async_session = None
        
        # 设置日志
        self._setup_logging()
        
        # 初始化HTTP会话
        self._init_session()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载API客户端配置"""
        config_file = self.config_dir / "api_config.yaml"
        
        default_config = {
            'base_url': '',
            'timeout': 30,
            'retries': 3,
            'retry_delay': 1,
            'headers': {
                'User-Agent': 'YDS-Lab-API-Client/1.0',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            'auth': {
                'type': 'none',  # none, basic, bearer, api_key, oauth2
                'username': '',
                'password': '',
                'token': '',
                'api_key': '',
                'api_key_header': 'X-API-Key'
            },
            'ssl': {
                'verify': True,
                'cert': None,
                'key': None
            },
            'proxy': {
                'http': None,
                'https': None
            },
            'rate_limit': {
                'enabled': False,
                'requests_per_second': 10,
                'burst': 20
            },
            'logging': {
                'log_requests': True,
                'log_responses': True,
                'log_headers': False,
                'log_body': True,
                'max_body_size': 1024
            },
            'testing': {
                'parallel_tests': 5,
                'test_timeout': 60,
                'continue_on_failure': True,
                'generate_reports': True
            },
            'log_level': 'INFO'
        }
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f)
                    default_config.update(user_config)
            except Exception as e:
                print(f"⚠️ 加载API配置失败: {e}")
        
        return default_config
    
    def _load_endpoints(self) -> Dict[str, APIEndpoint]:
        """加载API端点配置"""
        endpoints = {}
        
        endpoints_file = self.config_dir / "api_endpoints.yaml"
        
        if endpoints_file.exists():
            try:
                with open(endpoints_file, 'r', encoding='utf-8') as f:
                    endpoints_config = yaml.safe_load(f)
                    
                    for name, config in endpoints_config.items():
                        endpoints[name] = APIEndpoint(
                            name=name,
                            **config
                        )
            except Exception as e:
                self.logger.error(f"加载API端点配置失败: {e}")
        
        return endpoints
    
    def _load_test_cases(self) -> Dict[str, TestCase]:
        """加载测试用例"""
        test_cases = {}
        
        test_cases_file = self.config_dir / "api_test_cases.yaml"
        
        if test_cases_file.exists():
            try:
                with open(test_cases_file, 'r', encoding='utf-8') as f:
                    test_config = yaml.safe_load(f)
                    
                    for name, config in test_config.items():
                        test_cases[name] = TestCase(
                            name=name,
                            **config
                        )
            except Exception as e:
                self.logger.error(f"加载测试用例失败: {e}")
        
        return test_cases
    
    def _setup_logging(self):
        """设置日志"""
        log_file = self.logs_dir / f"api_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=getattr(logging, self.config['log_level']),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def _init_session(self):
        """初始化HTTP会话"""
        if not REQUESTS_AVAILABLE:
            self.logger.warning("requests库未安装，同步请求功能不可用")
            return
        
        self.session = requests.Session()
        
        # 设置重试策略
        retry_strategy = Retry(
            total=self.config['retries'],
            backoff_factor=self.config['retry_delay'],
            status_forcelist=[429, 500, 502, 503, 504]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # 设置默认头部
        self.session.headers.update(self.config['headers'])
        
        # 设置SSL配置
        self.session.verify = self.config['ssl']['verify']
        if self.config['ssl']['cert']:
            self.session.cert = (self.config['ssl']['cert'], self.config['ssl']['key'])
        
        # 设置代理
        if self.config['proxy']['http'] or self.config['proxy']['https']:
            self.session.proxies.update({
                'http': self.config['proxy']['http'],
                'https': self.config['proxy']['https']
            })
    
    def _get_auth(self, auth_config: Dict[str, str] = None) -> Any:
        """获取认证配置"""
        if auth_config is None:
            auth_config = self.config['auth']
        
        auth_type = auth_config.get('type', 'none')
        
        if auth_type == 'basic':
            return (auth_config['username'], auth_config['password'])
        
        elif auth_type == 'bearer':
            return {'Authorization': f"Bearer {auth_config['token']}"}
        
        elif auth_type == 'api_key':
            header_name = auth_config.get('api_key_header', 'X-API-Key')
            return {header_name: auth_config['api_key']}
        
        return None
    
    def _apply_auth(self, headers: Dict[str, str], auth_config: Dict[str, str] = None):
        """应用认证配置到头部"""
        auth = self._get_auth(auth_config)
        
        if isinstance(auth, dict):
            headers.update(auth)
        elif isinstance(auth, tuple) and self.session:
            self.session.auth = auth
    
    def _log_request(self, method: str, url: str, headers: Dict, data: Any = None):
        """记录请求日志"""
        if not self.config['logging']['log_requests']:
            return
        
        self.logger.info(f"🔄 {method} {url}")
        
        if self.config['logging']['log_headers'] and headers:
            for key, value in headers.items():
                # 隐藏敏感信息
                if key.lower() in ['authorization', 'x-api-key', 'cookie']:
                    value = '***'
                self.logger.debug(f"  {key}: {value}")
        
        if self.config['logging']['log_body'] and data:
            body_str = str(data)
            max_size = self.config['logging']['max_body_size']
            
            if len(body_str) > max_size:
                body_str = body_str[:max_size] + '...'
            
            self.logger.debug(f"  Body: {body_str}")
    
    def _log_response(self, response: APIResponse):
        """记录响应日志"""
        if not self.config['logging']['log_responses']:
            return
        
        status_emoji = "✅" if response.success else "❌"
        self.logger.info(f"{status_emoji} {response.status_code} ({response.response_time:.3f}s)")
        
        if self.config['logging']['log_headers'] and response.headers:
            for key, value in response.headers.items():
                self.logger.debug(f"  {key}: {value}")
        
        if self.config['logging']['log_body'] and response.text:
            body_str = response.text
            max_size = self.config['logging']['max_body_size']
            
            if len(body_str) > max_size:
                body_str = body_str[:max_size] + '...'
            
            self.logger.debug(f"  Body: {body_str}")
    
    def request(self, method: str, url: str, headers: Dict[str, str] = None, 
                params: Dict[str, Any] = None, data: Any = None, 
                json_data: Dict = None, auth: Dict[str, str] = None,
                timeout: int = None) -> APIResponse:
        """发送HTTP请求"""
        if not REQUESTS_AVAILABLE:
            return APIResponse(
                success=False,
                error="requests库未安装"
            )
        
        start_time = time.time()
        
        # 准备请求参数
        if headers is None:
            headers = {}
        
        if timeout is None:
            timeout = self.config['timeout']
        
        # 构建完整URL
        if self.config['base_url'] and not url.startswith('http'):
            url = urljoin(self.config['base_url'], url)
        
        # 应用认证
        request_headers = headers.copy()
        self._apply_auth(request_headers, auth)
        
        # 记录请求
        self._log_request(method, url, request_headers, data or json_data)
        
        try:
            # 发送请求
            response = self.session.request(
                method=method,
                url=url,
                headers=request_headers,
                params=params,
                data=data,
                json=json_data,
                timeout=timeout
            )
            
            response_time = time.time() - start_time
            
            # 解析响应
            api_response = APIResponse(
                success=response.ok,
                status_code=response.status_code,
                headers=dict(response.headers),
                text=response.text,
                response_time=response_time
            )
            
            # 尝试解析JSON
            try:
                api_response.json_data = response.json()
                api_response.data = api_response.json_data
            except:
                api_response.data = response.text
            
            # 记录响应
            self._log_response(api_response)
            
            return api_response
        
        except Exception as e:
            response_time = time.time() - start_time
            
            api_response = APIResponse(
                success=False,
                response_time=response_time,
                error=str(e)
            )
            
            self.logger.error(f"请求失败: {e}")
            return api_response
    
    def get(self, url: str, **kwargs) -> APIResponse:
        """GET请求"""
        return self.request('GET', url, **kwargs)
    
    def post(self, url: str, **kwargs) -> APIResponse:
        """POST请求"""
        return self.request('POST', url, **kwargs)
    
    def put(self, url: str, **kwargs) -> APIResponse:
        """PUT请求"""
        return self.request('PUT', url, **kwargs)
    
    def patch(self, url: str, **kwargs) -> APIResponse:
        """PATCH请求"""
        return self.request('PATCH', url, **kwargs)
    
    def delete(self, url: str, **kwargs) -> APIResponse:
        """DELETE请求"""
        return self.request('DELETE', url, **kwargs)
    
    def call_endpoint(self, endpoint_name: str, **kwargs) -> APIResponse:
        """调用配置的端点"""
        if endpoint_name not in self.endpoints:
            return APIResponse(
                success=False,
                error=f"端点不存在: {endpoint_name}"
            )
        
        endpoint = self.endpoints[endpoint_name]
        
        # 合并参数
        headers = endpoint.headers.copy()
        headers.update(kwargs.get('headers', {}))
        
        params = endpoint.params.copy()
        params.update(kwargs.get('params', {}))
        
        data = endpoint.data.copy()
        data.update(kwargs.get('data', {}))
        
        # 发送请求
        return self.request(
            method=endpoint.method,
            url=endpoint.url,
            headers=headers,
            params=params,
            data=data if data else None,
            json_data=kwargs.get('json_data'),
            auth=endpoint.auth or kwargs.get('auth'),
            timeout=endpoint.timeout
        )
    
    def add_endpoint(self, endpoint: APIEndpoint) -> bool:
        """添加API端点"""
        try:
            self.endpoints[endpoint.name] = endpoint
            self._save_endpoints()
            
            self.logger.info(f"API端点已添加: {endpoint.name}")
            return True
        
        except Exception as e:
            self.logger.error(f"添加API端点失败: {e}")
            return False
    
    def remove_endpoint(self, name: str) -> bool:
        """移除API端点"""
        try:
            if name in self.endpoints:
                del self.endpoints[name]
                self._save_endpoints()
                
                self.logger.info(f"API端点已移除: {name}")
                return True
            else:
                self.logger.warning(f"API端点不存在: {name}")
                return False
        
        except Exception as e:
            self.logger.error(f"移除API端点失败: {e}")
            return False
    
    def _save_endpoints(self):
        """保存API端点配置"""
        endpoints_file = self.config_dir / "api_endpoints.yaml"
        
        try:
            endpoints_config = {}
            for name, endpoint in self.endpoints.items():
                config_dict = asdict(endpoint)
                del config_dict['name']  # 名称作为key
                endpoints_config[name] = config_dict
            
            with open(endpoints_file, 'w', encoding='utf-8') as f:
                yaml.dump(endpoints_config, f, default_flow_style=False, allow_unicode=True)
        
        except Exception as e:
            self.logger.error(f"保存API端点配置失败: {e}")
    
    def run_test_case(self, test_case_name: str) -> TestResult:
        """运行单个测试用例"""
        if test_case_name not in self.test_cases:
            return TestResult(
                test_case=test_case_name,
                success=False,
                error=f"测试用例不存在: {test_case_name}"
            )
        
        test_case = self.test_cases[test_case_name]
        start_time = time.time()
        
        try:
            # 执行setup
            if test_case.setup:
                self._execute_setup(test_case.setup)
            
            # 调用API
            response = self.call_endpoint(test_case.endpoint)
            
            # 检查状态码
            status_ok = response.status_code == test_case.expected_status
            
            # 执行断言
            assertions_passed = 0
            assertions_failed = 0
            
            for assertion in test_case.assertions:
                try:
                    if self._evaluate_assertion(assertion, response):
                        assertions_passed += 1
                    else:
                        assertions_failed += 1
                except Exception as e:
                    assertions_failed += 1
                    self.logger.error(f"断言执行失败: {assertion} - {e}")
            
            # 执行teardown
            if test_case.teardown:
                self._execute_teardown(test_case.teardown)
            
            execution_time = time.time() - start_time
            success = status_ok and assertions_failed == 0
            
            return TestResult(
                test_case=test_case_name,
                success=success,
                response=response,
                assertions_passed=assertions_passed,
                assertions_failed=assertions_failed,
                execution_time=execution_time
            )
        
        except Exception as e:
            execution_time = time.time() - start_time
            
            return TestResult(
                test_case=test_case_name,
                success=False,
                error=str(e),
                execution_time=execution_time
            )
    
    def _execute_setup(self, setup: Dict[str, Any]):
        """执行测试setup"""
        # 这里可以实现setup逻辑，比如创建测试数据
        pass
    
    def _execute_teardown(self, teardown: Dict[str, Any]):
        """执行测试teardown"""
        # 这里可以实现teardown逻辑，比如清理测试数据
        pass
    
    def _evaluate_assertion(self, assertion: str, response: APIResponse) -> bool:
        """评估断言"""
        # 简单的断言评估器
        # 支持的断言格式:
        # - status_code == 200
        # - json_data.key == "value"
        # - headers.Content-Type contains "json"
        
        try:
            # 创建评估上下文
            context = {
                'status_code': response.status_code,
                'json_data': response.json_data or {},
                'headers': response.headers,
                'text': response.text,
                'response_time': response.response_time
            }
            
            # 简单的表达式评估
            # 注意：这是一个简化版本，生产环境中应该使用更安全的评估器
            return eval(assertion, {"__builtins__": {}}, context)
        
        except Exception as e:
            self.logger.error(f"断言评估失败: {assertion} - {e}")
            return False
    
    def run_tests(self, test_names: List[str] = None) -> List[TestResult]:
        """运行测试用例"""
        if test_names is None:
            test_names = list(self.test_cases.keys())
        
        results = []
        
        for test_name in test_names:
            self.logger.info(f"🧪 运行测试: {test_name}")
            
            result = self.run_test_case(test_name)
            results.append(result)
            
            if result.success:
                self.logger.info(f"✅ 测试通过: {test_name}")
            else:
                self.logger.error(f"❌ 测试失败: {test_name} - {result.error}")
                
                if not self.config['testing']['continue_on_failure']:
                    break
        
        return results
    
    def generate_test_report(self, results: List[TestResult], format: str = 'html') -> str:
        """生成测试报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format == 'html':
            report_file = self.reports_dir / f"api_test_report_{timestamp}.html"
            content = self._generate_html_report(results)
        
        elif format == 'json':
            report_file = self.reports_dir / f"api_test_report_{timestamp}.json"
            content = self._generate_json_report(results)
        
        elif format == 'markdown':
            report_file = self.reports_dir / f"api_test_report_{timestamp}.md"
            content = self._generate_markdown_report(results)
        
        else:
            raise ValueError(f"不支持的报告格式: {format}")
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.info(f"测试报告已生成: {report_file}")
            return str(report_file)
        
        except Exception as e:
            self.logger.error(f"生成测试报告失败: {e}")
            return ""
    
    def _generate_html_report(self, results: List[TestResult]) -> str:
        """生成HTML测试报告"""
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.success)
        failed_tests = total_tests - passed_tests
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>API测试报告</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
        .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
        .metric {{ background: white; padding: 15px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .test-case {{ margin: 20px 0; padding: 15px; border-radius: 5px; }}
        .success {{ background: #d4edda; border-left: 4px solid #28a745; }}
        .failure {{ background: #f8d7da; border-left: 4px solid #dc3545; }}
        .details {{ margin-top: 10px; font-family: monospace; font-size: 12px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🧪 API测试报告</h1>
        <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="summary">
        <div class="metric">
            <h3>总测试数</h3>
            <h2>{total_tests}</h2>
        </div>
        <div class="metric">
            <h3>通过</h3>
            <h2 style="color: #28a745;">{passed_tests}</h2>
        </div>
        <div class="metric">
            <h3>失败</h3>
            <h2 style="color: #dc3545;">{failed_tests}</h2>
        </div>
        <div class="metric">
            <h3>成功率</h3>
            <h2>{(passed_tests/total_tests*100):.1f}%</h2>
        </div>
    </div>
    
    <h2>📋 测试详情</h2>
"""
        
        for result in results:
            status_class = "success" if result.success else "failure"
            status_icon = "✅" if result.success else "❌"
            
            html += f"""
    <div class="test-case {status_class}">
        <h3>{status_icon} {result.test_case}</h3>
        <p><strong>执行时间:</strong> {result.execution_time:.3f}s</p>
        
        {f'<p><strong>错误:</strong> {result.error}</p>' if result.error else ''}
        
        {f'<p><strong>断言:</strong> 通过 {result.assertions_passed}, 失败 {result.assertions_failed}</p>' if result.assertions_passed or result.assertions_failed else ''}
        
        {self._format_response_html(result.response) if result.response else ''}
    </div>
"""
        
        html += """
</body>
</html>
"""
        
        return html
    
    def _format_response_html(self, response: APIResponse) -> str:
        """格式化响应为HTML"""
        if not response:
            return ""
        
        return f"""
        <div class="details">
            <h4>响应详情</h4>
            <table>
                <tr><th>状态码</th><td>{response.status_code}</td></tr>
                <tr><th>响应时间</th><td>{response.response_time:.3f}s</td></tr>
                <tr><th>成功</th><td>{'是' if response.success else '否'}</td></tr>
            </table>
            
            {f'<h5>响应头</h5><pre>{json.dumps(response.headers, indent=2, ensure_ascii=False)}</pre>' if response.headers else ''}
            
            {f'<h5>响应体</h5><pre>{json.dumps(response.json_data, indent=2, ensure_ascii=False) if response.json_data else response.text}</pre>' if response.text else ''}
        </div>
"""
    
    def _generate_json_report(self, results: List[TestResult]) -> str:
        """生成JSON测试报告"""
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tests': len(results),
                'passed_tests': sum(1 for r in results if r.success),
                'failed_tests': sum(1 for r in results if not r.success),
                'success_rate': sum(1 for r in results if r.success) / len(results) * 100 if results else 0
            },
            'results': []
        }
        
        for result in results:
            result_data = {
                'test_case': result.test_case,
                'success': result.success,
                'execution_time': result.execution_time,
                'assertions_passed': result.assertions_passed,
                'assertions_failed': result.assertions_failed,
                'error': result.error
            }
            
            if result.response:
                result_data['response'] = {
                    'status_code': result.response.status_code,
                    'success': result.response.success,
                    'response_time': result.response.response_time,
                    'headers': result.response.headers,
                    'data': result.response.json_data or result.response.text
                }
            
            report_data['results'].append(result_data)
        
        return json.dumps(report_data, indent=2, ensure_ascii=False)
    
    def _generate_markdown_report(self, results: List[TestResult]) -> str:
        """生成Markdown测试报告"""
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.success)
        failed_tests = total_tests - passed_tests
        
        md = f"""# 🧪 API测试报告

**生成时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 测试摘要

| 指标 | 数值 |
|------|------|
| 总测试数 | {total_tests} |
| 通过 | {passed_tests} |
| 失败 | {failed_tests} |
| 成功率 | {(passed_tests/total_tests*100):.1f}% |

## 📋 测试详情

"""
        
        for result in results:
            status_icon = "✅" if result.success else "❌"
            
            md += f"""### {status_icon} {result.test_case}

- **执行时间:** {result.execution_time:.3f}s
- **状态:** {'通过' if result.success else '失败'}
"""
            
            if result.error:
                md += f"- **错误:** {result.error}\n"
            
            if result.assertions_passed or result.assertions_failed:
                md += f"- **断言:** 通过 {result.assertions_passed}, 失败 {result.assertions_failed}\n"
            
            if result.response:
                md += f"""
**响应信息:**
- 状态码: {result.response.status_code}
- 响应时间: {result.response.response_time:.3f}s
- 成功: {'是' if result.response.success else '否'}
"""
            
            md += "\n---\n\n"
        
        return md
    
    def export_endpoints(self, format: str = 'yaml') -> str:
        """导出API端点配置"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format == 'yaml':
            export_file = self.data_dir / f"endpoints_export_{timestamp}.yaml"
            
            endpoints_config = {}
            for name, endpoint in self.endpoints.items():
                config_dict = asdict(endpoint)
                del config_dict['name']
                endpoints_config[name] = config_dict
            
            with open(export_file, 'w', encoding='utf-8') as f:
                yaml.dump(endpoints_config, f, default_flow_style=False, allow_unicode=True)
        
        elif format == 'json':
            export_file = self.data_dir / f"endpoints_export_{timestamp}.json"
            
            endpoints_config = {}
            for name, endpoint in self.endpoints.items():
                config_dict = asdict(endpoint)
                del config_dict['name']
                endpoints_config[name] = config_dict
            
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(endpoints_config, f, indent=2, ensure_ascii=False)
        
        elif format == 'postman':
            export_file = self.data_dir / f"endpoints_postman_{timestamp}.json"
            postman_collection = self._generate_postman_collection()
            
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(postman_collection, f, indent=2, ensure_ascii=False)
        
        else:
            raise ValueError(f"不支持的导出格式: {format}")
        
        self.logger.info(f"端点配置已导出: {export_file}")
        return str(export_file)
    
    def _generate_postman_collection(self) -> Dict:
        """生成Postman集合"""
        collection = {
            "info": {
                "name": "YDS-Lab API Collection",
                "description": "Generated by YDS-Lab API Client",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "item": []
        }
        
        for name, endpoint in self.endpoints.items():
            item = {
                "name": name,
                "request": {
                    "method": endpoint.method,
                    "header": [
                        {"key": k, "value": v} for k, v in endpoint.headers.items()
                    ],
                    "url": {
                        "raw": endpoint.url,
                        "query": [
                            {"key": k, "value": str(v)} for k, v in endpoint.params.items()
                        ]
                    }
                }
            }
            
            if endpoint.data:
                item["request"]["body"] = {
                    "mode": "raw",
                    "raw": json.dumps(endpoint.data, ensure_ascii=False),
                    "options": {
                        "raw": {
                            "language": "json"
                        }
                    }
                }
            
            if endpoint.description:
                item["request"]["description"] = endpoint.description
            
            collection["item"].append(item)
        
        return collection
    
    def list_endpoints(self) -> List[Dict[str, Any]]:
        """列出所有端点"""
        endpoints_list = []
        
        for name, endpoint in self.endpoints.items():
            endpoint_info = {
                'name': name,
                'method': endpoint.method,
                'url': endpoint.url,
                'description': endpoint.description,
                'timeout': endpoint.timeout
            }
            
            endpoints_list.append(endpoint_info)
        
        return endpoints_list

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='YDS-Lab API客户端工具')
    parser.add_argument('--project-root', help='指定项目根目录路径')
    parser.add_argument('--list-endpoints', action='store_true', help='列出所有API端点')
    parser.add_argument('--call', help='调用指定端点')
    parser.add_argument('--test', help='运行指定测试用例')
    parser.add_argument('--test-all', action='store_true', help='运行所有测试用例')
    parser.add_argument('--export', choices=['yaml', 'json', 'postman'], help='导出端点配置')
    parser.add_argument('--request', nargs=2, metavar=('METHOD', 'URL'), help='发送HTTP请求')
    parser.add_argument('--headers', help='请求头部 (JSON格式)')
    parser.add_argument('--data', help='请求数据 (JSON格式)')
    parser.add_argument('--params', help='请求参数 (JSON格式)')
    
    args = parser.parse_args()
    
    client = APIClient(args.project_root)
    
    # 列出端点
    if args.list_endpoints:
        endpoints = client.list_endpoints()
        
        print("🔗 API端点列表")
        print("="*50)
        
        for endpoint in endpoints:
            print(f"名称: {endpoint['name']}")
            print(f"方法: {endpoint['method']}")
            print(f"URL: {endpoint['url']}")
            print(f"描述: {endpoint['description']}")
            print(f"超时: {endpoint['timeout']}s")
            print("-" * 30)
        
        return
    
    # 调用端点
    if args.call:
        print(f"🔄 调用端点: {args.call}")
        
        response = client.call_endpoint(args.call)
        
        print(f"状态码: {response.status_code}")
        print(f"成功: {'是' if response.success else '否'}")
        print(f"响应时间: {response.response_time:.3f}s")
        
        if response.error:
            print(f"错误: {response.error}")
        
        if response.json_data:
            print("响应数据:")
            print(json.dumps(response.json_data, indent=2, ensure_ascii=False))
        elif response.text:
            print(f"响应文本: {response.text[:500]}...")
        
        return
    
    # 运行测试
    if args.test:
        print(f"🧪 运行测试: {args.test}")
        
        result = client.run_test_case(args.test)
        
        if result.success:
            print("✅ 测试通过")
        else:
            print(f"❌ 测试失败: {result.error}")
        
        print(f"执行时间: {result.execution_time:.3f}s")
        
        if result.assertions_passed or result.assertions_failed:
            print(f"断言: 通过 {result.assertions_passed}, 失败 {result.assertions_failed}")
        
        return
    
    # 运行所有测试
    if args.test_all:
        print("🧪 运行所有测试用例")
        
        results = client.run_tests()
        
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.success)
        
        print(f"\n📊 测试结果: {passed_tests}/{total_tests} 通过")
        
        # 生成报告
        if client.config['testing']['generate_reports']:
            report_file = client.generate_test_report(results, 'html')
            print(f"📄 测试报告: {report_file}")
        
        return
    
    # 导出配置
    if args.export:
        print(f"📤 导出端点配置: {args.export}")
        
        export_file = client.export_endpoints(args.export)
        print(f"✅ 导出完成: {export_file}")
        
        return
    
    # 发送请求
    if args.request:
        method, url = args.request
        
        # 解析参数
        headers = {}
        if args.headers:
            try:
                headers = json.loads(args.headers)
            except:
                print("❌ 头部参数格式错误")
                return
        
        params = {}
        if args.params:
            try:
                params = json.loads(args.params)
            except:
                print("❌ 请求参数格式错误")
                return
        
        data = None
        if args.data:
            try:
                data = json.loads(args.data)
            except:
                print("❌ 请求数据格式错误")
                return
        
        print(f"🔄 发送请求: {method} {url}")
        
        response = client.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json_data=data
        )
        
        print(f"状态码: {response.status_code}")
        print(f"成功: {'是' if response.success else '否'}")
        print(f"响应时间: {response.response_time:.3f}s")
        
        if response.error:
            print(f"错误: {response.error}")
        
        if response.json_data:
            print("响应数据:")
            print(json.dumps(response.json_data, indent=2, ensure_ascii=False))
        elif response.text:
            print(f"响应文本: {response.text[:500]}...")
        
        return
    
    # 默认显示状态
    print("🔗 API客户端状态")
    print("="*40)
    print(f"项目路径: {client.project_root}")
    print(f"基础URL: {client.config['base_url']}")
    print(f"端点数量: {len(client.endpoints)}")
    print(f"测试用例: {len(client.test_cases)}")
    print(f"超时设置: {client.config['timeout']}s")

if __name__ == "__main__":
    main()