"""
流式LLM响应处理器
"""
import json
import logging
from typing import Dict, Any
from fastapi import WebSocket

from .base import BaseHandler
from ..models.message import StreamRequest, StreamChunk
from ..llm.base import LLMFactory, LLMConfig


logger = logging.getLogger(__name__)


class StreamingHandler(BaseHandler):
    """流式LLM响应处理器"""

    def __init__(self, connection_manager, llm_factory: LLMFactory, settings):
        super().__init__(connection_manager, llm_factory, settings)

    async def handle(self, websocket: WebSocket, message: StreamRequest, client_id: str):
        """
        处理流式生成请求

        Args:
            websocket: WebSocket连接
            message: 流式请求消息
            client_id: 客户端ID
        """
        self.logger.info(f"处理流式请求，客户端: {client_id}, 提示词长度: {len(message.prompt)}")

        try:
            # 创建LLM客户端
            llm_client = self.llm_factory.create_from_settings(self.settings)

            # 开始流式生成
            chunk_id = 0
            async for chunk in llm_client.generate_stream(
                prompt=message.prompt,
                model=message.model,
                temperature=message.temperature,
                max_tokens=message.max_tokens
            ):
                # 发送流式分块
                stream_chunk = StreamChunk(
                    content=chunk,
                    chunk_id=chunk_id,
                    is_complete=False
                )
                await self.send_message(websocket, stream_chunk)
                chunk_id += 1

            # 发送完成消息
            complete_chunk = StreamChunk(
                content="",
                chunk_id=chunk_id,
                is_complete=True
            )
            await self.send_message(websocket, complete_chunk)

            self.logger.info(f"流式生成完成，客户端: {client_id}, 分块数: {chunk_id}")

        except Exception as e:
            self.logger.error(f"流式处理失败: {e}")
            await self.send_error(
                websocket,
                f"流式生成失败: {str(e)}",
                code="STREAM_ERROR"
            )