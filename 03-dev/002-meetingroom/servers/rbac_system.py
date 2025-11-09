"""
YDS AI RBAC权限系统
实现基于角色的访问控制和操作审计
"""

import os
import json
import jwt
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass
from enum import Enum
import logging
from functools import wraps

logger = logging.getLogger(__name__)


class Permission(Enum):
    """权限枚举"""
    # 会议权限
    CREATE_MEETING = "create_meeting"
    JOIN_MEETING = "join_meeting"
    MODERATE_MEETING = "moderate_meeting"
    END_MEETING = "end_meeting"
    
    # 文档权限
    READ_DOCS = "read_docs"
    WRITE_DOCS = "write_docs"
    DELETE_DOCS = "delete_docs"
    SHARE_DOCS = "share_docs"
    
    # 系统权限
    ADMIN_SYSTEM = "admin_system"
    VIEW_AUDIT = "view_audit"
    MANAGE_USERS = "manage_users"
    MANAGE_ROLES = "manage_roles"
    
    # 投票权限
    CREATE_VOTE = "create_vote"
    PARTICIPATE_VOTE = "participate_vote"
    VIEW_VOTE_RESULTS = "view_vote_results"
    
    # LM系统权限
    ACCESS_LM = "access_lm"
    MANAGE_LM = "manage_lm"

 
class ResourceType(Enum):
    """资源类型"""
    MEETING = "meeting"
    DOCUMENT = "document"
    VOTE = "vote"
    SYSTEM = "system"
    LM_COMPONENT = "lm_component"

 
@dataclass
class Role:
    """角色定义"""
    name: str
    display_name: str
    description: str
    permissions: Set[Permission]
    resource_access: Dict[ResourceType, Set[str]]  # 资源类型 -> 资源ID集合
    is_system_role: bool = False
    created_at: datetime = None
    updated_at: datetime = None

 
@dataclass
class User:
    """用户定义"""
    user_id: str
    username: str
    display_name: str
    email: str
    roles: Set[str]
    is_active: bool = True
    created_at: datetime = None
    last_login: datetime = None
    metadata: Dict[str, Any] = None

 
@dataclass
class AccessControlEntry:
    """访问控制条目"""
    resource_type: ResourceType
    resource_id: str
    user_id: str
    permissions: Set[Permission]
    granted_by: str
    granted_at: datetime
    expires_at: Optional[datetime] = None

 
@dataclass
class AuditEntry:
    """审计条目"""
    audit_id: str
    user_id: str
    username: str
    action: str
    resource_type: ResourceType
    resource_id: str
    timestamp: datetime
    success: bool
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Dict[str, Any] = None

 
class RBACSystem:
    """RBAC权限系统"""
    
    def __init__(self, config_path: str = None, jwt_secret: str = None):
        # 统一配置路径优先使用 config/rbac_config.json，保留根路径回退
        if config_path:
            resolved_config_path = config_path
        else:
            candidate_paths = [
                os.path.join("config", "rbac_config.json"),  # 优先统一到 config/
                "rbac_config.json",  # 回退到根路径（兼容旧版本）
            ]
            resolved_config_path = None
            for p in candidate_paths:
                if os.path.exists(p):
                    resolved_config_path = p
                    break
            # 如果都不存在，默认指向 config 路径（后续保存时会创建）
            if resolved_config_path is None:
                resolved_config_path = os.path.join("config", "rbac_config.json")

        self.config_path = resolved_config_path
        logger.info(f"[RBACSystem] 使用配置路径: {self.config_path}")
        self.jwt_secret = jwt_secret or "yds-ai-rbac-secret-key"
        self.roles: Dict[str, Role] = {}
        self.users: Dict[str, User] = {}
        self.acl_entries: List[AccessControlEntry] = []
        self.audit_log: List[AuditEntry] = []
        self._load_config()
        self._setup_default_roles()
    
    def _load_config(self):
        """加载配置"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                    # 加载角色
                    for role_data in config.get('roles', []):
                        role = Role(
                            name=role_data['name'],
                            display_name=role_data['display_name'],
                            description=role_data['description'],
                            permissions={Permission(p) for p in role_data['permissions']},
                            resource_access={ResourceType(k): set(v) for k, v in role_data['resource_access'].items()},
                            is_system_role=role_data.get('is_system_role', False),
                            created_at=(
                                datetime.fromisoformat(role_data['created_at'])
                                if role_data.get('created_at') else None
                            ),
                            updated_at=(
                                datetime.fromisoformat(role_data['updated_at'])
                                if role_data.get('updated_at') else None
                            )
                        )
                        self.roles[role.name] = role
                    
                    # 加载用户
                    for user_data in config.get('users', []):
                        user = User(
                            user_id=user_data['user_id'],
                            username=user_data['username'],
                            display_name=user_data['display_name'],
                            email=user_data['email'],
                            roles=set(user_data['roles']),
                            is_active=user_data.get('is_active', True),
                            created_at=(
                                datetime.fromisoformat(user_data['created_at'])
                                if user_data.get('created_at') else None
                            ),
                            last_login=(
                                datetime.fromisoformat(user_data['last_login'])
                                if user_data.get('last_login') else None
                            ),
                            metadata=user_data.get('metadata', {})
                        )
                        self.users[user.user_id] = user
        except Exception as e:
            logger.error(f"加载RBAC配置失败: {e}")
    
    def _save_config(self):
        """保存配置"""
        try:
            config = {
                'roles': [],
                'users': []
            }
            
            # 保存角色
            for role in self.roles.values():
                role_data = {
                    'name': role.name,
                    'display_name': role.display_name,
                    'description': role.description,
                    'permissions': [p.value for p in role.permissions],
                    'resource_access': {k.value: list(v) for k, v in role.resource_access.items()},
                    'is_system_role': role.is_system_role,
                    'created_at': role.created_at.isoformat() if role.created_at else None,
                    'updated_at': role.updated_at.isoformat() if role.updated_at else None
                }
                config['roles'].append(role_data)
            
            # 保存用户
            for user in self.users.values():
                user_data = {
                    'user_id': user.user_id,
                    'username': user.username,
                    'display_name': user.display_name,
                    'email': user.email,
                    'roles': list(user.roles),
                    'is_active': user.is_active,
                    'created_at': user.created_at.isoformat() if user.created_at else None,
                    'last_login': user.last_login.isoformat() if user.last_login else None,
                    'metadata': user.metadata
                }
                config['users'].append(user_data)
            
            # 确保保存目录存在
            save_dir = os.path.dirname(self.config_path) or "."
            os.makedirs(save_dir, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存RBAC配置失败: {e}")
    
    def _setup_default_roles(self):
        """设置默认角色"""
        if not self.roles:
            default_roles = [
                Role(
                    name="CEO",
                    display_name="首席执行官",
                    description="公司最高管理者，拥有所有权限",
                    permissions=set(Permission),  # 所有权限
                    resource_access={
                        ResourceType.MEETING: {"*"},
                        ResourceType.DOCUMENT: {"*"},
                        ResourceType.VOTE: {"*"},
                        ResourceType.SYSTEM: {"*"},
                        ResourceType.LM_COMPONENT: {"*"}
                    },
                    is_system_role=True,
                    created_at=datetime.now()
                ),
                Role(
                    name="CFO",
                    display_name="首席财务官",
                    description="财务负责人，拥有财务相关权限",
                    permissions={
                        Permission.CREATE_MEETING, Permission.JOIN_MEETING, Permission.MODERATE_MEETING,
                        Permission.READ_DOCS, Permission.WRITE_DOCS, Permission.SHARE_DOCS,
                        Permission.CREATE_VOTE, Permission.PARTICIPATE_VOTE, Permission.VIEW_VOTE_RESULTS,
                        Permission.ACCESS_LM, Permission.VIEW_AUDIT
                    },
                    resource_access={
                        ResourceType.MEETING: {"financial", "strategic"},
                        ResourceType.DOCUMENT: {"financial", "strategic"},
                        ResourceType.VOTE: {"financial", "strategic"},
                        ResourceType.LM_COMPONENT: {"financial_analysis"}
                    },
                    is_system_role=True,
                    created_at=datetime.now()
                ),
                Role(
                    name="CTO",
                    display_name="首席技术官",
                    description="技术负责人，拥有技术相关权限",
                    permissions={
                        Permission.CREATE_MEETING, Permission.JOIN_MEETING, Permission.MODERATE_MEETING,
                        Permission.READ_DOCS, Permission.WRITE_DOCS, Permission.DELETE_DOCS, Permission.SHARE_DOCS,
                        Permission.CREATE_VOTE, Permission.PARTICIPATE_VOTE, Permission.VIEW_VOTE_RESULTS,
                        Permission.ACCESS_LM, Permission.MANAGE_LM, Permission.VIEW_AUDIT
                    },
                    resource_access={
                        ResourceType.MEETING: {"technical", "strategic"},
                        ResourceType.DOCUMENT: {"technical", "strategic"},
                        ResourceType.VOTE: {"technical", "strategic"},
                        ResourceType.LM_COMPONENT: {"*"}
                    },
                    is_system_role=True,
                    created_at=datetime.now()
                ),
                Role(
                    name="项目协调者",
                    display_name="项目协调者",
                    description="项目管理和协调角色",
                    permissions={
                        Permission.CREATE_MEETING, Permission.JOIN_MEETING, Permission.MODERATE_MEETING,
                        Permission.READ_DOCS, Permission.WRITE_DOCS, Permission.SHARE_DOCS,
                        Permission.CREATE_VOTE, Permission.PARTICIPATE_VOTE, Permission.VIEW_VOTE_RESULTS,
                        Permission.ACCESS_LM
                    },
                    resource_access={
                        ResourceType.MEETING: {"operational", "technical"},
                        ResourceType.DOCUMENT: {"operational", "technical"},
                        ResourceType.VOTE: {"operational", "technical"},
                        ResourceType.LM_COMPONENT: {"project_management"}
                    },
                    is_system_role=True,
                    created_at=datetime.now()
                ),
                Role(
                    name="前端开发智能体",
                    display_name="前端开发智能体",
                    description="前端开发专用智能体",
                    permissions={
                        Permission.JOIN_MEETING, Permission.READ_DOCS, Permission.WRITE_DOCS,
                        Permission.PARTICIPATE_VOTE, Permission.ACCESS_LM
                    },
                    resource_access={
                        ResourceType.MEETING: {"technical"},
                        ResourceType.DOCUMENT: {"technical"},
                        ResourceType.VOTE: {"technical"},
                        ResourceType.LM_COMPONENT: {"frontend_development"}
                    },
                    is_system_role=True,
                    created_at=datetime.now()
                ),
                Role(
                    name="后端开发智能体",
                    display_name="后端开发智能体",
                    description="后端开发专用智能体",
                    permissions={
                        Permission.JOIN_MEETING, Permission.READ_DOCS, Permission.WRITE_DOCS,
                        Permission.PARTICIPATE_VOTE, Permission.ACCESS_LM
                    },
                    resource_access={
                        ResourceType.MEETING: {"technical"},
                        ResourceType.DOCUMENT: {"technical"},
                        ResourceType.VOTE: {"technical"},
                        ResourceType.LM_COMPONENT: {"backend_development"}
                    },
                    is_system_role=True,
                    created_at=datetime.now()
                ),
                Role(
                    name="会议秘书",
                    display_name="会议秘书",
                    description="会议记录和管理专用智能体",
                    permissions={
                        Permission.JOIN_MEETING, Permission.READ_DOCS, Permission.WRITE_DOCS,
                        Permission.ACCESS_LM
                    },
                    resource_access={
                        ResourceType.MEETING: {"*"},
                        ResourceType.DOCUMENT: {"meeting_records"},
                        ResourceType.LM_COMPONENT: {"meeting_assistant"}
                    },
                    is_system_role=True,
                    created_at=datetime.now()
                )
            ]
            
            for role in default_roles:
                self.roles[role.name] = role
            
            # 创建默认用户
            default_users = [
                User(
                    user_id="admin",
                    username="admin",
                    display_name="系统管理员",
                    email="admin@yds-ai.com",
                    roles={"CEO"},  # 给admin用户CEO权限
                    created_at=datetime.now()
                ),
                User(
                    user_id="ceo_001",
                    username="ceo",
                    display_name="CEO智能体",
                    email="ceo@yds-ai.com",
                    roles={"CEO"},
                    created_at=datetime.now()
                ),
                User(
                    user_id="cfo_001",
                    username="cfo",
                    display_name="CFO智能体",
                    email="cfo@yds-ai.com",
                    roles={"CFO"},
                    created_at=datetime.now()
                ),
                User(
                    user_id="coordinator_001",
                    username="coordinator",
                    display_name="项目协调者",
                    email="coordinator@yds-ai.com",
                    roles={"项目协调者"},
                    created_at=datetime.now()
                )
            ]
            
            for user in default_users:
                self.users[user.user_id] = user
            
            self._save_config()
    
    def create_user(self, user_id: str, username: str, display_name: str, email: str, roles: Set[str]) -> bool:
        """创建用户"""
        if user_id in self.users:
            return False
        
        # 验证角色存在
        for role_name in roles:
            if role_name not in self.roles:
                return False
        
        user = User(
            user_id=user_id,
            username=username,
            display_name=display_name,
            email=email,
            roles=roles,
            created_at=datetime.now()
        )
        
        self.users[user_id] = user
        self._save_config()
        
        self._audit_log(
            "system",
            "CREATE_USER",
            ResourceType.SYSTEM,
            user_id,
            True,
            details={
                "username": username,
                "roles": list(roles)
            }
        )
        
        return True
    
    def authenticate_user(self, username: str, password: str = None) -> Optional[str]:
        """用户认证，返回JWT令牌"""
        # 查找用户
        for user_id, user in self.users.items():
            if user.username == username:
                # 简化的密码验证逻辑（演示用）
                # 实际应用中应该使用哈希密码验证
                if password is None:
                    # 如果没有提供密码，直接生成令牌（向后兼容）
                    return self.generate_jwt_token(user_id)
                else:
                    # 简单的密码验证：admin用户密码为admin123，其他用户密码为用户名
                    expected_password = "admin123" if username == "admin" else username
                    if password == expected_password:
                        return self.generate_jwt_token(user_id)
                    else:
                        return None
        return None
    
    def has_permission(
        self,
        user_id: str,
        permission: Permission,
        resource_type: ResourceType = None,
        resource_id: str = None
    ) -> bool:
        """检查用户是否有指定权限"""
        user = self.users.get(user_id)
        if not user or not user.is_active:
            return False
        
        # 检查用户角色权限
        for role_name in user.roles:
            role = self.roles.get(role_name)
            if not role:
                continue
            
            if permission in role.permissions:
                # 如果指定了资源，检查资源访问权限
                if resource_type and resource_id:
                    resource_access = role.resource_access.get(resource_type, set())
                    if "*" in resource_access or resource_id in resource_access:
                        return True
                else:
                    return True
        
        # 检查ACL条目
        for acl in self.acl_entries:
            if (
                acl.user_id == user_id
                and permission in acl.permissions
                and (not resource_type or acl.resource_type == resource_type)
                and (not resource_id or acl.resource_id == resource_id)
                and (not acl.expires_at or acl.expires_at > datetime.now())
            ):
                return True
        
        return False
    
    def grant_permission(
        self,
        user_id: str,
        permission: Permission,
        resource_type: ResourceType,
        resource_id: str,
        granted_by: str,
        expires_at: datetime = None
    ) -> bool:
        """授予权限"""
        if user_id not in self.users:
            return False
        
        acl_entry = AccessControlEntry(
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            permissions={permission},
            granted_by=granted_by,
            granted_at=datetime.now(),
            expires_at=expires_at
        )
        
        self.acl_entries.append(acl_entry)
        
        self._audit_log(
            granted_by,
            "GRANT_PERMISSION",
            resource_type,
            resource_id,
            True,
            details={"target_user": user_id, "permission": permission.value}
        )
        
        return True
    
    def revoke_permission(
        self,
        user_id: str,
        permission: Permission,
        resource_type: ResourceType,
        resource_id: str,
        revoked_by: str
    ) -> bool:
        """撤销权限"""
        original_count = len(self.acl_entries)
        self.acl_entries = [
            acl for acl in self.acl_entries
            if not (
                acl.user_id == user_id
                and permission in acl.permissions
                and acl.resource_type == resource_type
                and acl.resource_id == resource_id
            )
        ]
        removed = original_count != len(self.acl_entries)
        
        if removed:
            self._audit_log(
                revoked_by,
                "REVOKE_PERMISSION",
                resource_type,
                resource_id,
                True,
                details={
                    "target_user": user_id,
                    "permission": permission.value
                }
            )
        
        return removed
    
    def generate_jwt_token(self, user_id: str, expires_in_hours: int = 24) -> Optional[str]:
        """生成JWT令牌"""
        user = self.users.get(user_id)
        if not user or not user.is_active:
            return None
        
        payload = {
            'user_id': user_id,
            'username': user.username,
            'roles': list(user.roles),
            'exp': datetime.utcnow() + timedelta(hours=expires_in_hours),
            'iat': datetime.utcnow()
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm='HS256')
        
        # 更新最后登录时间
        user.last_login = datetime.now()
        self._save_config()
        
        self._audit_log(user_id, "LOGIN", ResourceType.SYSTEM, "jwt_token", True)
        
        return token
    
    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证JWT令牌"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            user_id = payload.get('user_id')
            
            # 检查用户是否仍然活跃
            user = self.users.get(user_id)
            if not user or not user.is_active:
                return None
            
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def _audit_log(
        self,
        user_id: str,
        action: str,
        resource_type: ResourceType,
        resource_id: str,
        success: bool,
        ip_address: str = None,
        user_agent: str = None,
        details: Dict[str, Any] = None
    ):
        """记录审计日志"""
        audit_id = hashlib.md5(f"{user_id}_{action}_{resource_id}_{datetime.now().isoformat()}".encode()).hexdigest()
        
        user = self.users.get(user_id)
        username = user.username if user else user_id
        
        audit_entry = AuditEntry(
            audit_id=audit_id,
            user_id=user_id,
            username=username,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            timestamp=datetime.now(),
            success=success,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {}
        )
        
        self.audit_log.append(audit_entry)
        
        # 保持审计日志数量在合理范围内
        if len(self.audit_log) > 50000:
            self.audit_log = self.audit_log[-25000:]
    
    def get_audit_logs(
        self,
        user_id: str = None,
        action: str = None,
        resource_type: ResourceType = None,
        start_time: datetime = None,
        end_time: datetime = None,
        limit: int = 1000
    ) -> List[AuditEntry]:
        """获取审计日志"""
        filtered_logs = self.audit_log
        
        if user_id:
            filtered_logs = [log for log in filtered_logs if log.user_id == user_id]
        
        if action:
            filtered_logs = [log for log in filtered_logs if log.action == action]
        
        if resource_type:
            filtered_logs = [log for log in filtered_logs if log.resource_type == resource_type]
        
        if start_time:
            filtered_logs = [log for log in filtered_logs if log.timestamp >= start_time]
        
        if end_time:
            filtered_logs = [log for log in filtered_logs if log.timestamp <= end_time]
        
        # 按时间倒序排列并限制数量
        filtered_logs = sorted(filtered_logs, key=lambda x: x.timestamp, reverse=True)[:limit]
        
        return filtered_logs
    
    def require_permission(self, permission: Permission, resource_type: ResourceType = None, resource_id: str = None):
        """权限装饰器"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # 从请求中获取用户信息（这里简化处理）
                user_id = kwargs.get('user_id') or getattr(args[0], 'current_user_id', None)
                if not user_id:
                    raise PermissionError("未找到用户信息")
                
                if not self.has_permission(user_id, permission, resource_type, resource_id):
                    self._audit_log(
                        user_id,
                        func.__name__,
                        resource_type or ResourceType.SYSTEM,
                        resource_id or "unknown",
                        False,
                        details={"required_permission": permission.value}
                    )
                    raise PermissionError(f"权限不足，需要 {permission.value} 权限")
                
                # 记录成功的操作
                result = func(*args, **kwargs)
                self._audit_log(
                    user_id,
                    func.__name__,
                    resource_type or ResourceType.SYSTEM,
                    resource_id or "unknown",
                    True
                )
                return result
            return wrapper
        return decorator


# 全局实例
rbac_system = RBACSystem()