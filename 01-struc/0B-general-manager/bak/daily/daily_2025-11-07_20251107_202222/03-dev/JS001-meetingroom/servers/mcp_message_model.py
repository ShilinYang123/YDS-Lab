#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP统一消息模型 - 支持多通道会议协作
按照YDS AI公司建设方案V3.0实现
"""

import json
import time
import uuid
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from enum import Enum


class ChannelType(Enum):
    """通道类型枚举"""
    TEXT = "text"
    VOICE = "voice"
    DOCS = "docs"
    VOTE = "vote"
    SYSTEM = "system"
    MEETING = "meeting"


class EventType(Enum):
    """事件类型枚举"""
    # 文字通道
    MESSAGE_TEXT = "message.text"
    MESSAGE_REPLY = "message.reply"
    MESSAGE_EDIT = "message.edit"
    MESSAGE_DELETE = "message.delete"
    
    # 语音通道
    VOICE_STREAM = "voice.stream"
    VOICE_START = "voice.start"
    VOICE_END = "voice.end"
    VOICE_TRANSCRIBE = "voice.transcribe"
    
    # 文档共享
    DOCS_SHARE = "docs.share"
    DOCS_REVOKE = "docs.revoke"
    DOCS_ACCESS = "docs.access"
    DOCS_DOWNLOAD = "docs.download"
    
    # 投票系统
    VOTE_CREATE = "vote.create"
    VOTE_CAST = "vote.cast"
    VOTE_UPDATE = "vote.update"
    VOTE_FINALIZE = "vote.finalize"
    
    # 系统事件
    SYSTEM_NOTICE = "system.notice"
    SYSTEM_ERROR = "system.error"
    SYSTEM_STATUS = "system.status"
    
    # 会议控制
    MEETING_START = "meeting.start"
    MEETING_END = "meeting.end"
    MEETING_PAUSE = "meeting.pause"
    MEETING_RESUME = "meeting.resume"
    
    # 举手系统
    HAND_RAISE = "hand.raise"
    HAND_LOWER = "hand.lower"
    HAND_APPROVE = "hand.approve"


@dataclass
class AgentInfo:
    """智能体信息"""
    id: Optional[str] = None
    role: Optional[str] = None
    display_name: Optional[str] = None
    department: Optional[str] = None
    avatar: Optional[str] = None
    permissions: List[str] = None
    
    def __post_init__(self):
        """初始化后处理"""
        if self.permissions is None:
            self.permissions = []


@dataclass
class TextPayload:
    """文字消息载荷"""
    content: str
    reply_to: Optional[str] = None
    mentions: Optional[List[str]] = None
    attachments: Optional[List[str]] = None


@dataclass
class VoicePayload:
    """语音消息载荷"""
    session_id: str
    chunk_seq: int
    sample_rate: int
    format: str  # pcm16, webm, opus
    data_base64: str
    is_final: bool = False
    transcript: Optional[str] = None
    confidence: Optional[float] = None


@dataclass
class DocsPayload:
    """文档共享载荷"""
    action: str  # share, revoke, access, download
    path: str
    name: str
    type: str  # pdf, docx, xlsx, pptx, md, txt
    size: int
    hash: str
    permissions: str  # read, write, admin
    expires_at: Optional[str] = None
    watermark: Optional[str] = None


@dataclass
class VotePayload:
    """投票载荷"""
    proposal_id: str
    title: str
    description: Optional[str] = None
    options: List[str] = None
    selected: Optional[str] = None
    anonymous: bool = False
    weight: int = 1
    quorum: float = 0.6
    expires_at: Optional[str] = None
    results: Optional[Dict[str, int]] = None
    status: str = "active"  # active, closed, cancelled


@dataclass
class SystemPayload:
    """系统消息载荷"""
    type: str  # notice, error, status, warning
    code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


@dataclass
class MCPMessage:
    """MCP统一消息模型"""
    id: str
    room_id: str
    channel: ChannelType
    event_type: EventType
    topic: str
    sender: AgentInfo
    timestamp: float
    payload: Union[TextPayload, VoicePayload, DocsPayload, VotePayload, SystemPayload]
    
    # 可选字段
    priority: str = "normal"  # low, normal, high, urgent
    encrypted: bool = False
    signature: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "id": self.id,
            "room_id": self.room_id,
            "channel": self.channel.value,
            "event_type": self.event_type.value,
            "topic": self.topic,
            "sender": asdict(self.sender),
            "timestamp": self.timestamp,
            "priority": self.priority,
            "encrypted": self.encrypted,
            "signature": self.signature,
            "metadata": self.metadata or {}
        }
        
        # 根据通道类型添加对应的payload
        if isinstance(self.payload, (TextPayload, VoicePayload, DocsPayload, VotePayload, SystemPayload)):
            result["payload"] = {self.channel.value: asdict(self.payload)}
        else:
            result["payload"] = {}
            
        return result

    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPMessage':
        """从字典创建消息对象"""
        channel = ChannelType(data["channel"])
        event_type = EventType(data["event_type"])
        
        # 解析sender
        sender = AgentInfo(**data["sender"])
        
        # 解析payload
        payload_data = data["payload"].get(channel.value, {})
        if channel == ChannelType.TEXT:
            payload = TextPayload(**payload_data)
        elif channel == ChannelType.VOICE:
            payload = VoicePayload(**payload_data)
        elif channel == ChannelType.DOCS:
            payload = DocsPayload(**payload_data)
        elif channel == ChannelType.VOTE:
            payload = VotePayload(**payload_data)
        elif channel == ChannelType.SYSTEM:
            payload = SystemPayload(**payload_data)
        else:
            payload = SystemPayload(type="unknown")
        
        return cls(
            id=data["id"],
            room_id=data["room_id"],
            channel=channel,
            event_type=event_type,
            topic=data["topic"],
            sender=sender,
            timestamp=data["timestamp"],
            payload=payload,
            priority=data.get("priority", "normal"),
            encrypted=data.get("encrypted", False),
            signature=data.get("signature"),
            metadata=data.get("metadata", {})
        )


class MCPMessageBuilder:
    """MCP消息构建器"""
    
    @staticmethod
    def create_text_message(
        room_id: str,
        sender: AgentInfo,
        content: str,
        reply_to: Optional[str] = None,
        mentions: Optional[List[str]] = None
    ) -> MCPMessage:
        """创建文字消息"""
        msg_id = f"msg-{int(time.time())}-{uuid.uuid4().hex[:8]}"
        topic = f"rooms/{room_id}/text/message.text"
        
        payload = TextPayload(
            content=content,
            reply_to=reply_to,
            mentions=mentions
        )
        
        return MCPMessage(
            id=msg_id,
            room_id=room_id,
            channel=ChannelType.TEXT,
            event_type=EventType.MESSAGE_TEXT,
            topic=topic,
            sender=sender,
            timestamp=time.time(),
            payload=payload
        )
    
    @staticmethod
    def create_voice_stream(
        room_id: str,
        sender: AgentInfo,
        session_id: str,
        chunk_seq: int,
        audio_data: str,
        sample_rate: int = 16000,
        format: str = "pcm16"
    ) -> MCPMessage:
        """创建语音流消息"""
        msg_id = f"voice-{int(time.time())}-{uuid.uuid4().hex[:8]}"
        topic = f"rooms/{room_id}/voice/voice.stream"
        
        payload = VoicePayload(
            session_id=session_id,
            chunk_seq=chunk_seq,
            sample_rate=sample_rate,
            format=format,
            data_base64=audio_data
        )
        
        return MCPMessage(
            id=msg_id,
            room_id=room_id,
            channel=ChannelType.VOICE,
            event_type=EventType.VOICE_STREAM,
            topic=topic,
            sender=sender,
            timestamp=time.time(),
            payload=payload
        )
    
    @staticmethod
    def create_docs_share(
        room_id: str,
        sender: AgentInfo,
        file_path: str,
        file_name: str,
        file_type: str,
        file_size: int,
        file_hash: str,
        permissions: str = "read"
    ) -> MCPMessage:
        """创建文档共享消息"""
        msg_id = f"docs-{int(time.time())}-{uuid.uuid4().hex[:8]}"
        topic = f"rooms/{room_id}/docs/docs.share"
        
        payload = DocsPayload(
            action="share",
            path=file_path,
            name=file_name,
            type=file_type,
            size=file_size,
            hash=file_hash,
            permissions=permissions
        )
        
        return MCPMessage(
            id=msg_id,
            room_id=room_id,
            channel=ChannelType.DOCS,
            event_type=EventType.DOCS_SHARE,
            topic=topic,
            sender=sender,
            timestamp=time.time(),
            payload=payload
        )
    
    @staticmethod
    def create_vote(
        room_id: str,
        sender: AgentInfo,
        title: str,
        options: List[str],
        description: Optional[str] = None,
        anonymous: bool = False,
        quorum: float = 0.6,
        expires_minutes: int = 60
    ) -> MCPMessage:
        """创建投票消息"""
        msg_id = f"vote-{int(time.time())}-{uuid.uuid4().hex[:8]}"
        topic = f"rooms/{room_id}/vote/vote.create"
        
        expires_at = time.time() + (expires_minutes * 60)
        
        payload = VotePayload(
            proposal_id=msg_id,
            title=title,
            description=description,
            options=options,
            anonymous=anonymous,
            quorum=quorum,
            expires_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(expires_at))
        )
        
        return MCPMessage(
            id=msg_id,
            room_id=room_id,
            channel=ChannelType.VOTE,
            event_type=EventType.VOTE_CREATE,
            topic=topic,
            sender=sender,
            timestamp=time.time(),
            payload=payload
        )
    
    @staticmethod
    def create_system_notice(
        room_id: str,
        message_type: str,
        content: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> MCPMessage:
        """创建系统通知消息"""
        msg_id = f"sys-{int(time.time())}-{uuid.uuid4().hex[:8]}"
        topic = f"rooms/{room_id}/system/system.notice"
        
        system_agent = AgentInfo(
            id="system",
            role="system",
            display_name="系统"
        )
        
        payload = SystemPayload(
            type=message_type,
            code=code,
            details=details or {"message": content}
        )
        
        return MCPMessage(
            id=msg_id,
            room_id=room_id,
            channel=ChannelType.SYSTEM,
            event_type=EventType.SYSTEM_NOTICE,
            topic=topic,
            sender=system_agent,
            timestamp=time.time(),
            payload=payload
        )


# 消息验证器
class MCPMessageValidator:
    """MCP消息验证器"""
    
    @staticmethod
    def validate_message(message_dict: Dict[str, Any]) -> tuple[bool, List[str]]:
        """验证消息格式"""
        errors = []
        try:
            # 基本字段验证
            if not message_dict.get('id') or not message_dict.get('room_id'):
                errors.append("消息ID和房间ID不能为空")
            
            sender = message_dict.get('sender', {})
            if not sender or not sender.get('id'):
                errors.append("发送者信息不能为空")
            
            # 载荷验证
            channel = message_dict.get('channel')
            payload_wrapper = message_dict.get('payload', {})
            
            if channel == ChannelType.TEXT.value:
                text_payload = payload_wrapper.get('text', {})
                if not text_payload.get('content', '').strip():
                    errors.append("文字内容不能为空")
            
            elif channel == ChannelType.VOICE.value:
                voice_payload = payload_wrapper.get('voice', {})
                if not voice_payload.get('session_id') or not voice_payload.get('data_base64'):
                    errors.append("语音数据不完整")
            
            elif channel == ChannelType.DOCS.value:
                docs_payload = payload_wrapper.get('docs', {})
                if not docs_payload.get('path') or not docs_payload.get('name'):
                    errors.append("文档路径和名称不能为空")
            
            elif channel == ChannelType.VOTE.value:
                vote_payload = payload_wrapper.get('vote', {})
                if not vote_payload.get('title') or not vote_payload.get('options'):
                    errors.append("投票标题和选项不能为空")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            errors.append(f"验证过程中出现错误: {str(e)}")
            return False, errors
    
    @staticmethod
    def validate_topic_format(topic: str, room_id: str, channel: str, event_type: str) -> bool:
        """验证主题格式"""
        expected = f"rooms/{room_id}/{channel}/{event_type}"
        return topic == expected


if __name__ == "__main__":
    # 测试示例
    ceo_agent = AgentInfo(
        id="agent.ceo",
        role="CEO",
        display_name="总经理智能体",
        department="管理层"
    )
    
    # 创建文字消息
    text_msg = MCPMessageBuilder.create_text_message(
        room_id="room-2025-001",
        sender=ceo_agent,
        content="大家好，现在开始讨论AI去水印工具项目。"
    )
    
    print("文字消息示例:")
    print(text_msg.to_json())
    print("\n" + "="*50 + "\n")
    
    # 创建投票消息
    vote_msg = MCPMessageBuilder.create_vote(
        room_id="room-2025-001",
        sender=ceo_agent,
        title="是否启动AI去水印工具项目？",
        options=["同意", "反对", "需要更多信息"],
        description="基于技术可行性分析，决定是否正式启动该项目。",
        quorum=0.7
    )
    
    print("投票消息示例:")
    print(vote_msg.to_json())