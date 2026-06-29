"""
消息处理器基类
"""
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from fastapi import WebSocket

from ..models.message import BaseMessage, ErrorMessage
from ..llm.base import LLMFactory


logger = logging.getLogger(__name__)


class BaseHandler(ABC):
    """消息处理器基类"""

    def __init__(self, connection_manager, llm_factory: LLMFactory, settings):
        self.connection_manager = connection_manager
        self.llm_factory = llm_factory
        self.settings = settings
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    async def handle(self, websocket: WebSocket, message: BaseMessage, client_id: str):
        """
        处理消息

        Args:
            websocket: WebSocket连接
            message: 消息对象
            client_id: 客户端ID
        """
        pass

    async def send_error(self, websocket: WebSocket, message: str, code: Optional[str] = None):
        """发送错误消息"""
        error_msg = ErrorMessage(
            message=message,
            code=code
        )
        await websocket.send_json(error_msg.model_dump())

    async def send_message(self, websocket: WebSocket, message: BaseMessage):
        """发送消息"""
        await websocket.send_json(message.model_dump())

    def validate_message(self, message_data: Dict[str, Any], required_fields: list) -> bool:
        """
        验证消息字段

        Args:
            message_data: 消息数据
            required_fields: 必需字段列表

        Returns:
            是否验证通过
        """
        for field in required_fields:
            if field not in message_data:
                return False
        return True

    def get_llm_client(self, provider: Optional[str] = None):
        """
        获取LLM客户端

        Args:
            provider: 模型提供商，如果为None则使用默认配置

        Returns:
            LLM客户端实例
        """
        # 这里需要从配置获取默认LLM
        # 暂时返回None，实际实现中应从工厂创建
        return None