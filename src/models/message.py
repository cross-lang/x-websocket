"""
消息数据模型
"""
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class MessageType(str, Enum):
    """消息类型枚举"""
    CHAT = "chat"
    STREAM = "stream"
    STATUS = "status"
    PING = "ping"
    PONG = "pong"
    ERROR = "error"
    CONNECTED = "connected"


class BaseMessage(BaseModel):
    """基础消息模型"""
    type: MessageType
    timestamp: float = Field(default_factory=lambda: datetime.utcnow().timestamp())


class ChatMessage(BaseMessage):
    """聊天消息"""
    type: MessageType = MessageType.CHAT
    content: str
    room_id: Optional[str] = None
    to_user_id: Optional[str] = None
    require_assistant: bool = False


class StreamRequest(BaseMessage):
    """流式生成请求"""
    type: MessageType = MessageType.STREAM
    prompt: str
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000
    stream: bool = True


class StreamChunk(BaseMessage):
    """流式生成分块"""
    type: MessageType = MessageType.STREAM
    content: str
    chunk_id: int
    is_complete: bool = False


class StatusRequest(BaseMessage):
    """状态查询请求"""
    type: MessageType = MessageType.STATUS
    task_id: str
    action: str = "query"  # query, subscribe, cancel


class StatusResponse(BaseMessage):
    """状态响应"""
    type: MessageType = MessageType.STATUS
    task_id: str
    status: str  # pending, running, completed, failed
    progress: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    estimated_time: Optional[float] = None


class ErrorMessage(BaseMessage):
    """错误消息"""
    type: MessageType = MessageType.ERROR
    message: str
    code: Optional[str] = None


class ConnectedMessage(BaseMessage):
    """连接成功消息"""
    type: MessageType = MessageType.CONNECTED
    message: str
    client_id: str