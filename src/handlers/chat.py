"""
实时聊天处理器
"""
import json
import logging
import asyncio
from typing import Dict, Any
from fastapi import WebSocket

from .base import BaseHandler
from ..models.message import ChatMessage, ErrorMessage
from ..llm.base import LLMFactory


logger = logging.getLogger(__name__)


class ChatHandler(BaseHandler):
    """实时聊天处理器"""

    def __init__(self, connection_manager, llm_factory: LLMFactory, settings):
        super().__init__(connection_manager, llm_factory, settings)
        self.user_sessions: Dict[str, Dict[str, Any]] = {}
        self.room_conversations: Dict[str, list] = {}

    async def handle(self, websocket: WebSocket, message: ChatMessage, client_id: str):
        """
        处理聊天消息

        Args:
            websocket: WebSocket连接
            message: 聊天消息
            client_id: 客户端ID
        """
        self.logger.info(f"处理聊天消息，客户端: {client_id}, 房间: {message.room_id}")

        # 确保用户会话存在
        if client_id not in self.user_sessions:
            self.user_sessions[client_id] = {
                "rooms": set(),
                "conversation_history": []
            }

        # 如果有房间ID，加入房间
        if message.room_id:
            await self._handle_room_message(websocket, message, client_id)
        else:
            await self._handle_private_message(websocket, message, client_id)

    async def _handle_room_message(self, websocket: WebSocket, message: ChatMessage, client_id: str):
        """处理房间消息"""
        room_id = message.room_id

        # 加入房间
        if room_id not in self.user_sessions[client_id]["rooms"]:
            await self.connection_manager.join_room(room_id, client_id)
            self.user_sessions[client_id]["rooms"].add(room_id)

            # 初始化房间对话历史
            if room_id not in self.room_conversations:
                self.room_conversations[room_id] = []

        # 广播消息到房间
        broadcast_msg = {
            "type": "chat",
            "from": client_id,
            "room_id": room_id,
            "content": message.content,
            "timestamp": asyncio.get_event_loop().time()
        }

        await self.connection_manager.broadcast_to_room(
            room_id,
            json.dumps(broadcast_msg),
            exclude_client_id=client_id
        )

        # 添加到房间对话历史
        self.room_conversations[room_id].append({
            "role": "user",
            "content": message.content,
            "user_id": client_id
        })

        # 如果需要助手回复
        if message.require_assistant:
            await self._generate_assistant_reply(websocket, message, client_id, room_id)

    async def _handle_private_message(self, websocket: WebSocket, message: ChatMessage, client_id: str):
        """处理私聊消息"""
        # 这里可以处理私聊消息
        # 暂时简单回复
        reply = {
            "type": "chat",
            "from": "system",
            "to": client_id,
            "content": f"收到你的消息: {message.content}",
            "timestamp": asyncio.get_event_loop().time()
        }

        await websocket.send_json(reply)

    async def _generate_assistant_reply(self, websocket: WebSocket, message: ChatMessage, client_id: str, room_id: str):
        """生成助手回复"""
        try:
            # 创建LLM客户端
            llm_client = self.llm_factory.create_from_settings(self.settings)

            # 准备对话历史
            conversation = self.room_conversations.get(room_id, [])
            messages = [
                {"role": "system", "content": "你是一个有帮助的AI助手，在聊天室中协助用户。"}
            ]

            # 添加最近的对话历史（限制长度）
            for msg in conversation[-10:]:  # 最多10条历史
                role = "assistant" if msg.get("user_id") == "assistant" else "user"
                messages.append({"role": role, "content": msg["content"]})

            # 调用LLM生成回复
            response = await llm_client.chat(messages)

            # 广播助手回复
            assistant_msg = {
                "type": "chat",
                "from": "assistant",
                "room_id": room_id,
                "content": response["content"],
                "timestamp": asyncio.get_event_loop().time()
            }

            await self.connection_manager.broadcast_to_room(
                room_id,
                json.dumps(assistant_msg)
            )

            # 添加到房间对话历史
            self.room_conversations[room_id].append({
                "role": "assistant",
                "content": response["content"],
                "user_id": "assistant"
            })

        except Exception as e:
            self.logger.error(f"生成助手回复失败: {e}")
            error_msg = {
                "type": "chat",
                "from": "system",
                "room_id": room_id,
                "content": f"助手回复生成失败: {str(e)}",
                "timestamp": asyncio.get_event_loop().time()
            }

            await websocket.send_json(error_msg)