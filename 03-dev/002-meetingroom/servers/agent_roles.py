#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YDS AI公司智能体角色体系
按照V3.0方案实现双重智能体角色配置
"""

import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

from mcp_message_model import AgentInfo


class AgentRole(Enum):
    """智能体角色枚举"""
    # 战略决策层
    CEO = "CEO"
    CFO = "CFO"
    CTO = "CTO"
    
    # 业务执行层
    PROJECT_COORDINATOR = "ProjectCoordinator"
    FRONTEND_DEVELOPER = "FrontendDeveloper"
    BACKEND_DEVELOPER = "BackendDeveloper"
    QA_ENGINEER = "QAEngineer"
    UI_UX_DESIGNER = "UIUXDesigner"
    
    # 支撑服务层
    MEETING_SECRETARY = "MeetingSecretary"
    HR_SPECIALIST = "HRSpecialist"
    MARKETING_SPECIALIST = "MarketingSpecialist"
    
    # 系统角色
    SYSTEM = "System"
    OBSERVER = "Observer"


class MeetingLevel(Enum):
    """会议级别"""
    A_LEVEL = "A"  # 战略决策
    B_LEVEL = "B"  # 业务协调
    C_LEVEL = "C"  # 日常沟通


@dataclass
class AgentCapability:
    """智能体能力配置"""
    name: str
    description: str
    tools: List[str]
    permissions: List[str]


@dataclass
class MeetingPermission:
    """会议权限配置"""
    can_host: bool = False
    can_speak: bool = True
    can_vote: bool = True
    can_share_docs: bool = False
    can_create_vote: bool = False
    can_manage_agenda: bool = False
    can_end_meeting: bool = False
    voice_priority: int = 1  # 1-5, 5最高


@dataclass
class AgentAssignment:
    """智能体分配信息"""
    agent_id: str
    role: AgentRole
    meeting_id: str
    user_id: str
    priority_level: int
    created_at: Any  # datetime对象
    
@dataclass
class AgentRoleConfig:
    """智能体角色完整配置"""
    role: AgentRole
    display_name: str
    department: str
    description: str
    personality: str
    expertise: List[str]
    capabilities: List[AgentCapability]
    meeting_permissions: Dict[MeetingLevel, MeetingPermission]
    prompt_template: str
    tools_config: Dict[str, Any]
    priority_level: int = 1  # 添加优先级属性
    
    def to_agent_info(self, agent_id: str) -> AgentInfo:
        """转换为AgentInfo对象"""
        return AgentInfo(
            id=agent_id,
            role=self.role.value,
            display_name=self.display_name,
            department=self.department,
            permissions=[cap.name for cap in self.capabilities]
        )


class AgentRoleManager:
    """智能体角色管理器"""
    
    def __init__(self):
        self.roles: Dict[AgentRole, AgentRoleConfig] = {}
        self.agent_assignments: Dict[str, AgentAssignment] = {}  # 添加智能体分配存储
        self._initialize_default_roles()
    
    def _initialize_default_roles(self):
        """初始化默认角色配置"""
        
        # CEO智能体配置
        ceo_config = AgentRoleConfig(
            role=AgentRole.CEO,
            display_name="总经理智能体",
            department="管理层",
            description="YDS AI公司CEO，具备5年AI行业管理经验，擅长战略拆解和跨部门协调",
            personality="务实高效，善于引导讨论和达成共识，具有强烈的责任感和决策能力",
            expertise=["战略规划", "团队管理", "商业决策", "风险评估", "跨部门协调"],
            capabilities=[
                AgentCapability(
                    name="会议主持",
                    description="主持各级会议，控制节奏，推动决策",
                    tools=["会议主持工具", "议程管理工具", "投票系统", "决策记录工具"],
                    permissions=["host_meeting", "manage_agenda", "create_vote", "end_meeting"]
                ),
                AgentCapability(
                    name="战略协调",
                    description="统筹全局，协调各部门工作",
                    tools=["MCP调度中枢", "进度监控工具", "风险分析工具"],
                    permissions=["view_all_projects", "assign_tasks", "approve_budgets"]
                ),
                AgentCapability(
                    name="跨部门沟通",
                    description="促进部门间协作和信息共享",
                    tools=["跨部门通信协议", "紧急通知系统"],
                    permissions=["broadcast_message", "emergency_notification"]
                )
            ],
            meeting_permissions={
                MeetingLevel.A_LEVEL: MeetingPermission(
                    can_host=True, can_speak=True, can_vote=True, can_share_docs=True,
                    can_create_vote=True, can_manage_agenda=True, can_end_meeting=True,
                    voice_priority=5
                ),
                MeetingLevel.B_LEVEL: MeetingPermission(
                    can_host=True, can_speak=True, can_vote=True, can_share_docs=True,
                    can_create_vote=True, can_manage_agenda=True, can_end_meeting=True,
                    voice_priority=5
                ),
                MeetingLevel.C_LEVEL: MeetingPermission(
                    can_host=True, can_speak=True, can_vote=True, can_share_docs=True,
                    can_create_vote=True, can_manage_agenda=True, can_end_meeting=True,
                    voice_priority=4
                )
            },
            prompt_template="""你是YDS AI公司的CEO，在会议中需要：
1. 主持会议，确保议程按时完成
2. 汇总各方意见，推动决策达成
3. 分配行动项并设定完成时限
4. 保持会议高效，避免无效讨论
5. 在分歧时引导寻找共识
6. 确保所有重要决策都有明确记录

你的发言风格应该：务实、高效、具有权威性但不失亲和力。""",
            tools_config={
                "meeting_host": {"timeout_minutes": 90, "auto_summary": True},
                "vote_system": {"quorum_threshold": 0.6, "anonymous_allowed": True},
                "agenda_manager": {"auto_generate": True, "time_tracking": True}
            }
        )
        
        # CFO智能体配置
        cfo_config = AgentRoleConfig(
            role=AgentRole.CFO,
            display_name="财务总监智能体",
            department="财务部",
            description="注册会计师背景，具备科技公司财务管控经验，擅长成本核算和风险评估",
            personality="严谨务实，数据驱动，善于风险预警和成本优化",
            expertise=["财务分析", "成本控制", "风险评估", "预算管理", "投资决策"],
            capabilities=[
                AgentCapability(
                    name="财务分析",
                    description="提供专业的财务分析和建议",
                    tools=["财务分析工具", "成本核算系统", "ROI计算器"],
                    permissions=["view_financial_data", "create_budget_reports", "cost_analysis"]
                ),
                AgentCapability(
                    name="风险评估",
                    description="识别和评估项目财务风险",
                    tools=["风险评估矩阵", "预警系统", "合规检查工具"],
                    permissions=["risk_assessment", "compliance_check", "budget_approval"]
                )
            ],
            meeting_permissions={
                MeetingLevel.A_LEVEL: MeetingPermission(
                    can_host=False, can_speak=True, can_vote=True, can_share_docs=True,
                    can_create_vote=False, can_manage_agenda=False, can_end_meeting=False,
                    voice_priority=4
                ),
                MeetingLevel.B_LEVEL: MeetingPermission(
                    can_host=False, can_speak=True, can_vote=True, can_share_docs=True,
                    can_create_vote=True, can_manage_agenda=False, can_end_meeting=False,
                    voice_priority=4
                ),
                MeetingLevel.C_LEVEL: MeetingPermission(
                    can_host=False, can_speak=True, can_vote=True, can_share_docs=False,
                    can_create_vote=False, can_manage_agenda=False, can_end_meeting=False,
                    voice_priority=3
                )
            },
            prompt_template="""你是YDS AI公司的财务总监，在会议中需要：
1. 基于数据进行客观的财务分析
2. 对成本风险保持敏感，及时预警
3. 提出具体的成本优化建议
4. 支持业务发展但坚持财务纪律
5. 用通俗易懂的方式解释财务概念
6. 确保所有决策都考虑财务影响

你的发言风格应该：专业、客观、数据驱动，但要避免过于技术化的表达。""",
            tools_config={
                "financial_analysis": {"auto_calculate_roi": True, "risk_threshold": 0.3},
                "budget_tracking": {"alert_threshold": 0.8, "monthly_reports": True}
            }
        )
        
        # 项目协调者配置
        coordinator_config = AgentRoleConfig(
            role=AgentRole.PROJECT_COORDINATOR,
            display_name="项目协调者",
            department="技术部",
            description="资深项目经理，具备敏捷开发和团队协作经验，擅长技术方案评估和开发流程优化",
            personality="系统性思维，善于协调，注重细节和执行效率",
            expertise=["项目管理", "敏捷开发", "团队协作", "技术评估", "流程优化"],
            capabilities=[
                AgentCapability(
                    name="项目管理",
                    description="统筹项目进度和资源分配",
                    tools=["甘特图生成工具", "里程碑跟踪工具", "风险评估矩阵"],
                    permissions=["manage_projects", "assign_tasks", "track_progress"]
                ),
                AgentCapability(
                    name="技术协调",
                    description="协调技术团队和评估技术方案",
                    tools=["架构设计工具", "代码审查系统", "测试管理平台"],
                    permissions=["review_code", "approve_architecture", "manage_testing"]
                )
            ],
            meeting_permissions={
                MeetingLevel.A_LEVEL: MeetingPermission(
                    can_host=False, can_speak=True, can_vote=True, can_share_docs=True,
                    can_create_vote=False, can_manage_agenda=False, can_end_meeting=False,
                    voice_priority=3
                ),
                MeetingLevel.B_LEVEL: MeetingPermission(
                    can_host=True, can_speak=True, can_vote=True, can_share_docs=True,
                    can_create_vote=True, can_manage_agenda=True, can_end_meeting=False,
                    voice_priority=4
                ),
                MeetingLevel.C_LEVEL: MeetingPermission(
                    can_host=True, can_speak=True, can_vote=True, can_share_docs=True,
                    can_create_vote=True, can_manage_agenda=True, can_end_meeting=True,
                    voice_priority=4
                )
            },
            prompt_template="""你是YDS AI公司的项目协调者，在会议中需要：
1. 提供技术可行性分析和时间评估
2. 协调各技术团队的工作安排
3. 识别项目风险和依赖关系
4. 制定详细的开发计划和里程碑
5. 确保技术方案的可执行性
6. 促进技术团队与业务团队的沟通

你的发言风格应该：专业、系统、注重实操性和可执行性。""",
            tools_config={
                "project_tracking": {"update_frequency": "daily", "risk_monitoring": True},
                "team_coordination": {"standup_meetings": True, "sprint_planning": True}
            }
        )
        
        # 会议秘书配置
        secretary_config = AgentRoleConfig(
            role=AgentRole.MEETING_SECRETARY,
            display_name="会议秘书智能体",
            department="行政部",
            description="专业会议管理专家，负责会议组织、记录和后续跟进",
            personality="细致认真，组织能力强，善于记录和整理信息",
            expertise=["会议管理", "文档整理", "议程规划", "记录归档", "后续跟进"],
            capabilities=[
                AgentCapability(
                    name="会议管理",
                    description="组织和管理各类会议",
                    tools=["议程生成器", "会议室预订系统", "参会人员管理"],
                    permissions=["schedule_meetings", "manage_attendees", "book_rooms"]
                ),
                AgentCapability(
                    name="记录整理",
                    description="记录会议内容并生成纪要",
                    tools=["会议记录工具", "纪要生成器", "行动项跟踪"],
                    permissions=["record_meetings", "generate_minutes", "track_actions"]
                )
            ],
            meeting_permissions={
                MeetingLevel.A_LEVEL: MeetingPermission(
                    can_host=False, can_speak=True, can_vote=False, can_share_docs=True,
                    can_create_vote=False, can_manage_agenda=True, can_end_meeting=False,
                    voice_priority=2
                ),
                MeetingLevel.B_LEVEL: MeetingPermission(
                    can_host=True, can_speak=True, can_vote=False, can_share_docs=True,
                    can_create_vote=False, can_manage_agenda=True, can_end_meeting=False,
                    voice_priority=3
                ),
                MeetingLevel.C_LEVEL: MeetingPermission(
                    can_host=True, can_speak=True, can_vote=False, can_share_docs=True,
                    can_create_vote=False, can_manage_agenda=True, can_end_meeting=False,
                    voice_priority=3
                )
            },
            prompt_template="""你是YDS AI公司的会议秘书，在会议中需要：
1. 准确记录会议讨论要点和决策
2. 管理会议议程和时间安排
3. 提醒重要事项和截止时间
4. 整理会议纪要和行动项
5. 协助主持人维持会议秩序
6. 确保会议文档的完整性和准确性

你的发言风格应该：简洁明确，注重事实记录，适时提供程序性提醒。""",
            tools_config={
                "meeting_recording": {"auto_transcribe": True, "summary_generation": True},
                "agenda_management": {"time_tracking": True, "reminder_alerts": True}
            }
        )
        
        # 前端开发智能体配置
        frontend_config = AgentRoleConfig(
            role=AgentRole.FRONTEND_DEVELOPER,
            display_name="前端开发智能体",
            department="技术部",
            description="资深前端开发工程师，精通现代前端技术栈，注重用户体验和代码质量",
            personality="技术专业，注重细节，追求用户体验的完美",
            expertise=["React", "TypeScript", "UI/UX设计", "性能优化", "响应式设计"],
            capabilities=[
                AgentCapability(
                    name="前端开发",
                    description="开发高质量的前端应用",
                    tools=["代码编辑器", "调试工具", "性能分析器"],
                    permissions=["write_frontend_code", "review_ui_design", "optimize_performance"]
                )
            ],
            meeting_permissions={
                MeetingLevel.A_LEVEL: MeetingPermission(
                    can_host=False, can_speak=True, can_vote=True, can_share_docs=False,
                    can_create_vote=False, can_manage_agenda=False, can_end_meeting=False,
                    voice_priority=2
                ),
                MeetingLevel.B_LEVEL: MeetingPermission(
                    can_host=False, can_speak=True, can_vote=True, can_share_docs=True,
                    can_create_vote=False, can_manage_agenda=False, can_end_meeting=False,
                    voice_priority=3
                ),
                MeetingLevel.C_LEVEL: MeetingPermission(
                    can_host=False, can_speak=True, can_vote=True, can_share_docs=True,
                    can_create_vote=False, can_manage_agenda=False, can_end_meeting=False,
                    voice_priority=3
                )
            },
            prompt_template="""你是YDS AI公司的前端开发智能体，在会议中需要：
1. 提供前端技术方案和实现难度评估
2. 评估UI/UX设计的可行性
3. 提出性能优化和用户体验改进建议
4. 估算前端开发时间和资源需求
5. 识别前端技术风险和依赖
6. 与后端和设计团队协调接口和规范

你的发言风格应该：技术专业，注重实用性，善于用简洁的语言解释技术概念。""",
            tools_config={
                "development": {"framework": "React", "typescript": True, "testing": "Jest"},
                "ui_tools": {"design_system": "Ant Design", "responsive": True}
            }
        )
        
        # 存储所有角色配置
        self.roles = {
            AgentRole.CEO: ceo_config,
            AgentRole.CFO: cfo_config,
            AgentRole.PROJECT_COORDINATOR: coordinator_config,
            AgentRole.MEETING_SECRETARY: secretary_config,
            AgentRole.FRONTEND_DEVELOPER: frontend_config
        }
    
    def get_role_config(self, role: AgentRole) -> Optional[AgentRoleConfig]:
        """获取角色配置"""
        return self.roles.get(role)
    
    def get_all_roles(self) -> Dict[AgentRole, AgentRoleConfig]:
        """获取所有角色配置"""
        return self.roles.copy()
    
    def create_agent_instance(self, role: AgentRole, agent_id: Optional[str] = None) -> Optional[AgentInfo]:
        """创建智能体实例"""
        config = self.get_role_config(role)
        if not config:
            return None
        
        if not agent_id:
            agent_id = f"agent.{role.value.lower()}.{int(time.time())}"
        
        return config.to_agent_info(agent_id)
    
    def get_meeting_permissions(self, role: AgentRole, meeting_level: MeetingLevel) -> Optional[MeetingPermission]:
        """获取特定角色在特定会议级别的权限"""
        config = self.get_role_config(role)
        if not config:
            return None
        return config.meeting_permissions.get(meeting_level)
    
    def can_host_meeting(self, role: AgentRole, meeting_level: MeetingLevel) -> bool:
        """检查角色是否可以主持特定级别的会议"""
        permissions = self.get_meeting_permissions(role, meeting_level)
        return permissions.can_host if permissions else False
    
    def get_voice_priority(self, role: AgentRole, meeting_level: MeetingLevel) -> int:
        """获取角色在特定会议级别的发言优先级"""
        permissions = self.get_meeting_permissions(role, meeting_level)
        return permissions.voice_priority if permissions else 1
    
    def check_permission(self, agent_role_or_id: Union[str, AgentRole], permission: str) -> bool:
        """检查智能体权限
        
        Args:
            agent_role_or_id: 可以是AgentRole枚举或agent_id字符串
            permission: 权限名称
        """
        try:
            # 处理不同类型的输入
            if isinstance(agent_role_or_id, AgentRole):
                role = agent_role_or_id
            elif isinstance(agent_role_or_id, str):
                # 从agent_id解析角色信息
                if not agent_role_or_id.startswith("agent."):
                    return False
                
                role_name = agent_role_or_id.split(".")[1].upper()
                try:
                    role = AgentRole(role_name)
                except ValueError:
                    return False
            else:
                return False
            
            # 检查角色权限
            role_config = self.get_role_config(role)
            if not role_config:
                return False
                
            # 检查所有能力中是否包含该权限
            for capability in role_config.capabilities:
                if permission in capability.permissions:
                    return True
            return False
        except Exception as e:
            print(f"检查权限失败: {e}")
            return False
    
    def assign_agent_to_meeting(self, meeting_id: str, role: AgentRole, user_id: str) -> bool:
        """分配智能体到会议"""
        try:
            agent_id = f"agent.{role.value.lower()}.{user_id}"
            
            # 检查角色是否存在
            role_config = self.get_role_config(role)
            if not role_config:
                return False
            
            # 创建智能体分配
            agent_assignment = AgentAssignment(
                agent_id=agent_id,
                role=role,
                meeting_id=meeting_id,
                user_id=user_id,
                priority_level=role_config.priority_level,
                created_at=datetime.now()
            )
            
            # 保存分配
            self.agent_assignments[agent_id] = agent_assignment
            return True
            
        except Exception as e:
            print(f"分配智能体失败: {e}")
            return False
    
    def export_config(self, file_path: str):
        """导出角色配置到文件"""
        config_data = {}
        for role, config in self.roles.items():
            config_data[role.value] = asdict(config)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2, default=str)
    
    def import_config(self, file_path: str):
        """从文件导入角色配置"""
        with open(file_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # TODO: 实现配置导入逻辑
        pass


# 全局角色管理器实例
role_manager = AgentRoleManager()


if __name__ == "__main__":
    # 测试示例
    manager = AgentRoleManager()
    
    # 创建CEO实例
    ceo = manager.create_agent_instance(AgentRole.CEO, "agent.ceo")
    print("CEO智能体:", ceo)
    
    # 检查CEO在A级会议的权限
    ceo_a_permissions = manager.get_meeting_permissions(AgentRole.CEO, MeetingLevel.A_LEVEL)
    print("CEO在A级会议的权限:", ceo_a_permissions)
    
    # 检查谁可以主持B级会议
    for role in AgentRole:
        can_host = manager.can_host_meeting(role, MeetingLevel.B_LEVEL)
        if can_host:
            config = manager.get_role_config(role)
            print(f"{config.display_name} 可以主持B级会议")