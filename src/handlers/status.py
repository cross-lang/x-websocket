"""
模型推理状态推送处理器
"""
import json
import logging
import asyncio
import uuid
from typing import Dict, Any, Optional
from fastapi import WebSocket

from .base import BaseHandler
from ..models.message import StatusRequest, StatusResponse
from ..llm.base import LLMFactory


logger = logging.getLogger(__name__)


class TaskStatus:
    """任务状态"""

    def __init__(self, task_id: str, task_type: str, config: Dict[str, Any]):
        self.task_id = task_id
        self.task_type = task_type
        self.config = config
        self.status = "pending"  # pending, running, completed, failed
        self.progress = 0.0
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.created_at = asyncio.get_event_loop().time()
        self.updated_at = self.created_at
        self.subscribers: set = set()  # 订阅此任务状态的客户端ID


class StatusHandler(BaseHandler):
    """模型推理状态推送处理器"""

    def __init__(self, connection_manager, llm_factory: LLMFactory, settings):
        super().__init__(connection_manager, llm_factory, settings)
        self.tasks: Dict[str, TaskStatus] = {}

    async def handle(self, websocket: WebSocket, message: StatusRequest, client_id: str):
        """
        处理状态请求

        Args:
            websocket: WebSocket连接
            message: 状态请求消息
            client_id: 客户端ID
        """
        self.logger.info(f"处理状态请求，客户端: {client_id}, 任务ID: {message.task_id}, 动作: {message.action}")

        if message.action == "subscribe":
            await self._handle_subscribe(websocket, message, client_id)
        elif message.action == "query":
            await self._handle_query(websocket, message, client_id)
        elif message.action == "cancel":
            await self._handle_cancel(websocket, message, client_id)
        else:
            await self.send_error(
                websocket,
                f"未知的动作: {message.action}",
                code="UNKNOWN_ACTION"
            )

    async def _handle_subscribe(self, websocket: WebSocket, message: StatusRequest, client_id: str):
        """处理订阅请求"""
        task_id = message.task_id

        # 如果任务不存在，创建新任务
        if task_id not in self.tasks:
            # 这里可以根据配置创建不同类型的任务
            # 暂时创建一个模拟任务
            task = TaskStatus(
                task_id=task_id,
                task_type="llm_inference",
                config={"prompt": "模拟推理任务"}
            )
            self.tasks[task_id] = task

            # 启动任务执行
            asyncio.create_task(self._execute_task(task))

        # 订阅任务状态更新
        task = self.tasks[task_id]
        task.subscribers.add(client_id)

        # 发送当前状态
        response = StatusResponse(
            task_id=task_id,
            status=task.status,
            progress=task.progress,
            result=task.result,
            estimated_time=self._estimate_time(task)
        )
        await self.send_message(websocket, response)

        self.logger.info(f"客户端 {client_id} 订阅任务 {task_id}")

    async def _handle_query(self, websocket: WebSocket, message: StatusRequest, client_id: str):
        """处理查询请求"""
        task_id = message.task_id

        if task_id not in self.tasks:
            await self.send_error(
                websocket,
                f"任务不存在: {task_id}",
                code="TASK_NOT_FOUND"
            )
            return

        task = self.tasks[task_id]

        response = StatusResponse(
            task_id=task_id,
            status=task.status,
            progress=task.progress,
            result=task.result,
            estimated_time=self._estimate_time(task)
        )
        await self.send_message(websocket, response)

    async def _handle_cancel(self, websocket: WebSocket, message: StatusRequest, client_id: str):
        """处理取消请求"""
        task_id = message.task_id

        if task_id not in self.tasks:
            await self.send_error(
                websocket,
                f"任务不存在: {task_id}",
                code="TASK_NOT_FOUND"
            )
            return

        task = self.tasks[task_id]

        # 只有任务在运行或等待中才能取消
        if task.status in ["pending", "running"]:
            task.status = "cancelled"
            task.updated_at = asyncio.get_event_loop().time()

            # 通知订阅者
            await self._notify_subscribers(task)

            response = StatusResponse(
                task_id=task_id,
                status=task.status,
                progress=task.progress,
                result={"message": "任务已取消"}
            )
            await self.send_message(websocket, response)
        else:
            await self.send_error(
                websocket,
                f"任务状态为 {task.status}，无法取消",
                code="CANNOT_CANCEL"
            )

    async def _execute_task(self, task: TaskStatus):
        """执行任务（模拟）"""
        try:
            # 更新状态为运行中
            task.status = "running"
            task.updated_at = asyncio.get_event_loop().time()
            await self._notify_subscribers(task)

            # 模拟任务执行过程
            steps = 10
            for i in range(steps):
                # 模拟处理时间
                await asyncio.sleep(1.0)

                # 更新进度
                task.progress = (i + 1) / steps * 100
                task.updated_at = asyncio.get_event_loop().time()

                # 通知订阅者
                await self._notify_subscribers(task)

            # 任务完成
            task.status = "completed"
            task.progress = 100.0
            task.result = {
                "output": "任务执行完成",
                "metrics": {"time_taken": steps, "steps": steps}
            }
            task.updated_at = asyncio.get_event_loop().time()

            # 通知订阅者
            await self._notify_subscribers(task)

            self.logger.info(f"任务 {task.task_id} 完成")

        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            task.updated_at = asyncio.get_event_loop().time()

            # 通知订阅者
            await self._notify_subscribers(task)

            self.logger.error(f"任务 {task.task_id} 失败: {e}")

    async def _notify_subscribers(self, task: TaskStatus):
        """通知所有订阅者"""
        if not task.subscribers:
            return

        response = StatusResponse(
            task_id=task.task_id,
            status=task.status,
            progress=task.progress,
            result=task.result,
            estimated_time=self._estimate_time(task)
        )

        response_json = json.dumps(response.model_dump())

        for client_id in task.subscribers.copy():  # 使用副本避免迭代时修改
            try:
                await self.connection_manager.send_personal_message(response_json, client_id)
            except Exception as e:
                self.logger.error(f"通知客户端 {client_id} 失败: {e}")
                # 如果通知失败，移除订阅者
                task.subscribers.discard(client_id)

    def _estimate_time(self, task: TaskStatus) -> Optional[float]:
        """估算剩余时间（模拟）"""
        if task.status in ["completed", "failed", "cancelled"]:
            return 0.0

        if task.progress > 0:
            elapsed = asyncio.get_event_loop().time() - task.created_at
            remaining = (elapsed / task.progress) * (100 - task.progress)
            return remaining
        else:
            return 10.0  # 默认估计10秒