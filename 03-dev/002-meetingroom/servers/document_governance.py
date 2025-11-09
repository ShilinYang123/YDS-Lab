"""
YDS AI 文档治理系统

功能：实现目录白名单、角色访问控制与操作审计
说明：本模块提供统一的配置读取与默认规则，并与 RBAC 角色命名保持一致（如“项目协调者”“前端开发智能体”“后端开发智能体”“CEO”“CTO”“CFO”）。
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DocumentCategory(Enum):
    """文档分类"""
    STRATEGIC = "strategic"          # 战略规划
    OPERATIONAL = "operational"      # 运营管理
    TECHNICAL = "technical"          # 技术文档
    FINANCIAL = "financial"          # 财务文档
    MARKETING = "marketing"          # 市场营销
    HR = "hr"                        # 人力资源
    LEGAL = "legal"                  # 法务合规
    PUBLIC = "public"                # 公开文档


class AccessLevel(Enum):
    """访问等级"""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    NONE = "none"


class AuditAction(Enum):
    """审计动作"""
    ACCESS = "access"
    MODIFY = "modify"
    DELETE = "delete"
    SHARE = "share"
    DOWNLOAD = "download"


@dataclass
class DirectoryRule:
    """目录规则
    - path：目录路径（前缀匹配）
    - category：文档类别
    - allowed_roles：允许访问的角色集合；支持 "*" 表示所有角色
    - access_levels：不同角色的访问等级；支持 "*" 兜底等级
    - description：规则说明
    - auto_approval：是否自动审批访问请求
    - requires_audit：是否记录审计日志
    """
    path: str
    category: DocumentCategory
    allowed_roles: Set[str]
    access_levels: Dict[str, AccessLevel]
    description: str
    auto_approval: bool = False
    requires_audit: bool = True


@dataclass
class AccessRequest:
    """访问请求"""
    request_id: str
    user_id: str
    user_role: str
    path: str
    action: AuditAction
    timestamp: datetime
    approved: Optional[bool] = None
    approver: Optional[str] = None
    reason: Optional[str] = None


@dataclass
class AuditLog:
    """审计日志"""
    log_id: str
    user_id: str
    user_role: str
    path: str
    action: AuditAction
    timestamp: datetime
    success: bool
    details: Dict[str, Any]


class DocumentGovernanceManager:
    """文档治理管理器"""

    def __init__(self, config_path: str = None):
        # 统一配置路径：优先使用 config/document_governance_config.json，保留根目录回退
        if config_path:
            resolved_config_path = config_path
        else:
            candidate_paths = [
                os.path.join("config", "document_governance_config.json"),
                "document_governance_config.json",
            ]
            resolved_config_path = None
            for p in candidate_paths:
                if os.path.exists(p):
                    resolved_config_path = p
                    break
            if resolved_config_path is None:
                resolved_config_path = os.path.join("config", "document_governance_config.json")
        self.config_path = resolved_config_path
        logger.info(f"[DocumentGovernanceManager] 使用配置路径: {self.config_path}")
        self.directory_rules: Dict[str, DirectoryRule] = {}
        self.access_requests: Dict[str, AccessRequest] = {}
        self.audit_logs: List[AuditLog] = []
        self._load_config()
        self._setup_default_rules()

    def _load_config(self):
        """加载配置"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 加载目录规则
                    for rule_data in config.get('directory_rules', []):
                        rule = DirectoryRule(
                            path=rule_data['path'],
                            category=DocumentCategory(rule_data['category']),
                            allowed_roles=set(rule_data['allowed_roles']),
                            access_levels={k: AccessLevel(v) for k, v in rule_data['access_levels'].items()},
                            description=rule_data['description'],
                            auto_approval=rule_data.get('auto_approval', False),
                            requires_audit=rule_data.get('requires_audit', True)
                        )
                        self.directory_rules[rule.path] = rule
        except Exception as e:
            logger.error(f"加载配置失败: {e}")

    def _save_config(self):
        """保存配置"""
        try:
            config = {
                'directory_rules': []
            }
            for rule in self.directory_rules.values():
                rule_data = {
                    'path': rule.path,
                    'category': rule.category.value,
                    'allowed_roles': list(rule.allowed_roles),
                    'access_levels': {k: v.value for k, v in rule.access_levels.items()},
                    'description': rule.description,
                    'auto_approval': rule.auto_approval,
                    'requires_audit': rule.requires_audit
                }
                config['directory_rules'].append(rule_data)

            # 确保存储目录存在
            save_dir = os.path.dirname(self.config_path) or "."
            os.makedirs(save_dir, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存配置失败: {e}")

    def _setup_default_rules(self):
        """设置默认规则"""
        if not self.directory_rules:
            default_rules = [
                DirectoryRule(
                    path="S:/YDS-Lab/01-struc/docs/YDS-AI-战略规划",
                    category=DocumentCategory.STRATEGIC,
                    allowed_roles={"CEO", "CFO", "CTO"},
                    access_levels={"CEO": AccessLevel.ADMIN, "CFO": AccessLevel.READ, "CTO": AccessLevel.READ},
                    description="公司战略规划相关文档",
                    auto_approval=False,
                    requires_audit=True
                ),
                DirectoryRule(
                    path="S:/YDS-Lab/01-struc/Agents/07-marketing_director",
                    category=DocumentCategory.MARKETING,
                    allowed_roles={"CEO", "项目协调者"},
                    access_levels={"CEO": AccessLevel.ADMIN, "项目协调者": AccessLevel.WRITE},
                    description="市场营销部门文档与素材",
                    auto_approval=True,
                    requires_audit=True
                ),
                DirectoryRule(
                    path="S:/YDS-Lab/01-struc/04-dev-team",
                    category=DocumentCategory.TECHNICAL,
                    allowed_roles={
                        "CTO",
                        "前端开发智能体",
                        "后端开发智能体",
                        "项目协调者"
                    },
                    access_levels={
                        "CTO": AccessLevel.ADMIN,
                        "前端开发智能体": AccessLevel.WRITE,
                        "后端开发智能体": AccessLevel.WRITE,
                        "项目协调者": AccessLevel.READ
                    },
                    description="研发团队技术文档与设计资料",
                    auto_approval=True,
                    requires_audit=True
                ),
                DirectoryRule(
                    path="S:/YDS-Lab/01-struc/02-finance",
                    category=DocumentCategory.FINANCIAL,
                    allowed_roles={"CEO", "CFO"},
                    access_levels={"CEO": AccessLevel.ADMIN, "CFO": AccessLevel.ADMIN},
                    description="公司财务部门文档",
                    auto_approval=False,
                    requires_audit=True
                ),
                DirectoryRule(
                    path="S:/YDS-Lab/04-prod",
                    category=DocumentCategory.OPERATIONAL,
                    allowed_roles={
                        "CEO",
                        "项目协调者",
                        "前端开发智能体",
                        "后端开发智能体"
                    },
                    access_levels={
                        "CEO": AccessLevel.ADMIN,
                        "项目协调者": AccessLevel.WRITE,
                        "前端开发智能体": AccessLevel.WRITE,
                        "后端开发智能体": AccessLevel.WRITE
                    },
                    description="生产环境部署与运维相关文档",
                    auto_approval=True,
                    requires_audit=True
                ),
                DirectoryRule(
                    path="S:/YDS-Lab/tools",
                    category=DocumentCategory.TECHNICAL,
                    allowed_roles={
                        "CTO",
                        "前端开发智能体",
                        "后端开发智能体",
                        "项目协调者"
                    },
                    access_levels={
                        "CTO": AccessLevel.ADMIN,
                        "前端开发智能体": AccessLevel.WRITE,
                        "后端开发智能体": AccessLevel.WRITE,
                        "项目协调者": AccessLevel.READ
                    },
                    description="工具与脚本目录",
                    auto_approval=True,
                    requires_audit=False
                ),
                DirectoryRule(
                    path="S:/YDS-Lab/Public",
                    category=DocumentCategory.PUBLIC,
                    allowed_roles={"*"},  # 所有角色
                    access_levels={"*": AccessLevel.READ},
                    description="公开共享文档",
                    auto_approval=True,
                    requires_audit=False
                )
            ]

            for rule in default_rules:
                self.directory_rules[rule.path] = rule

            self._save_config()

    def check_access(
        self,
        user_role: str,
        path: str,
        action: AuditAction,
        user_id: Optional[str] = None
    ) -> Tuple[bool, str]:
        """检查访问权限"""
        # 标准化路径
        normalized_path = os.path.normpath(path)

        # 查找匹配的规则
        matching_rule = None
        for rule_path, rule in self.directory_rules.items():
            if normalized_path.startswith(os.path.normpath(rule_path)):
                matching_rule = rule
                break

        if not matching_rule:
            return False, "未找到匹配的访问规则"

        # 检查角色权限
        if (
            "*" not in matching_rule.allowed_roles
            and user_role not in matching_rule.allowed_roles
        ):
            return False, f"角色 {user_role} 无权访问该目录"

        # 检查访问等级
        required_level = self._get_required_access_level(action)
        user_level = (
            matching_rule.access_levels.get(user_role)
            or matching_rule.access_levels.get("*", AccessLevel.NONE)
        )

        if not self._has_sufficient_access(user_level, required_level):
            return False, f"权限不足，需要 {required_level.value} 等级"

        return True, "访问允许"

    def _get_required_access_level(self, action: AuditAction) -> AccessLevel:
        """获取动作所需的访问等级"""
        level_map = {
            AuditAction.ACCESS: AccessLevel.READ,
            AuditAction.DOWNLOAD: AccessLevel.READ,
            AuditAction.MODIFY: AccessLevel.WRITE,
            AuditAction.DELETE: AccessLevel.ADMIN,
            AuditAction.SHARE: AccessLevel.WRITE
        }
        return level_map.get(action, AccessLevel.READ)

    def _has_sufficient_access(self, user_level: AccessLevel, required_level: AccessLevel) -> bool:
        """检查用户访问等级是否满足要求"""
        level_hierarchy = {
            AccessLevel.NONE: 0,
            AccessLevel.READ: 1,
            AccessLevel.WRITE: 2,
            AccessLevel.ADMIN: 3
        }
        return level_hierarchy.get(user_level, 0) >= level_hierarchy.get(required_level, 0)

    def request_access(self, user_id: str, user_role: str, path: str, action: AuditAction, reason: str = None) -> str:
        """提交访问请求"""
        request_id = hashlib.md5(f"{user_id}_{path}_{action.value}_{datetime.now().isoformat()}".encode()).hexdigest()

        request = AccessRequest(
            request_id=request_id,
            user_id=user_id,
            user_role=user_role,
            path=path,
            action=action,
            timestamp=datetime.now(),
            reason=reason
        )

        # 自动审批
        normalized_path = os.path.normpath(path)
        matching_rule = None
        for rule_path, rule in self.directory_rules.items():
            if normalized_path.startswith(os.path.normpath(rule_path)):
                matching_rule = rule
                break

        if matching_rule and matching_rule.auto_approval:
            allowed, _ = self.check_access(user_role, path, action)
            if allowed:
                request.approved = True
                request.approver = "system"

        self.access_requests[request_id] = request
        return request_id

    def approve_request(self, request_id: str, approver: str, approved: bool, reason: str = None) -> bool:
        """批准/拒绝访问请求"""
        if request_id not in self.access_requests:
            return False

        request = self.access_requests[request_id]
        request.approved = approved
        request.approver = approver
        if reason:
            request.reason = reason

        return True

    def log_access(
        self,
        user_id: str,
        user_role: str,
        path: str,
        action: AuditAction,
        success: bool,
        details: Dict[str, Any] = None
    ):
        """记录访问审计日志"""
        log_id = hashlib.md5(
            f"{user_id}_{path}_{action.value}_{datetime.now().isoformat()}".encode()
        ).hexdigest()

        audit_log = AuditLog(
            log_id=log_id,
            user_id=user_id,
            user_role=user_role,
            path=path,
            action=action,
            timestamp=datetime.now(),
            success=success,
            details=details or {}
        )

        self.audit_logs.append(audit_log)

        # 控制日志数量在合理范围
        if len(self.audit_logs) > 10000:
            self.audit_logs = self.audit_logs[-5000:]

    def get_audit_logs(self, user_id: str = None, path: str = None, action: AuditAction = None,
                       start_time: datetime = None, end_time: datetime = None, limit: int = None) -> List[AuditLog]:
        """获取审计日志"""
        filtered_logs = self.audit_logs

        if user_id:
            filtered_logs = [log for log in filtered_logs if log.user_id == user_id]

        if path:
            normalized_path = os.path.normpath(path)
            filtered_logs = [log for log in filtered_logs if os.path.normpath(log.path).startswith(normalized_path)]

        if action:
            filtered_logs = [log for log in filtered_logs if log.action == action]

        if start_time:
            filtered_logs = [log for log in filtered_logs if log.timestamp >= start_time]

        if end_time:
            filtered_logs = [log for log in filtered_logs if log.timestamp <= end_time]

        # 按时间倒序排序
        sorted_logs = sorted(filtered_logs, key=lambda x: x.timestamp, reverse=True)

        # 应用 limit 限制
        if limit is not None and limit > 0:
            return sorted_logs[:limit]

        return sorted_logs

    def add_directory_rule(self, rule: DirectoryRule):
        """新增目录规则"""
        self.directory_rules[rule.path] = rule
        self._save_config()

    def remove_directory_rule(self, path: str) -> bool:
        """删除目录规则"""
        if path in self.directory_rules:
            del self.directory_rules[path]
            self._save_config()
            return True
        return False

    def get_directory_rules(self) -> Dict[str, DirectoryRule]:
        """获取全部目录规则"""
        return self.directory_rules.copy()

    def get_user_accessible_paths(self, user_role: str) -> List[Tuple[str, AccessLevel]]:
        """获取用户可访问的目录及其访问等级"""
        accessible_paths = []

        for path, rule in self.directory_rules.items():
            if "*" in rule.allowed_roles or user_role in rule.allowed_roles:
                access_level = rule.access_levels.get(user_role) or rule.access_levels.get("*", AccessLevel.NONE)
                if access_level != AccessLevel.NONE:
                    accessible_paths.append((path, access_level))

        return accessible_paths

    def generate_access_report(self) -> Dict[str, Any]:
        """生成访问与审计报告汇总"""
        report = {
            "总目录规则数": len(self.directory_rules),
            "待审批请求数": len([r for r in self.access_requests.values() if r.approved is None]),
            "已批准请求数": len([r for r in self.access_requests.values() if r.approved is True]),
            "已拒绝请求数": len([r for r in self.access_requests.values() if r.approved is False]),
            "审计日志数": len(self.audit_logs),
            "最近24小时访问次数": len([log for log in self.audit_logs if log.timestamp > datetime.now() - timedelta(days=1)]),
            "按类别统计": {},
            "按角色统计": {}
        }

        # 按类别统计
        for rule in self.directory_rules.values():
            category = rule.category.value
            if category not in report["按类别统计"]:
                report["按类别统计"][category] = 0
            report["按类别统计"][category] += 1

        # 按角色统计（基于审计日志）
        for log in self.audit_logs:
            role = log.user_role
            if role not in report["按角色统计"]:
                report["按角色统计"][role] = 0
            report["按角色统计"][role] += 1

        return report


# 全局实例
document_governance = DocumentGovernanceManager()