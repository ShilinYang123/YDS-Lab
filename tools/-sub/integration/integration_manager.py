#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YDS-Lab 集成管理工具
提供第三方服务集成、API连接、数据同步和集成测试功能
适配YDS-Lab项目结构和AI Agent协作需求
"""

import os
import sys
import json
import asyncio
import aiohttp
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Callable
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, asdict, field
from enum import Enum
import hashlib
import base64
from urllib.parse import urljoin, urlparse
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False

try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    import pika
    RABBITMQ_AVAILABLE = True
except ImportError:
    RABBITMQ_AVAILABLE = False

class IntegrationType(Enum):
    """集成类型枚举"""
    REST_API = "rest_api"
    GRAPHQL = "graphql"
    WEBHOOK = "webhook"
    DATABASE = "database"
    MESSAGE_QUEUE = "message_queue"
    FILE_STORAGE = "file_storage"
    AUTHENTICATION = "authentication"
    PAYMENT = "payment"
    EMAIL = "email"
    SMS = "sms"
    ANALYTICS = "analytics"
    MONITORING = "monitoring"
    CUSTOM = "custom"

class AuthType(Enum):
    """认证类型枚举"""
    NONE = "none"
    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"
    BASIC_AUTH = "basic_auth"
    OAUTH2 = "oauth2"
    JWT = "jwt"
    CUSTOM = "custom"

class SyncDirection(Enum):
    """同步方向枚举"""
    PULL = "pull"  # 从外部拉取数据
    PUSH = "push"  # 推送数据到外部
    BIDIRECTIONAL = "bidirectional"  # 双向同步

class IntegrationStatus(Enum):
    """集成状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    TESTING = "testing"
    MAINTENANCE = "maintenance"

@dataclass
class AuthConfig:
    """认证配置"""
    auth_type: AuthType
    credentials: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    params: Dict[str, str] = field(default_factory=dict)
    token_refresh_url: Optional[str] = None
    token_expires_at: Optional[datetime] = None

@dataclass
class EndpointConfig:
    """端点配置"""
    url: str
    method: str = "GET"
    headers: Dict[str, str] = field(default_factory=dict)
    params: Dict[str, Any] = field(default_factory=dict)
    data: Optional[Dict[str, Any]] = None
    timeout: int = 30
    retry_count: int = 3
    retry_delay: float = 1.0

@dataclass
class DataMapping:
    """数据映射配置"""
    source_field: str
    target_field: str
    transform_function: Optional[str] = None
    default_value: Any = None
    required: bool = False

@dataclass
class SyncConfig:
    """同步配置"""
    direction: SyncDirection
    schedule: Optional[str] = None  # cron表达式
    batch_size: int = 100
    data_mappings: List[DataMapping] = field(default_factory=list)
    filters: Dict[str, Any] = field(default_factory=dict)
    last_sync: Optional[datetime] = None
    sync_key_field: Optional[str] = None

@dataclass
class Integration:
    """集成配置"""
    id: str
    name: str
    integration_type: IntegrationType
    description: str = ""
    base_url: str = ""
    auth_config: Optional[AuthConfig] = None
    endpoints: Dict[str, EndpointConfig] = field(default_factory=dict)
    sync_config: Optional[SyncConfig] = None
    status: IntegrationStatus = IntegrationStatus.INACTIVE
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if isinstance(self.integration_type, str):
            self.integration_type = IntegrationType(self.integration_type)
        if isinstance(self.status, str):
            self.status = IntegrationStatus(self.status)

@dataclass
class IntegrationResult:
    """集成执行结果"""
    integration_id: str
    endpoint: str
    success: bool
    status_code: Optional[int] = None
    response_data: Any = None
    error_message: Optional[str] = None
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class SyncResult:
    """同步结果"""
    integration_id: str
    direction: SyncDirection
    success: bool
    records_processed: int = 0
    records_success: int = 0
    records_failed: int = 0
    error_message: Optional[str] = None
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

class IntegrationManager:
    """集成管理器"""
    
    def __init__(self, project_root: str = None):
        """初始化集成管理器"""
        if project_root is None:
            self.project_root = Path(__file__).parent.parent.parent
        else:
            self.project_root = Path(project_root)
        
        # 集成管理目录
        self.integration_dir = self.project_root / "integrations"
        self.config_dir = self.integration_dir / "config"
        self.data_dir = self.integration_dir / "data"
        self.logs_dir = self.integration_dir / "logs"
        self.cache_dir = self.integration_dir / "cache"
        
        # 创建目录
        for directory in [self.integration_dir, self.config_dir, self.data_dir, 
                         self.logs_dir, self.cache_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # 配置文件
        self.config_file = self.config_dir / "integration_config.json"
        self.integrations_file = self.config_dir / "integrations.json"
        
        # 设置日志
        self.logger = logging.getLogger('yds_lab.integration_manager')
        self._setup_logging()
        
        # 加载配置
        self._load_config()
        
        # 集成实例
        self.integrations: Dict[str, Integration] = {}
        self._load_integrations()
        
        # 会话管理
        self.session = None
        if REQUESTS_AVAILABLE:
            self.session = requests.Session()
        
        # 异步会话
        self.async_session = None
        
        # 线程池
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # 缓存
        self.cache = {}
        
        # 加密密钥
        self.encryption_key = self._get_or_create_encryption_key()
    
    def _setup_logging(self):
        """设置日志"""
        log_file = self.logs_dir / f"integration_{datetime.now().strftime('%Y%m%d')}.log"
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 文件处理器
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.WARNING)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        self.logger.setLevel(logging.INFO)
    
    def _load_config(self):
        """加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except Exception as e:
                self.logger.error(f"加载配置失败: {e}")
                self.config = {}
        else:
            self.config = {
                'default_timeout': 30,
                'default_retry_count': 3,
                'default_retry_delay': 1.0,
                'max_concurrent_requests': 10,
                'cache_ttl': 3600,
                'sync_batch_size': 100,
                'webhook_secret': None,
                'rate_limit': {
                    'enabled': True,
                    'requests_per_minute': 60,
                    'burst_limit': 10
                },
                'security': {
                    'encrypt_credentials': True,
                    'validate_ssl': True,
                    'allowed_hosts': []
                }
            }
            self._save_config()
    
    def _save_config(self):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
    
    def _load_integrations(self):
        """加载集成配置"""
        if self.integrations_file.exists():
            try:
                with open(self.integrations_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for integration_data in data.get('integrations', []):
                    # 解密凭据
                    if integration_data.get('auth_config', {}).get('credentials'):
                        integration_data['auth_config']['credentials'] = self._decrypt_credentials(
                            integration_data['auth_config']['credentials']
                        )
                    
                    # 转换日期时间
                    for field in ['created_at', 'updated_at']:
                        if field in integration_data:
                            integration_data[field] = datetime.fromisoformat(integration_data[field])
                    
                    # 转换同步配置中的日期时间
                    if integration_data.get('sync_config', {}).get('last_sync'):
                        integration_data['sync_config']['last_sync'] = datetime.fromisoformat(
                            integration_data['sync_config']['last_sync']
                        )
                    
                    # 创建集成实例
                    integration = Integration(**integration_data)
                    self.integrations[integration.id] = integration
                
                self.logger.info(f"已加载 {len(self.integrations)} 个集成配置")
            
            except Exception as e:
                self.logger.error(f"加载集成配置失败: {e}")
    
    def _save_integrations(self):
        """保存集成配置"""
        try:
            integrations_data = []
            
            for integration in self.integrations.values():
                integration_dict = asdict(integration)
                
                # 加密凭据
                if integration_dict.get('auth_config', {}).get('credentials'):
                    integration_dict['auth_config']['credentials'] = self._encrypt_credentials(
                        integration_dict['auth_config']['credentials']
                    )
                
                # 转换枚举为字符串
                integration_dict['integration_type'] = integration.integration_type.value
                integration_dict['status'] = integration.status.value
                
                if integration.auth_config and integration.auth_config.auth_type:
                    integration_dict['auth_config']['auth_type'] = integration.auth_config.auth_type.value
                
                if integration.sync_config and integration.sync_config.direction:
                    integration_dict['sync_config']['direction'] = integration.sync_config.direction.value
                
                # 转换日期时间为字符串
                for field in ['created_at', 'updated_at']:
                    if field in integration_dict:
                        integration_dict[field] = integration_dict[field].isoformat()
                
                if integration_dict.get('sync_config', {}).get('last_sync'):
                    integration_dict['sync_config']['last_sync'] = integration_dict['sync_config']['last_sync'].isoformat()
                
                integrations_data.append(integration_dict)
            
            data = {'integrations': integrations_data}
            
            with open(self.integrations_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"已保存 {len(integrations_data)} 个集成配置")
        
        except Exception as e:
            self.logger.error(f"保存集成配置失败: {e}")
    
    def _get_or_create_encryption_key(self) -> bytes:
        """获取或创建加密密钥"""
        key_file = self.config_dir / ".encryption_key"
        
        if key_file.exists() and CRYPTO_AVAILABLE:
            try:
                return key_file.read_bytes()
            except Exception:
                pass
        
        if CRYPTO_AVAILABLE:
            key = Fernet.generate_key()
            try:
                key_file.write_bytes(key)
                key_file.chmod(0o600)  # 仅所有者可读写
                return key
            except Exception:
                pass
        
        # 如果无法使用加密，返回固定密钥（不安全）
        return b"insecure_fallback_key_32_bytes_"
    
    def _encrypt_credentials(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """加密凭据"""
        if not self.config.get('security', {}).get('encrypt_credentials', True):
            return credentials
        
        if not CRYPTO_AVAILABLE:
            self.logger.warning("加密库不可用，凭据将以明文存储")
            return credentials
        
        try:
            fernet = Fernet(self.encryption_key)
            encrypted_credentials = {}
            
            for key, value in credentials.items():
                if isinstance(value, str) and value:
                    encrypted_value = fernet.encrypt(value.encode()).decode()
                    encrypted_credentials[key] = f"encrypted:{encrypted_value}"
                else:
                    encrypted_credentials[key] = value
            
            return encrypted_credentials
        
        except Exception as e:
            self.logger.error(f"加密凭据失败: {e}")
            return credentials
    
    def _decrypt_credentials(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """解密凭据"""
        if not CRYPTO_AVAILABLE:
            return credentials
        
        try:
            fernet = Fernet(self.encryption_key)
            decrypted_credentials = {}
            
            for key, value in credentials.items():
                if isinstance(value, str) and value.startswith("encrypted:"):
                    encrypted_value = value[10:]  # 移除"encrypted:"前缀
                    decrypted_value = fernet.decrypt(encrypted_value.encode()).decode()
                    decrypted_credentials[key] = decrypted_value
                else:
                    decrypted_credentials[key] = value
            
            return decrypted_credentials
        
        except Exception as e:
            self.logger.error(f"解密凭据失败: {e}")
            return credentials
    
    def add_integration(self, integration: Integration) -> bool:
        """添加集成"""
        try:
            integration.updated_at = datetime.now()
            self.integrations[integration.id] = integration
            self._save_integrations()
            
            self.logger.info(f"已添加集成: {integration.name} ({integration.id})")
            return True
        
        except Exception as e:
            self.logger.error(f"添加集成失败: {e}")
            return False
    
    def remove_integration(self, integration_id: str) -> bool:
        """移除集成"""
        try:
            if integration_id in self.integrations:
                integration = self.integrations[integration_id]
                del self.integrations[integration_id]
                self._save_integrations()
                
                self.logger.info(f"已移除集成: {integration.name} ({integration_id})")
                return True
            else:
                self.logger.warning(f"集成不存在: {integration_id}")
                return False
        
        except Exception as e:
            self.logger.error(f"移除集成失败: {e}")
            return False
    
    def update_integration(self, integration_id: str, **kwargs) -> bool:
        """更新集成"""
        try:
            if integration_id not in self.integrations:
                self.logger.error(f"集成不存在: {integration_id}")
                return False
            
            integration = self.integrations[integration_id]
            
            for key, value in kwargs.items():
                if hasattr(integration, key):
                    setattr(integration, key, value)
            
            integration.updated_at = datetime.now()
            self._save_integrations()
            
            self.logger.info(f"已更新集成: {integration.name} ({integration_id})")
            return True
        
        except Exception as e:
            self.logger.error(f"更新集成失败: {e}")
            return False
    
    def get_integration(self, integration_id: str) -> Optional[Integration]:
        """获取集成"""
        return self.integrations.get(integration_id)
    
    def list_integrations(self, status: IntegrationStatus = None, 
                         integration_type: IntegrationType = None) -> List[Integration]:
        """列出集成"""
        integrations = list(self.integrations.values())
        
        if status:
            integrations = [i for i in integrations if i.status == status]
        
        if integration_type:
            integrations = [i for i in integrations if i.integration_type == integration_type]
        
        return integrations
    
    def test_integration(self, integration_id: str, endpoint: str = None) -> IntegrationResult:
        """测试集成"""
        integration = self.get_integration(integration_id)
        if not integration:
            return IntegrationResult(
                integration_id=integration_id,
                endpoint=endpoint or "unknown",
                success=False,
                error_message="集成不存在"
            )
        
        start_time = time.time()
        
        try:
            # 选择测试端点
            if endpoint and endpoint in integration.endpoints:
                endpoint_config = integration.endpoints[endpoint]
            elif integration.endpoints:
                endpoint_name = list(integration.endpoints.keys())[0]
                endpoint_config = integration.endpoints[endpoint_name]
                endpoint = endpoint_name
            else:
                # 创建默认测试端点
                endpoint_config = EndpointConfig(
                    url=integration.base_url,
                    method="GET"
                )
                endpoint = "default"
            
            # 执行请求
            result = self._execute_request(integration, endpoint_config)
            
            execution_time = time.time() - start_time
            
            return IntegrationResult(
                integration_id=integration_id,
                endpoint=endpoint,
                success=result.get('success', False),
                status_code=result.get('status_code'),
                response_data=result.get('data'),
                error_message=result.get('error'),
                execution_time=execution_time
            )
        
        except Exception as e:
            execution_time = time.time() - start_time
            
            return IntegrationResult(
                integration_id=integration_id,
                endpoint=endpoint or "unknown",
                success=False,
                error_message=str(e),
                execution_time=execution_time
            )
    
    def _execute_request(self, integration: Integration, 
                        endpoint_config: EndpointConfig) -> Dict[str, Any]:
        """执行HTTP请求"""
        if not REQUESTS_AVAILABLE:
            return {
                'success': False,
                'error': 'requests库不可用'
            }
        
        try:
            # 构建URL
            if endpoint_config.url.startswith('http'):
                url = endpoint_config.url
            else:
                url = urljoin(integration.base_url, endpoint_config.url)
            
            # 准备请求参数
            headers = dict(endpoint_config.headers)
            params = dict(endpoint_config.params)
            
            # 添加认证
            if integration.auth_config:
                self._add_authentication(headers, params, integration.auth_config)
            
            # 执行请求
            response = self.session.request(
                method=endpoint_config.method,
                url=url,
                headers=headers,
                params=params,
                json=endpoint_config.data,
                timeout=endpoint_config.timeout
            )
            
            # 处理响应
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            return {
                'success': response.status_code < 400,
                'status_code': response.status_code,
                'data': response_data,
                'headers': dict(response.headers)
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _add_authentication(self, headers: Dict[str, str], params: Dict[str, str], 
                          auth_config: AuthConfig):
        """添加认证信息"""
        if auth_config.auth_type == AuthType.API_KEY:
            api_key = auth_config.credentials.get('api_key')
            key_location = auth_config.credentials.get('key_location', 'header')
            key_name = auth_config.credentials.get('key_name', 'X-API-Key')
            
            if api_key:
                if key_location == 'header':
                    headers[key_name] = api_key
                elif key_location == 'query':
                    params[key_name] = api_key
        
        elif auth_config.auth_type == AuthType.BEARER_TOKEN:
            token = auth_config.credentials.get('token')
            if token:
                headers['Authorization'] = f'Bearer {token}'
        
        elif auth_config.auth_type == AuthType.BASIC_AUTH:
            username = auth_config.credentials.get('username')
            password = auth_config.credentials.get('password')
            if username and password:
                credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                headers['Authorization'] = f'Basic {credentials}'
        
        elif auth_config.auth_type == AuthType.JWT:
            token = auth_config.credentials.get('token')
            if token:
                headers['Authorization'] = f'Bearer {token}'
        
        # 添加自定义头部和参数
        headers.update(auth_config.headers)
        params.update(auth_config.params)
    
    def call_endpoint(self, integration_id: str, endpoint: str, 
                     data: Dict[str, Any] = None, **kwargs) -> IntegrationResult:
        """调用集成端点"""
        integration = self.get_integration(integration_id)
        if not integration:
            return IntegrationResult(
                integration_id=integration_id,
                endpoint=endpoint,
                success=False,
                error_message="集成不存在"
            )
        
        if endpoint not in integration.endpoints:
            return IntegrationResult(
                integration_id=integration_id,
                endpoint=endpoint,
                success=False,
                error_message="端点不存在"
            )
        
        start_time = time.time()
        
        try:
            endpoint_config = integration.endpoints[endpoint]
            
            # 覆盖配置
            if data is not None:
                endpoint_config.data = data
            
            for key, value in kwargs.items():
                if hasattr(endpoint_config, key):
                    setattr(endpoint_config, key, value)
            
            # 执行请求
            result = self._execute_request(integration, endpoint_config)
            
            execution_time = time.time() - start_time
            
            return IntegrationResult(
                integration_id=integration_id,
                endpoint=endpoint,
                success=result.get('success', False),
                status_code=result.get('status_code'),
                response_data=result.get('data'),
                error_message=result.get('error'),
                execution_time=execution_time
            )
        
        except Exception as e:
            execution_time = time.time() - start_time
            
            return IntegrationResult(
                integration_id=integration_id,
                endpoint=endpoint,
                success=False,
                error_message=str(e),
                execution_time=execution_time
            )
    
    def sync_data(self, integration_id: str, direction: SyncDirection = None) -> SyncResult:
        """同步数据"""
        integration = self.get_integration(integration_id)
        if not integration:
            return SyncResult(
                integration_id=integration_id,
                direction=direction or SyncDirection.PULL,
                success=False,
                error_message="集成不存在"
            )
        
        if not integration.sync_config:
            return SyncResult(
                integration_id=integration_id,
                direction=direction or SyncDirection.PULL,
                success=False,
                error_message="未配置同步"
            )
        
        sync_direction = direction or integration.sync_config.direction
        start_time = time.time()
        
        try:
            if sync_direction == SyncDirection.PULL:
                result = self._sync_pull_data(integration)
            elif sync_direction == SyncDirection.PUSH:
                result = self._sync_push_data(integration)
            elif sync_direction == SyncDirection.BIDIRECTIONAL:
                pull_result = self._sync_pull_data(integration)
                push_result = self._sync_push_data(integration)
                
                result = SyncResult(
                    integration_id=integration_id,
                    direction=sync_direction,
                    success=pull_result.success and push_result.success,
                    records_processed=pull_result.records_processed + push_result.records_processed,
                    records_success=pull_result.records_success + push_result.records_success,
                    records_failed=pull_result.records_failed + push_result.records_failed,
                    error_message=pull_result.error_message or push_result.error_message,
                    execution_time=time.time() - start_time
                )
            else:
                result = SyncResult(
                    integration_id=integration_id,
                    direction=sync_direction,
                    success=False,
                    error_message="不支持的同步方向"
                )
            
            # 更新最后同步时间
            if result.success:
                integration.sync_config.last_sync = datetime.now()
                self._save_integrations()
            
            return result
        
        except Exception as e:
            execution_time = time.time() - start_time
            
            return SyncResult(
                integration_id=integration_id,
                direction=sync_direction,
                success=False,
                error_message=str(e),
                execution_time=execution_time
            )
    
    def _sync_pull_data(self, integration: Integration) -> SyncResult:
        """拉取数据同步"""
        # 这里应该实现具体的数据拉取逻辑
        # 根据集成类型和配置从外部系统拉取数据
        
        records_processed = 0
        records_success = 0
        records_failed = 0
        
        try:
            # 示例：从REST API拉取数据
            if integration.integration_type == IntegrationType.REST_API:
                if 'list' in integration.endpoints:
                    endpoint_config = integration.endpoints['list']
                    result = self._execute_request(integration, endpoint_config)
                    
                    if result.get('success'):
                        data = result.get('data', [])
                        if isinstance(data, list):
                            records_processed = len(data)
                            records_success = records_processed
                            
                            # 保存数据到本地
                            self._save_sync_data(integration.id, 'pull', data)
                        else:
                            records_processed = 1
                            records_success = 1
                            self._save_sync_data(integration.id, 'pull', [data])
            
            return SyncResult(
                integration_id=integration.id,
                direction=SyncDirection.PULL,
                success=records_failed == 0,
                records_processed=records_processed,
                records_success=records_success,
                records_failed=records_failed
            )
        
        except Exception as e:
            return SyncResult(
                integration_id=integration.id,
                direction=SyncDirection.PULL,
                success=False,
                error_message=str(e)
            )
    
    def _sync_push_data(self, integration: Integration) -> SyncResult:
        """推送数据同步"""
        # 这里应该实现具体的数据推送逻辑
        # 根据集成类型和配置向外部系统推送数据
        
        records_processed = 0
        records_success = 0
        records_failed = 0
        
        try:
            # 获取待推送的数据
            local_data = self._get_local_sync_data(integration.id, 'push')
            
            if not local_data:
                return SyncResult(
                    integration_id=integration.id,
                    direction=SyncDirection.PUSH,
                    success=True,
                    records_processed=0,
                    records_success=0,
                    records_failed=0
                )
            
            # 示例：推送数据到REST API
            if integration.integration_type == IntegrationType.REST_API:
                if 'create' in integration.endpoints:
                    endpoint_config = integration.endpoints['create']
                    
                    for record in local_data:
                        records_processed += 1
                        
                        # 应用数据映射
                        mapped_data = self._apply_data_mapping(
                            record, integration.sync_config.data_mappings
                        )
                        
                        endpoint_config.data = mapped_data
                        result = self._execute_request(integration, endpoint_config)
                        
                        if result.get('success'):
                            records_success += 1
                        else:
                            records_failed += 1
            
            return SyncResult(
                integration_id=integration.id,
                direction=SyncDirection.PUSH,
                success=records_failed == 0,
                records_processed=records_processed,
                records_success=records_success,
                records_failed=records_failed
            )
        
        except Exception as e:
            return SyncResult(
                integration_id=integration.id,
                direction=SyncDirection.PUSH,
                success=False,
                error_message=str(e)
            )
    
    def _apply_data_mapping(self, data: Dict[str, Any], 
                           mappings: List[DataMapping]) -> Dict[str, Any]:
        """应用数据映射"""
        mapped_data = {}
        
        for mapping in mappings:
            source_value = data.get(mapping.source_field, mapping.default_value)
            
            # 应用转换函数
            if mapping.transform_function and source_value is not None:
                try:
                    # 这里可以实现更复杂的转换逻辑
                    if mapping.transform_function == 'upper':
                        source_value = str(source_value).upper()
                    elif mapping.transform_function == 'lower':
                        source_value = str(source_value).lower()
                    elif mapping.transform_function == 'strip':
                        source_value = str(source_value).strip()
                except Exception as e:
                    self.logger.warning(f"数据转换失败: {e}")
            
            # 检查必填字段
            if mapping.required and source_value is None:
                raise ValueError(f"必填字段缺失: {mapping.source_field}")
            
            if source_value is not None:
                mapped_data[mapping.target_field] = source_value
        
        return mapped_data
    
    def _save_sync_data(self, integration_id: str, direction: str, data: List[Dict[str, Any]]):
        """保存同步数据"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{integration_id}_{direction}_{timestamp}.json"
            filepath = self.data_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"已保存同步数据: {filepath}")
        
        except Exception as e:
            self.logger.error(f"保存同步数据失败: {e}")
    
    def _get_local_sync_data(self, integration_id: str, direction: str) -> List[Dict[str, Any]]:
        """获取本地同步数据"""
        try:
            # 查找最新的数据文件
            pattern = f"{integration_id}_{direction}_*.json"
            files = list(self.data_dir.glob(pattern))
            
            if not files:
                return []
            
            # 按时间排序，获取最新文件
            latest_file = sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)[0]
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        except Exception as e:
            self.logger.error(f"获取本地同步数据失败: {e}")
            return []
    
    def get_integration_status(self, integration_id: str) -> Dict[str, Any]:
        """获取集成状态"""
        integration = self.get_integration(integration_id)
        if not integration:
            return {'error': '集成不存在'}
        
        # 测试连接
        test_result = self.test_integration(integration_id)
        
        # 获取最近的同步结果
        last_sync = None
        if integration.sync_config and integration.sync_config.last_sync:
            last_sync = integration.sync_config.last_sync.isoformat()
        
        return {
            'id': integration.id,
            'name': integration.name,
            'type': integration.integration_type.value,
            'status': integration.status.value,
            'base_url': integration.base_url,
            'endpoints_count': len(integration.endpoints),
            'has_auth': integration.auth_config is not None,
            'has_sync': integration.sync_config is not None,
            'last_sync': last_sync,
            'connection_test': {
                'success': test_result.success,
                'status_code': test_result.status_code,
                'response_time': test_result.execution_time,
                'error': test_result.error_message
            },
            'created_at': integration.created_at.isoformat(),
            'updated_at': integration.updated_at.isoformat()
        }
    
    def generate_integration_report(self) -> Dict[str, Any]:
        """生成集成报告"""
        report = {
            'summary': {
                'total_integrations': len(self.integrations),
                'active_integrations': len([i for i in self.integrations.values() 
                                          if i.status == IntegrationStatus.ACTIVE]),
                'inactive_integrations': len([i for i in self.integrations.values() 
                                            if i.status == IntegrationStatus.INACTIVE]),
                'error_integrations': len([i for i in self.integrations.values() 
                                         if i.status == IntegrationStatus.ERROR])
            },
            'by_type': {},
            'integrations': [],
            'generated_at': datetime.now().isoformat()
        }
        
        # 按类型统计
        for integration in self.integrations.values():
            type_name = integration.integration_type.value
            if type_name not in report['by_type']:
                report['by_type'][type_name] = 0
            report['by_type'][type_name] += 1
        
        # 集成详情
        for integration in self.integrations.values():
            status_info = self.get_integration_status(integration.id)
            report['integrations'].append(status_info)
        
        return report
    
    def cleanup_old_data(self, days: int = 30):
        """清理旧数据"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            cleaned_count = 0
            
            # 清理数据文件
            for data_file in self.data_dir.glob("*.json"):
                if data_file.stat().st_mtime < cutoff_date.timestamp():
                    data_file.unlink()
                    cleaned_count += 1
            
            # 清理日志文件
            for log_file in self.logs_dir.glob("*.log"):
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    log_file.unlink()
                    cleaned_count += 1
            
            self.logger.info(f"已清理 {cleaned_count} 个旧文件")
            return cleaned_count
        
        except Exception as e:
            self.logger.error(f"清理旧数据失败: {e}")
            return 0

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='YDS-Lab 集成管理工具')
    parser.add_argument('--project-root', help='指定项目根目录路径')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 列出集成
    list_parser = subparsers.add_parser('list', help='列出集成')
    list_parser.add_argument('--status', choices=['active', 'inactive', 'error', 'testing', 'maintenance'], 
                           help='按状态过滤')
    list_parser.add_argument('--type', help='按类型过滤')
    
    # 测试集成
    test_parser = subparsers.add_parser('test', help='测试集成')
    test_parser.add_argument('integration_id', help='集成ID')
    test_parser.add_argument('--endpoint', help='指定端点')
    
    # 调用端点
    call_parser = subparsers.add_parser('call', help='调用集成端点')
    call_parser.add_argument('integration_id', help='集成ID')
    call_parser.add_argument('endpoint', help='端点名称')
    call_parser.add_argument('--data', help='请求数据（JSON格式）')
    
    # 同步数据
    sync_parser = subparsers.add_parser('sync', help='同步数据')
    sync_parser.add_argument('integration_id', help='集成ID')
    sync_parser.add_argument('--direction', choices=['pull', 'push', 'bidirectional'], 
                           help='同步方向')
    
    # 状态检查
    status_parser = subparsers.add_parser('status', help='检查集成状态')
    status_parser.add_argument('integration_id', help='集成ID')
    
    # 生成报告
    report_parser = subparsers.add_parser('report', help='生成集成报告')
    report_parser.add_argument('--output', help='输出文件路径')
    
    # 清理数据
    cleanup_parser = subparsers.add_parser('cleanup', help='清理旧数据')
    cleanup_parser.add_argument('--days', type=int, default=30, help='保留天数')
    
    args = parser.parse_args()
    
    manager = IntegrationManager(args.project_root)
    
    if args.command == 'list':
        status_filter = IntegrationStatus(args.status) if args.status else None
        type_filter = IntegrationType(args.type) if args.type else None
        
        integrations = manager.list_integrations(status_filter, type_filter)
        
        print(f"📋 集成列表 (共{len(integrations)}个):")
        print("="*60)
        
        for integration in integrations:
            print(f"ID: {integration.id}")
            print(f"名称: {integration.name}")
            print(f"类型: {integration.integration_type.value}")
            print(f"状态: {integration.status.value}")
            print(f"基础URL: {integration.base_url}")
            print(f"端点数量: {len(integration.endpoints)}")
            print(f"创建时间: {integration.created_at}")
            print("-" * 60)
    
    elif args.command == 'test':
        result = manager.test_integration(args.integration_id, args.endpoint)
        
        print(f"🧪 集成测试结果:")
        print(f"集成ID: {result.integration_id}")
        print(f"端点: {result.endpoint}")
        print(f"成功: {'✅' if result.success else '❌'}")
        if result.status_code:
            print(f"状态码: {result.status_code}")
        print(f"执行时间: {result.execution_time:.2f}秒")
        if result.error_message:
            print(f"错误信息: {result.error_message}")
        if result.response_data:
            print(f"响应数据: {json.dumps(result.response_data, indent=2, ensure_ascii=False)}")
    
    elif args.command == 'call':
        data = None
        if args.data:
            try:
                data = json.loads(args.data)
            except json.JSONDecodeError:
                print("❌ 无效的JSON数据格式")
                return
        
        result = manager.call_endpoint(args.integration_id, args.endpoint, data)
        
        print(f"📞 端点调用结果:")
        print(f"集成ID: {result.integration_id}")
        print(f"端点: {result.endpoint}")
        print(f"成功: {'✅' if result.success else '❌'}")
        if result.status_code:
            print(f"状态码: {result.status_code}")
        print(f"执行时间: {result.execution_time:.2f}秒")
        if result.error_message:
            print(f"错误信息: {result.error_message}")
        if result.response_data:
            print(f"响应数据: {json.dumps(result.response_data, indent=2, ensure_ascii=False)}")
    
    elif args.command == 'sync':
        direction = SyncDirection(args.direction) if args.direction else None
        result = manager.sync_data(args.integration_id, direction)
        
        print(f"🔄 数据同步结果:")
        print(f"集成ID: {result.integration_id}")
        print(f"方向: {result.direction.value}")
        print(f"成功: {'✅' if result.success else '❌'}")
        print(f"处理记录: {result.records_processed}")
        print(f"成功记录: {result.records_success}")
        print(f"失败记录: {result.records_failed}")
        print(f"执行时间: {result.execution_time:.2f}秒")
        if result.error_message:
            print(f"错误信息: {result.error_message}")
    
    elif args.command == 'status':
        status = manager.get_integration_status(args.integration_id)
        
        if 'error' in status:
            print(f"❌ {status['error']}")
            return
        
        print(f"📊 集成状态:")
        print(f"ID: {status['id']}")
        print(f"名称: {status['name']}")
        print(f"类型: {status['type']}")
        print(f"状态: {status['status']}")
        print(f"基础URL: {status['base_url']}")
        print(f"端点数量: {status['endpoints_count']}")
        print(f"认证配置: {'是' if status['has_auth'] else '否'}")
        print(f"同步配置: {'是' if status['has_sync'] else '否'}")
        print(f"最后同步: {status['last_sync'] or '从未同步'}")
        
        conn_test = status['connection_test']
        print(f"连接测试: {'✅' if conn_test['success'] else '❌'}")
        if conn_test['status_code']:
            print(f"  状态码: {conn_test['status_code']}")
        print(f"  响应时间: {conn_test['response_time']:.2f}秒")
        if conn_test['error']:
            print(f"  错误: {conn_test['error']}")
    
    elif args.command == 'report':
        report = manager.generate_integration_report()
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"✅ 报告已保存到: {args.output}")
        else:
            print("📊 集成报告:")
            print("="*40)
            
            summary = report['summary']
            print(f"总集成数: {summary['total_integrations']}")
            print(f"活跃集成: {summary['active_integrations']}")
            print(f"非活跃集成: {summary['inactive_integrations']}")
            print(f"错误集成: {summary['error_integrations']}")
            
            print(f"\n按类型统计:")
            for type_name, count in report['by_type'].items():
                print(f"  {type_name}: {count}")
            
            print(f"\n生成时间: {report['generated_at']}")
    
    elif args.command == 'cleanup':
        cleaned_count = manager.cleanup_old_data(args.days)
        print(f"🧹 已清理 {cleaned_count} 个旧文件 (保留{args.days}天内的数据)")
    
    else:
        # 默认显示状态
        integrations = manager.list_integrations()
        
        print("🔗 集成管理器")
        print("="*30)
        print(f"项目路径: {manager.project_root}")
        print(f"集成目录: {manager.integration_dir}")
        print(f"总集成数: {len(integrations)}")
        
        if integrations:
            active_count = len([i for i in integrations if i.status == IntegrationStatus.ACTIVE])
            print(f"活跃集成: {active_count}")
            
            print(f"\n📋 集成列表:")
            for integration in integrations[:5]:  # 显示前5个
                print(f"  {integration.name} ({integration.integration_type.value}) - {integration.status.value}")
            
            if len(integrations) > 5:
                print(f"  ... 还有 {len(integrations) - 5} 个集成")

if __name__ == "__main__":
    main()