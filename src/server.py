"""
FastAPI WebSocket服务器主模块
"""
import asyncio
import json
import logging
from typing import Dict, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware

from .core.config import Settings
from .connection.manager import ConnectionManager
from .auth.jwt_auth import JWTAuthService
from .models.message import BaseMessage, MessageType, ChatMessage, StreamRequest, StatusRequest
from .llm.base import LLMFactory
from .handlers.stream import StreamingHandler
from .handlers.chat import ChatHandler
from .handlers.status import StatusHandler

logger = logging.getLogger(__name__)

app = FastAPI(
    title="x-websocket",
    description="WebSocket-based LLM demonstration application",
    version="0.1.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局对象
settings = Settings()
connection_manager = ConnectionManager()
auth_service = JWTAuthService(
    secret_key=settings.jwt_secret,
    algorithm=settings.jwt_algorithm
)

# LLM工厂和处理器
llm_factory = LLMFactory()
streaming_handler = StreamingHandler(connection_manager, llm_factory, settings)
chat_handler = ChatHandler(connection_manager, llm_factory, settings)
status_handler = StatusHandler(connection_manager, llm_factory, settings)

@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    logger.info(f"启动 x-websocket 服务器，版本 {__version__}")
    logger.info(f"服务器运行在 {settings.host}:{settings.port}")
    logger.info(f"调试模式: {settings.debug}")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    logger.info("关闭 x-websocket 服务器")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket 主端点
    处理连接、认证和消息路由
    """
    # 接受WebSocket连接
    await websocket.accept()

    client_id = None
    try:
        # 等待认证消息
        auth_message = await websocket.receive_text()
        auth_data = json.loads(auth_message)

        # 验证认证令牌
        if "token" not in auth_data:
            await websocket.send_json({
                "type": "error",
                "message": "需要认证令牌"
            })
            await websocket.close()
            return

        token = auth_data["token"]
        try:
            payload = auth_service.verify_token(token)
            client_id = payload.get("sub")
            if not client_id:
                raise ValueError("无效的令牌负载")
        except Exception as e:
            logger.warning(f"认证失败: {e}")
            await websocket.send_json({
                "type": "error",
                "message": "认证失败"
            })
            await websocket.close()
            return

        # 注册连接
        await connection_manager.connect(websocket, client_id)
        logger.info(f"客户端 {client_id} 已连接")

        await websocket.send_json({
            "type": "connected",
            "message": "认证成功，连接已建立",
            "client_id": client_id
        })

        # 消息循环
        while True:
            try:
                message = await websocket.receive_text()
                await handle_message(websocket, client_id, message)
            except WebSocketDisconnect:
                logger.info(f"客户端 {client_id} 断开连接")
                break
            except Exception as e:
                logger.error(f"处理消息时出错: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": f"处理消息时出错: {str(e)}"
                })

    except Exception as e:
        logger.error(f"WebSocket连接错误: {e}")
    finally:
        if client_id:
            await connection_manager.disconnect(client_id)

async def handle_message(websocket: WebSocket, client_id: str, message_str: str):
    """
    处理接收到的消息
    """
    try:
        message_data = json.loads(message_str)
        message_type = message_data.get("type")

        # 根据消息类型路由到不同的处理器
        if message_type == MessageType.CHAT:
            # 转换为ChatMessage模型
            chat_message = ChatMessage(**message_data)
            await chat_handler.handle(websocket, chat_message, client_id)

        elif message_type == MessageType.STREAM:
            # 转换为StreamRequest模型
            stream_request = StreamRequest(**message_data)
            await streaming_handler.handle(websocket, stream_request, client_id)

        elif message_type == MessageType.STATUS:
            # 转换为StatusRequest模型
            status_request = StatusRequest(**message_data)
            await status_handler.handle(websocket, status_request, client_id)

        elif message_type == MessageType.PING:
            await websocket.send_json({"type": "pong", "timestamp": asyncio.get_event_loop().time()})

        else:
            await websocket.send_json({
                "type": "error",
                "message": f"未知的消息类型: {message_type}"
            })

    except json.JSONDecodeError:
        await websocket.send_json({
            "type": "error",
            "message": "无效的JSON格式"
        })
    except Exception as e:
        logger.error(f"处理消息时出错: {e}")
        await websocket.send_json({
            "type": "error",
            "message": f"处理消息时出错: {str(e)}"
        })


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "service": "x-websocket"}

@app.get("/")
async def root():
    """根端点"""
    return {
        "name": "x-websocket",
        "version": __version__,
        "documentation": "/docs",
        "websocket_endpoint": "/ws"
    }

# 导入版本信息
from . import __version__