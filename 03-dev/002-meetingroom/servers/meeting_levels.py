#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YDS AI公司会议分级管理系统
实现A级/B级/C级会议的自动化管理和权限控制
"""

import json
import time
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta

from agent_roles import AgentRole, MeetingLevel, role_manager
from mcp_message_model import MCPMessage, ChannelType, EventType


class MeetingStatus(Enum):
    """会议状态"""
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"
    CANCELLED = "cancelled"


class VoteType(Enum):
    """投票类型"""
    SIMPLE_MAJORITY = "simple_majority"  # 简单多数
    QUALIFIED_MAJORITY = "qualified_majority"  # 特定多数（2/3）
    UNANIMOUS = "unanimous"  # 全票通过
    ADVISORY = "advisory"  # 咨询性投票


@dataclass
class MeetingRule:
    """会议规则配置"""
    level: MeetingLevel
    min_participants: int
    max_participants: int
    max_duration_minutes: int
    required_roles: List[AgentRole]
    optional_roles: List[AgentRole]
    auto_record: bool
    requires_agenda: bool
    vote_threshold: float  # 法定人数比例
    default_vote_type: VoteType
    can_create_submeeting: bool
    escalation_rules: Dict[str, Any]


@dataclass
class MeetingAgenda:
    """会议议程"""
    id: str
    title: str
    description: str
    estimated_minutes: int
    presenter: Optional[str] = None
    required_participants: List[str] = None
    attachments: List[str] = None
    vote_required: bool = False
    vote_type: Optional[VoteType] = None


@dataclass
class MeetingSession:
    """会议会话"""
    id: str
    level: MeetingLevel
    title: str
    description: str
    host_agent: str
    participants: List[str]
    agenda_items: List[MeetingAgenda]
    status: MeetingStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_minutes: int = 0
    meeting_notes: List[str] = None
    decisions: List[Dict[str, Any]] = None
    action_items: List[Dict[str, Any]] = None
    votes: List[Dict[str, Any]] = None
    escalated_to: Optional[str] = None
    parent_meeting: Optional[str] = None
    child_meetings: List[str] = None
    
    def get(self, key: str, default=None):
        """支持字典式访问"""
        return getattr(self, key, default)


class MeetingLevelManager:
    """会议分级管理器"""
    
    def __init__(self):
        self.rules: Dict[MeetingLevel, MeetingRule] = {}
        self.active_meetings: Dict[str, MeetingSession] = {}
        self.meeting_history: List[MeetingSession] = []
        self._initialize_meeting_rules()
    
    def _initialize_meeting_rules(self):
        """初始化会议规则"""
        
        # A级会议规则 - 战略决策
        a_level_rule = MeetingRule(
            level=MeetingLevel.A_LEVEL,
            min_participants=3,
            max_participants=8,
            max_duration_minutes=120,
            required_roles=[AgentRole.CEO],  # CEO必须参与
            optional_roles=[
                AgentRole.CFO, AgentRole.CTO, 
                AgentRole.PROJECT_COORDINATOR,
                AgentRole.MEETING_SECRETARY
            ],
            auto_record=True,
            requires_agenda=True,
            vote_threshold=0.75,  # 75%法定人数
            default_vote_type=VoteType.QUALIFIED_MAJORITY,
            can_create_submeeting=True,
            escalation_rules={
                "no_consensus_timeout": 30,  # 30分钟无共识自动升级
                "critical_decision": True,   # 关键决策标记
                "board_notification": True   # 通知董事会
            }
        )
        
        # B级会议规则 - 业务协调
        b_level_rule = MeetingRule(
            level=MeetingLevel.B_LEVEL,
            min_participants=2,
            max_participants=12,
            max_duration_minutes=90,
            required_roles=[AgentRole.PROJECT_COORDINATOR],  # 项目协调者必须参与
            optional_roles=[
                AgentRole.CEO, AgentRole.CFO,
                AgentRole.FRONTEND_DEVELOPER, AgentRole.BACKEND_DEVELOPER,
                AgentRole.QA_ENGINEER, AgentRole.UI_UX_DESIGNER,
                AgentRole.MEETING_SECRETARY
            ],
            auto_record=True,
            requires_agenda=True,
            vote_threshold=0.6,  # 60%法定人数
            default_vote_type=VoteType.SIMPLE_MAJORITY,
            can_create_submeeting=True,
            escalation_rules={
                "no_consensus_timeout": 45,  # 45分钟无共识升级到A级
                "resource_conflict": True,   # 资源冲突自动升级
                "cross_department": True     # 跨部门问题升级
            }
        )
        
        # C级会议规则 - 日常沟通
        c_level_rule = MeetingRule(
            level=MeetingLevel.C_LEVEL,
            min_participants=2,
            max_participants=15,
            max_duration_minutes=60,
            required_roles=[],  # 无强制角色要求
            optional_roles=[role for role in AgentRole if role != AgentRole.SYSTEM],
            auto_record=False,
            requires_agenda=False,
            vote_threshold=0.5,  # 50%法定人数
            default_vote_type=VoteType.SIMPLE_MAJORITY,
            can_create_submeeting=False,
            escalation_rules={
                "no_consensus_timeout": 60,  # 60分钟无共识升级到B级
                "technical_complexity": True,  # 技术复杂度升级
                "budget_impact": 10000       # 预算影响超过1万升级
            }
        )
        
        self.rules = {
            MeetingLevel.A_LEVEL: a_level_rule,
            MeetingLevel.B_LEVEL: b_level_rule,
            MeetingLevel.C_LEVEL: c_level_rule
        }
    
    def create_meeting(
        self, 
        level: MeetingLevel,
        title: str,
        description: str,
        host_agent: str,
        participants: List[str],
        organizer: Optional[str] = None,
        agenda_items: Optional[List[MeetingAgenda]] = None
    ) -> Optional[MeetingSession]:
        """创建会议"""
        
        rule = self.rules.get(level)
        if not rule:
            return None
        
        # 验证参与者数量
        if len(participants) < rule.min_participants:
            raise ValueError(f"{level.value}级会议至少需要{rule.min_participants}个参与者")
        
        if len(participants) > rule.max_participants:
            raise ValueError(f"{level.value}级会议最多允许{rule.max_participants}个参与者")
        
        # 验证必需角色
        participant_roles = self._get_participant_roles(participants)
        for required_role in rule.required_roles:
            if required_role not in participant_roles:
                role_config = role_manager.get_role_config(required_role)
                role_name = role_config.display_name if role_config else required_role.value
                raise ValueError(f"{level.value}级会议必须包含{role_name}")
        
        # 验证主持人权限
        host_role = self._get_agent_role(host_agent)
        if host_role and not role_manager.can_host_meeting(host_role, level):
            raise ValueError(f"智能体{host_agent}无权主持{level.value}级会议")
        
        # 创建会议会话
        meeting_id = f"meeting.{level.value.lower()}.{int(time.time())}"
        meeting = MeetingSession(
            id=meeting_id,
            level=level,
            title=title,
            description=description,
            host_agent=host_agent,
            participants=participants,
            agenda_items=agenda_items or [],
            status=MeetingStatus.SCHEDULED,
            created_at=datetime.now(),
            meeting_notes=[],
            decisions=[],
            action_items=[],
            votes=[],
            child_meetings=[]
        )
        
        self.active_meetings[meeting_id] = meeting
        return meeting
    
    def start_meeting(self, meeting_id: str) -> bool:
        """开始会议"""
        meeting = self.active_meetings.get(meeting_id)
        if not meeting or meeting.status != MeetingStatus.SCHEDULED:
            return False
        
        meeting.status = MeetingStatus.ACTIVE
        meeting.started_at = datetime.now()
        
        # 发送会议开始通知
        self._broadcast_meeting_event(meeting, EventType.MEETING_START)
        return True
    
    def end_meeting(self, meeting_id: str, summary: Optional[str] = None) -> bool:
        """结束会议"""
        meeting = self.active_meetings.get(meeting_id)
        if not meeting or meeting.status != MeetingStatus.ACTIVE:
            return False
        
        meeting.status = MeetingStatus.ENDED
        meeting.ended_at = datetime.now()
        
        if meeting.started_at:
            duration = meeting.ended_at - meeting.started_at
            meeting.duration_minutes = int(duration.total_seconds() / 60)
        
        # 添加会议总结
        if summary:
            meeting.meeting_notes.append(f"会议总结: {summary}")
        
        # 移动到历史记录
        self.meeting_history.append(meeting)
        del self.active_meetings[meeting_id]
        
        # 发送会议结束通知
        self._broadcast_meeting_event(meeting, EventType.MEETING_ENDED)
        return True
    
    def add_agenda_item(self, meeting_id: str, agenda: MeetingAgenda) -> bool:
        """添加议程项"""
        meeting = self.active_meetings.get(meeting_id)
        if not meeting:
            return False
        
        meeting.agenda_items.append(agenda)
        return True
    
    def create_vote(
        self,
        meeting_id: str,
        title: str,
        description: str,
        options: List[str],
        vote_type: Optional[VoteType] = None,
        anonymous: bool = False,
        duration_minutes: int = 10
    ) -> Optional[str]:
        """创建投票"""
        meeting = self.active_meetings.get(meeting_id)
        if not meeting or meeting.status != MeetingStatus.ACTIVE:
            return None
        
        rule = self.rules.get(meeting.level)
        if not vote_type:
            vote_type = rule.default_vote_type
        
        vote_id = f"vote.{meeting_id}.{int(time.time())}"
        vote_data = {
            "id": vote_id,
            "meeting_id": meeting_id,
            "title": title,
            "description": description,
            "options": options,
            "vote_type": vote_type.value,
            "anonymous": anonymous,
            "duration_minutes": duration_minutes,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(minutes=duration_minutes)).isoformat(),
            "votes": {},
            "status": "active"
        }
        
        meeting.votes.append(vote_data)
        
        # 发送投票创建通知
        self._broadcast_vote_event(meeting, vote_data, EventType.VOTE_CREATED)
        return vote_id
    
    def cast_vote(self, meeting_id: str, vote_id: str, agent_id: str, choice: str) -> bool:
        """投票"""
        meeting = self.active_meetings.get(meeting_id)
        if not meeting or agent_id not in meeting.participants:
            return False
        
        # 查找投票
        vote_data = None
        for vote in meeting.votes:
            if vote["id"] == vote_id:
                vote_data = vote
                break
        
        if not vote_data or vote_data["status"] != "active":
            return False
        
        # 检查投票是否过期
        expires_at = datetime.fromisoformat(vote_data["expires_at"])
        if datetime.now() > expires_at:
            vote_data["status"] = "expired"
            return False
        
        # 记录投票
        vote_data["votes"][agent_id] = choice
        
        # 检查是否达到法定人数
        rule = self.rules.get(meeting.level)
        required_votes = int(len(meeting.participants) * rule.vote_threshold)
        
        if len(vote_data["votes"]) >= required_votes:
            # 计算结果
            self._calculate_vote_result(vote_data)
            vote_data["status"] = "completed"
            
            # 发送投票完成通知
            self._broadcast_vote_event(meeting, vote_data, EventType.VOTE_COMPLETED)
        
        return True
    
    def escalate_meeting(self, meeting_id: str, reason: str) -> Optional[str]:
        """升级会议"""
        meeting = self.active_meetings.get(meeting_id)
        if not meeting:
            return None
        
        # 确定升级目标级别
        target_level = None
        if meeting.level == MeetingLevel.C_LEVEL:
            target_level = MeetingLevel.B_LEVEL
        elif meeting.level == MeetingLevel.B_LEVEL:
            target_level = MeetingLevel.A_LEVEL
        else:
            return None  # A级会议无法再升级
        
        # 创建升级后的会议
        escalated_meeting = self.create_meeting(
            level=target_level,
            title=f"[升级] {meeting.title}",
            description=f"从{meeting.level.value}级会议升级: {reason}\n\n原会议描述: {meeting.description}",
            host_agent=meeting.host_agent,
            participants=meeting.participants
        )
        
        if escalated_meeting:
            # 建立父子关系
            meeting.escalated_to = escalated_meeting.id
            escalated_meeting.parent_meeting = meeting.id
            
            # 暂停原会议
            meeting.status = MeetingStatus.PAUSED
            
            # 发送升级通知
            self._broadcast_meeting_event(meeting, EventType.MEETING_ESCALATED)
            
            return escalated_meeting.id
        
        return None
    
    def get_meeting_stats(self) -> Dict[str, Any]:
        """获取会议统计信息"""
        stats = {
            "active_meetings": len(self.active_meetings),
            "total_meetings": len(self.meeting_history) + len(self.active_meetings),
            "meetings_by_level": {
                "A": 0, "B": 0, "C": 0
            },
            "average_duration": 0,
            "escalation_rate": 0
        }
        
        all_meetings = list(self.active_meetings.values()) + self.meeting_history
        
        if all_meetings:
            total_duration = 0
            escalated_count = 0
            
            for meeting in all_meetings:
                stats["meetings_by_level"][meeting.level.value] += 1
                if meeting.duration_minutes > 0:
                    total_duration += meeting.duration_minutes
                if meeting.escalated_to:
                    escalated_count += 1
            
            stats["average_duration"] = total_duration / len(all_meetings)
            stats["escalation_rate"] = escalated_count / len(all_meetings)
        
        return stats
    
    def _get_participant_roles(self, participants: List[str]) -> Set[AgentRole]:
        """获取参与者角色集合"""
        roles = set()
        for participant in participants:
            role = self._get_agent_role(participant)
            if role:
                roles.add(role)
        return roles
    
    def _get_agent_role(self, agent_id: str) -> Optional[AgentRole]:
        """根据智能体ID获取角色"""
        # 简单的角色推断逻辑，实际应该从智能体管理系统获取
        if "ceo" in agent_id.lower():
            return AgentRole.CEO
        elif "cfo" in agent_id.lower():
            return AgentRole.CFO
        elif "coordinator" in agent_id.lower():
            return AgentRole.PROJECT_COORDINATOR
        elif "frontend" in agent_id.lower():
            return AgentRole.FRONTEND_DEVELOPER
        elif "secretary" in agent_id.lower():
            return AgentRole.MEETING_SECRETARY
        return None
    
    def _calculate_vote_result(self, vote_data: Dict[str, Any]):
        """计算投票结果"""
        votes = vote_data["votes"]
        options = vote_data["options"]
        vote_type = VoteType(vote_data["vote_type"])
        
        # 统计各选项票数
        vote_counts = {option: 0 for option in options}
        for choice in votes.values():
            if choice in vote_counts:
                vote_counts[choice] += 1
        
        total_votes = len(votes)
        
        # 根据投票类型确定结果
        result = {"counts": vote_counts, "total_votes": total_votes, "passed": False, "winner": None}
        
        if vote_type == VoteType.SIMPLE_MAJORITY:
            # 简单多数
            max_votes = max(vote_counts.values())
            if max_votes > total_votes / 2:
                result["passed"] = True
                result["winner"] = [k for k, v in vote_counts.items() if v == max_votes][0]
        
        elif vote_type == VoteType.QUALIFIED_MAJORITY:
            # 特定多数（2/3）
            max_votes = max(vote_counts.values())
            if max_votes >= total_votes * 2 / 3:
                result["passed"] = True
                result["winner"] = [k for k, v in vote_counts.items() if v == max_votes][0]
        
        elif vote_type == VoteType.UNANIMOUS:
            # 全票通过
            if len(set(votes.values())) == 1:
                result["passed"] = True
                result["winner"] = list(votes.values())[0]
        
        elif vote_type == VoteType.ADVISORY:
            # 咨询性投票，仅统计不判断通过
            max_votes = max(vote_counts.values())
            result["winner"] = [k for k, v in vote_counts.items() if v == max_votes][0]
        
        vote_data["result"] = result
    
    def _broadcast_meeting_event(self, meeting: MeetingSession, event_type: EventType):
        """广播会议事件"""
        # TODO: 实现事件广播逻辑
        pass
    
    def _broadcast_vote_event(self, meeting: MeetingSession, vote_data: Dict[str, Any], event_type: EventType):
        """广播投票事件"""
        # TODO: 实现投票事件广播逻辑
        pass


# 全局会议管理器实例
meeting_manager = MeetingLevelManager()


if __name__ == "__main__":
    # 测试示例
    manager = MeetingLevelManager()
    
    # 创建A级会议
    participants = ["agent.ceo", "agent.cfo", "agent.coordinator", "agent.secretary"]
    meeting = manager.create_meeting(
        level=MeetingLevel.A_LEVEL,
        title="Q4战略规划会议",
        description="讨论第四季度战略规划和预算分配",
        host_agent="agent.ceo",
        participants=participants
    )
    
    if meeting:
        print(f"创建会议成功: {meeting.id}")
        
        # 开始会议
        manager.start_meeting(meeting.id)
        print("会议已开始")
        
        # 创建投票
        vote_id = manager.create_vote(
            meeting_id=meeting.id,
            title="是否批准新产品开发预算",
            description="为新产品开发分配500万预算",
            options=["同意", "反对", "需要更多信息"],
            vote_type=VoteType.QUALIFIED_MAJORITY,
            duration_minutes=5
        )
        
        if vote_id:
            print(f"创建投票成功: {vote_id}")
            
            # 模拟投票
            manager.cast_vote(meeting.id, vote_id, "agent.ceo", "同意")
            manager.cast_vote(meeting.id, vote_id, "agent.cfo", "需要更多信息")
            manager.cast_vote(meeting.id, vote_id, "agent.coordinator", "同意")
        
        # 获取统计信息
        stats = manager.get_meeting_stats()
        print("会议统计:", stats)