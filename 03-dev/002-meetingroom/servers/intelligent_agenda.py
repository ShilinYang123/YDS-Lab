#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YDS AI公司智能议程系统
实现自动生成议程、时间管理和议程优化
"""

import json
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import re

from agent_roles import AgentRole, MeetingLevel, role_manager
from meeting_levels import MeetingAgenda, VoteType


class AgendaPriority(Enum):
    """议程优先级"""
    CRITICAL = "critical"      # 关键议题
    HIGH = "high"             # 高优先级
    MEDIUM = "medium"         # 中等优先级
    LOW = "low"              # 低优先级
    INFORMATIONAL = "info"    # 信息通报


class AgendaType(Enum):
    """议程类型"""
    DECISION = "decision"          # 决策议题
    DISCUSSION = "discussion"      # 讨论议题
    PRESENTATION = "presentation"  # 汇报议题
    BRAINSTORM = "brainstorm"     # 头脑风暴
    REVIEW = "review"             # 审查议题
    PLANNING = "planning"         # 规划议题
    UPDATE = "update"             # 进度更新
    VOTE = "vote"                 # 投票议题


@dataclass
class AgendaTemplate:
    """议程模板"""
    id: str
    name: str
    meeting_level: MeetingLevel
    template_items: List[Dict[str, Any]]
    estimated_duration: int
    required_roles: List[AgentRole]
    description: str


@dataclass
class TimeSlot:
    """时间段"""
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    buffer_minutes: int = 5  # 缓冲时间


@dataclass
class AgendaItem:
    """议程项详细信息"""
    id: str
    title: str
    description: str
    agenda_type: AgendaType
    priority: AgendaPriority
    presenter: Optional[str]
    participants: List[str]
    estimated_minutes: int
    actual_minutes: int = 0
    time_slot: Optional[TimeSlot] = None
    prerequisites: List[str] = None  # 前置议程ID
    attachments: List[str] = None
    vote_required: bool = False
    vote_type: Optional[VoteType] = None
    status: str = "pending"  # pending, active, completed, skipped
    notes: List[str] = None
    decisions: List[str] = None
    action_items: List[Dict[str, Any]] = None


class IntelligentAgendaGenerator:
    """智能议程生成器"""
    
    def __init__(self):
        self.templates: Dict[str, AgendaTemplate] = {}
        self.agenda_history: List[Dict[str, Any]] = []
        self._initialize_templates()
    
    def _initialize_templates(self):
        """初始化议程模板"""
        
        # A级会议模板 - 战略决策
        a_level_template = AgendaTemplate(
            id="template.a_level.strategic",
            name="战略决策会议模板",
            meeting_level=MeetingLevel.A_LEVEL,
            estimated_duration=120,
            required_roles=[AgentRole.CEO, AgentRole.CFO],
            description="用于重大战略决策的标准议程模板",
            template_items=[
                {
                    "title": "会议开场与目标确认",
                    "type": AgendaType.PRESENTATION.value,
                    "priority": AgendaPriority.HIGH.value,
                    "estimated_minutes": 10,
                    "presenter": "host"
                },
                {
                    "title": "上期决策执行情况回顾",
                    "type": AgendaType.REVIEW.value,
                    "priority": AgendaPriority.HIGH.value,
                    "estimated_minutes": 15,
                    "presenter": "secretary"
                },
                {
                    "title": "核心议题讨论",
                    "type": AgendaType.DISCUSSION.value,
                    "priority": AgendaPriority.CRITICAL.value,
                    "estimated_minutes": 60,
                    "presenter": "dynamic"
                },
                {
                    "title": "财务影响评估",
                    "type": AgendaType.PRESENTATION.value,
                    "priority": AgendaPriority.HIGH.value,
                    "estimated_minutes": 15,
                    "presenter": "cfo"
                },
                {
                    "title": "决策投票",
                    "type": AgendaType.VOTE.value,
                    "priority": AgendaPriority.CRITICAL.value,
                    "estimated_minutes": 10,
                    "vote_required": True,
                    "vote_type": VoteType.QUALIFIED_MAJORITY.value
                },
                {
                    "title": "行动计划制定",
                    "type": AgendaType.PLANNING.value,
                    "priority": AgendaPriority.HIGH.value,
                    "estimated_minutes": 15,
                    "presenter": "coordinator"
                },
                {
                    "title": "会议总结与下步安排",
                    "type": AgendaType.PRESENTATION.value,
                    "priority": AgendaPriority.MEDIUM.value,
                    "estimated_minutes": 10,
                    "presenter": "host"
                }
            ]
        )
        
        # B级会议模板 - 业务协调
        b_level_template = AgendaTemplate(
            id="template.b_level.coordination",
            name="业务协调会议模板",
            meeting_level=MeetingLevel.B_LEVEL,
            estimated_duration=90,
            required_roles=[AgentRole.PROJECT_COORDINATOR],
            description="用于跨部门业务协调的标准议程模板",
            template_items=[
                {
                    "title": "项目进度同步",
                    "type": AgendaType.UPDATE.value,
                    "priority": AgendaPriority.HIGH.value,
                    "estimated_minutes": 20,
                    "presenter": "coordinator"
                },
                {
                    "title": "资源需求与分配",
                    "type": AgendaType.DISCUSSION.value,
                    "priority": AgendaPriority.HIGH.value,
                    "estimated_minutes": 25,
                    "presenter": "dynamic"
                },
                {
                    "title": "技术方案评审",
                    "type": AgendaType.REVIEW.value,
                    "priority": AgendaPriority.MEDIUM.value,
                    "estimated_minutes": 20,
                    "presenter": "technical_lead"
                },
                {
                    "title": "风险识别与应对",
                    "type": AgendaType.DISCUSSION.value,
                    "priority": AgendaPriority.HIGH.value,
                    "estimated_minutes": 15,
                    "presenter": "coordinator"
                },
                {
                    "title": "下阶段计划确认",
                    "type": AgendaType.PLANNING.value,
                    "priority": AgendaPriority.MEDIUM.value,
                    "estimated_minutes": 10,
                    "presenter": "coordinator"
                }
            ]
        )
        
        # C级会议模板 - 日常沟通
        c_level_template = AgendaTemplate(
            id="template.c_level.daily",
            name="日常沟通会议模板",
            meeting_level=MeetingLevel.C_LEVEL,
            estimated_duration=60,
            required_roles=[],
            description="用于日常团队沟通的灵活议程模板",
            template_items=[
                {
                    "title": "工作进展分享",
                    "type": AgendaType.UPDATE.value,
                    "priority": AgendaPriority.MEDIUM.value,
                    "estimated_minutes": 20,
                    "presenter": "all"
                },
                {
                    "title": "问题讨论与解决",
                    "type": AgendaType.DISCUSSION.value,
                    "priority": AgendaPriority.HIGH.value,
                    "estimated_minutes": 25,
                    "presenter": "dynamic"
                },
                {
                    "title": "协作需求确认",
                    "type": AgendaType.DISCUSSION.value,
                    "priority": AgendaPriority.MEDIUM.value,
                    "estimated_minutes": 10,
                    "presenter": "dynamic"
                },
                {
                    "title": "下步工作安排",
                    "type": AgendaType.PLANNING.value,
                    "priority": AgendaPriority.MEDIUM.value,
                    "estimated_minutes": 5,
                    "presenter": "host"
                }
            ]
        )
        
        self.templates = {
            a_level_template.id: a_level_template,
            b_level_template.id: b_level_template,
            c_level_template.id: c_level_template
        }
    
    def generate_agenda(
        self,
        meeting_level: MeetingLevel,
        meeting_title: str,
        meeting_description: str,
        participants: List[str],
        duration_minutes: int,
        meeting_type: Optional[str] = None,
        custom_topics: Optional[List[str]] = None,
        template_id: Optional[str] = None
    ) -> List[AgendaItem]:
        """生成智能议程"""
        
        # 选择模板
        if template_id:
            template = self.templates.get(template_id)
        else:
            template = self._select_best_template(meeting_level, meeting_title, meeting_description)
        
        if not template:
            return self._generate_basic_agenda(meeting_title, participants, duration_minutes)
        
        # 基于模板生成议程项
        agenda_items = []
        total_estimated_time = 0
        
        for i, template_item in enumerate(template.template_items):
            item_id = f"agenda.{int(time.time())}.{i}"
            
            # 智能分配主讲人
            presenter = self._assign_presenter(
                template_item.get("presenter", "dynamic"),
                participants,
                template_item.get("type")
            )
            
            # 根据会议时长调整时间分配
            estimated_minutes = self._adjust_time_allocation(
                template_item["estimated_minutes"],
                duration_minutes,
                template.estimated_duration
            )
            
            agenda_item = AgendaItem(
                id=item_id,
                title=template_item["title"],
                description=template_item.get("description", ""),
                agenda_type=AgendaType(template_item["type"]),
                priority=AgendaPriority(template_item["priority"]),
                presenter=presenter,
                participants=participants,
                estimated_minutes=estimated_minutes,
                vote_required=template_item.get("vote_required", False),
                vote_type=VoteType(template_item["vote_type"]) if template_item.get("vote_type") else None,
                notes=[],
                decisions=[],
                action_items=[]
            )
            
            agenda_items.append(agenda_item)
            total_estimated_time += estimated_minutes
        
        # 添加自定义议题
        if custom_topics:
            remaining_time = max(0, duration_minutes - total_estimated_time - 10)  # 保留10分钟缓冲
            time_per_topic = remaining_time // len(custom_topics) if custom_topics else 0
            
            for j, topic in enumerate(custom_topics):
                item_id = f"agenda.custom.{int(time.time())}.{j}"
                agenda_item = AgendaItem(
                    id=item_id,
                    title=topic,
                    description=f"自定义议题: {topic}",
                    agenda_type=AgendaType.DISCUSSION,
                    priority=AgendaPriority.MEDIUM,
                    presenter=self._assign_presenter("dynamic", participants, "discussion"),
                    participants=participants,
                    estimated_minutes=max(5, time_per_topic),
                    notes=[],
                    decisions=[],
                    action_items=[]
                )
                agenda_items.append(agenda_item)
        
        # 优化议程顺序
        agenda_items = self._optimize_agenda_order(agenda_items)
        
        # 分配时间段
        agenda_items = self._assign_time_slots(agenda_items, duration_minutes)
        
        return agenda_items
    
    def optimize_agenda_order(self, agenda_items: List[AgendaItem]) -> List[AgendaItem]:
        """优化议程顺序（公共方法）"""
        return self._optimize_agenda_order(agenda_items)
    
    def _select_best_template(self, meeting_level: MeetingLevel, title: str, description: str) -> Optional[AgendaTemplate]:
        """选择最佳模板"""
        # 根据会议级别筛选模板
        level_templates = [t for t in self.templates.values() if t.meeting_level == meeting_level]
        
        if not level_templates:
            return None
        
        # 简单的关键词匹配选择最佳模板
        keywords_score = {}
        for template in level_templates:
            score = 0
            template_keywords = template.name.lower() + " " + template.description.lower()
            
            # 检查标题和描述中的关键词
            text_to_check = (title + " " + description).lower()
            
            if "战略" in text_to_check or "决策" in text_to_check:
                if "strategic" in template.id:
                    score += 10
            
            if "协调" in text_to_check or "项目" in text_to_check:
                if "coordination" in template.id:
                    score += 10
            
            if "日常" in text_to_check or "沟通" in text_to_check:
                if "daily" in template.id:
                    score += 10
            
            keywords_score[template.id] = score
        
        # 返回得分最高的模板
        best_template_id = max(keywords_score, key=keywords_score.get)
        return self.templates[best_template_id]
    
    def _assign_presenter(self, presenter_type: str, participants: List[str], agenda_type: str) -> Optional[str]:
        """智能分配主讲人"""
        if presenter_type == "host":
            return participants[0] if participants else None
        
        elif presenter_type == "ceo":
            for participant in participants:
                if "ceo" in participant.lower():
                    return participant
        
        elif presenter_type == "cfo":
            for participant in participants:
                if "cfo" in participant.lower():
                    return participant
        
        elif presenter_type == "coordinator":
            for participant in participants:
                if "coordinator" in participant.lower():
                    return participant
        
        elif presenter_type == "secretary":
            for participant in participants:
                if "secretary" in participant.lower():
                    return participant
        
        elif presenter_type == "technical_lead":
            for participant in participants:
                if any(role in participant.lower() for role in ["frontend", "backend", "developer"]):
                    return participant
        
        elif presenter_type == "dynamic":
            # 根据议程类型智能分配
            if agenda_type in ["presentation", "update"]:
                return participants[0] if participants else None
            elif agenda_type == "vote":
                # 投票通常由主持人发起
                return participants[0] if participants else None
            else:
                return None  # 讨论类议题不指定固定主讲人
        
        return None
    
    def _adjust_time_allocation(self, template_time: int, actual_duration: int, template_duration: int) -> int:
        """根据实际会议时长调整时间分配"""
        ratio = actual_duration / template_duration
        adjusted_time = int(template_time * ratio)
        return max(5, adjusted_time)  # 最少5分钟
    
    def _optimize_agenda_order(self, agenda_items: List[AgendaItem]) -> List[AgendaItem]:
        """优化议程顺序"""
        # 按优先级和类型排序
        priority_order = {
            AgendaPriority.CRITICAL: 5,
            AgendaPriority.HIGH: 4,
            AgendaPriority.MEDIUM: 3,
            AgendaPriority.LOW: 2,
            AgendaPriority.INFORMATIONAL: 1
        }
        
        type_order = {
            AgendaType.PRESENTATION: 1,  # 开场汇报
            AgendaType.REVIEW: 2,        # 回顾
            AgendaType.UPDATE: 3,        # 更新
            AgendaType.DISCUSSION: 4,    # 讨论
            AgendaType.BRAINSTORM: 5,    # 头脑风暴
            AgendaType.DECISION: 6,      # 决策
            AgendaType.VOTE: 7,          # 投票
            AgendaType.PLANNING: 8       # 规划
        }
        
        def sort_key(item: AgendaItem):
            # 特殊处理：开场和总结固定位置
            if "开场" in item.title or "目标确认" in item.title:
                return (0, 0, 0)
            if "总结" in item.title or "下步安排" in item.title:
                return (10, 0, 0)
            
            return (
                type_order.get(item.agenda_type, 5),
                -priority_order.get(item.priority, 3),
                item.estimated_minutes
            )
        
        return sorted(agenda_items, key=sort_key)
    
    def _assign_time_slots(self, agenda_items: List[AgendaItem], total_duration: int) -> List[AgendaItem]:
        """分配时间段"""
        start_time = datetime.now().replace(second=0, microsecond=0)
        current_time = start_time
        
        for item in agenda_items:
            end_time = current_time + timedelta(minutes=item.estimated_minutes)
            
            item.time_slot = TimeSlot(
                start_time=current_time,
                end_time=end_time,
                duration_minutes=item.estimated_minutes,
                buffer_minutes=2 if item.agenda_type == AgendaType.DISCUSSION else 1
            )
            
            current_time = end_time + timedelta(minutes=item.time_slot.buffer_minutes)
        
        return agenda_items
    
    def _generate_basic_agenda(self, title: str, participants: List[str], duration: int) -> List[AgendaItem]:
        """生成基础议程（无模板时的后备方案）"""
        basic_items = [
            AgendaItem(
                id=f"agenda.basic.{int(time.time())}.0",
                title="会议开场",
                description="介绍会议目标和议程安排",
                agenda_type=AgendaType.PRESENTATION,
                priority=AgendaPriority.HIGH,
                presenter=participants[0] if participants else None,
                participants=participants,
                estimated_minutes=5,
                notes=[],
                decisions=[],
                action_items=[]
            ),
            AgendaItem(
                id=f"agenda.basic.{int(time.time())}.1",
                title="主要议题讨论",
                description=title,
                agenda_type=AgendaType.DISCUSSION,
                priority=AgendaPriority.HIGH,
                presenter=None,
                participants=participants,
                estimated_minutes=duration - 15,  # 总时长减去开场和结尾
                notes=[],
                decisions=[],
                action_items=[]
            ),
            AgendaItem(
                id=f"agenda.basic.{int(time.time())}.2",
                title="会议总结",
                description="总结讨论结果和后续行动",
                agenda_type=AgendaType.PRESENTATION,
                priority=AgendaPriority.MEDIUM,
                presenter=participants[0] if participants else None,
                participants=participants,
                estimated_minutes=10,
                notes=[],
                decisions=[],
                action_items=[]
            )
        ]
        
        return self._assign_time_slots(basic_items, duration)
    
    def update_agenda_progress(self, agenda_id: str, status: str, actual_minutes: int = 0, notes: List[str] = None):
        """更新议程进度"""
        # TODO: 实现议程进度更新逻辑
        pass
    
    def get_agenda_analytics(self, meeting_id: str) -> Dict[str, Any]:
        """获取议程分析数据"""
        # TODO: 实现议程分析逻辑
        return {
            "total_items": 0,
            "completed_items": 0,
            "time_efficiency": 0.0,
            "priority_distribution": {},
            "type_distribution": {}
        }


# 全局智能议程生成器实例
agenda_generator = IntelligentAgendaGenerator()


if __name__ == "__main__":
    # 测试示例
    generator = IntelligentAgendaGenerator()
    
    # 生成A级会议议程
    participants = ["agent.ceo", "agent.cfo", "agent.coordinator", "agent.secretary"]
    agenda_items = generator.generate_agenda(
        meeting_level=MeetingLevel.A_LEVEL,
        meeting_title="Q4战略规划会议",
        meeting_description="讨论第四季度战略规划和预算分配",
        participants=participants,
        duration_minutes=120,
        custom_topics=["新产品线规划", "市场拓展策略"]
    )
    
    print(f"生成了 {len(agenda_items)} 个议程项:")
    for item in agenda_items:
        print(f"- {item.title} ({item.estimated_minutes}分钟) - {item.presenter or '开放讨论'}")
        if item.time_slot:
            print(f"  时间: {item.time_slot.start_time.strftime('%H:%M')} - {item.time_slot.end_time.strftime('%H:%M')}")
    
    # 生成B级会议议程
    b_agenda = generator.generate_agenda(
        meeting_level=MeetingLevel.B_LEVEL,
        meeting_title="项目协调会",
        meeting_description="协调各部门项目进展",
        participants=["agent.coordinator", "agent.frontend", "agent.backend"],
        duration_minutes=90
    )
    
    print(f"\nB级会议议程 ({len(b_agenda)} 项):")
    for item in b_agenda:
        print(f"- {item.title} ({item.estimated_minutes}分钟)")