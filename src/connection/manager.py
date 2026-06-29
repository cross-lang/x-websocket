"""
连接管理器
"""
import asyncio
from typing import Dict, Set, Optional
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """管理WebSocket连接"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.rooms: Dict[str, Set[str]] = {}  # 房间ID -> 客户端ID集合

    async def connect(self, websocket: WebSocket, client_id: str):
        """建立连接"""
        self.active_connections[client_id] = websocket
        logger.info(f"客户端 {client_id} 已连接")

    async def disconnect(self, client_id: str):
        """断开连接"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"客户端 {client_id} 已断开连接")

        # 从所有房间中移除
        for room_id, clients in self.rooms.items():
            if client_id in clients:
                clients.remove(client_id)
                if not clients:
                    del self.rooms[room_id]

    async def send_personal_message(self, message: str, client_id: str):
        """发送个人消息"""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"发送消息给客户端 {client_id} 失败: {e}")

    async def broadcast(self, message: str, exclude_client_id: Optional[str] = None):
        """广播消息给所有连接"""
        for client_id, websocket in self.active_connections.items():
            if client_id == exclude_client_id:
                continue
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"广播消息给客户端 {client_id} 失败: {e}")

    async def join_room(self, room_id: str, client_id: str):
        """加入房间"""
        if room_id not in self.rooms:
            self.rooms[room_id] = set()
        self.rooms[room_id].add(client_id)
        logger.info(f"客户端 {client_id} 加入房间 {room_id}")

    async def leave_room(self, room_id: str, client_id: str):
        """离开房间"""
        if room_id in self.rooms and client_id in self.rooms[room_id]:
            self.rooms[room_id].remove(client_id)
            if not self.rooms[room_id]:
                del self.rooms[room_id]
            logger.info(f"客户端 {client_id} 离开房间 {room_id}")

    async def broadcast_to_room(self, room_id: str, message: str, exclude_client_id: Optional[str] = None):
        """广播消息给房间内的所有客户端"""
        if room_id in self.rooms:
            for client_id in self.rooms[room_id]:
                if client_id == exclude_client_id:
                    continue
                await self.send_personal_message(message, client_id)

    def get_active_client_count(self) -> int:
        """获取活跃连接数"""
        return len(self.active_connections)

    def get_room_client_count(self, room_id: str) -> int:
        """获取房间内的客户端数量"""
        return len(self.rooms.get(room_id, set()))