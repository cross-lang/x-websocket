"""
模拟LLM实现
"""
import asyncio
import random
from typing import AsyncGenerator, Dict, List, Any
from .base import BaseLLM, LLMConfig


class MockLLM(BaseLLM):
    """模拟LLM，用于测试和演示"""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.responses = [
            "这是一个模拟响应。WebSocket连接正常，LLM集成工作正常。",
            "你好！我是模拟AI助手，很高兴通过WebSocket与你交流。",
            "流式传输测试：这是第一条消息。",
            "流式传输测试：这是第二条消息。",
            "流式传输测试：这是第三条消息。",
            "实时聊天演示：多个用户可以通过WebSocket进行实时交流。",
            "状态推送演示：长任务的状态更新会通过WebSocket实时推送。",
            "这个演示项目展示了WebSocket在大模型开发中的应用。",
            "使用FastAPI + WebSocket构建实时应用非常高效。",
            "JWT认证和消息加密确保了通信的安全性。",
        ]
        self.task_status = {
            "pending": "任务等待中",
            "running": "任务运行中",
            "completed": "任务已完成",
            "failed": "任务失败"
        }

    async def generate_stream(
        self,
        prompt: str,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        模拟流式生成

        Args:
            prompt: 提示词
            **kwargs: 额外参数

        Yields:
            模拟生成的文本块
        """
        self.logger.info(f"模拟流式生成，提示词: {prompt[:50]}...")

        # 根据提示词选择响应
        response_idx = hash(prompt) % len(self.responses)
        response = self.responses[response_idx]

        # 模拟流式生成：逐词返回
        words = response.split()
        for i, word in enumerate(words):
            # 添加一些随机延迟以模拟真实流式传输
            await asyncio.sleep(random.uniform(0.05, 0.15))
            yield word + (" " if i < len(words) - 1 else "")

        # 可选：生成一些额外内容
        if len(words) < 5:
            extra = " [模拟流式传输完成]"
            await asyncio.sleep(0.2)
            yield extra

    async def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        模拟聊天接口

        Args:
            messages: 消息列表
            **kwargs: 额外参数

        Returns:
            模拟聊天响应
        """
        self.logger.info(f"模拟聊天，消息数: {len(messages)}")

        if not messages:
            return {
                "content": "请发送消息开始聊天。",
                "role": "assistant",
                "tokens": 0,
                "finish_reason": "stop"
            }

        last_message = messages[-1]["content"]
        response_idx = hash(last_message) % len(self.responses)
        response = self.responses[response_idx]

        return {
            "content": response,
            "role": "assistant",
            "tokens": len(response.split()),
            "finish_reason": "stop",
            "model": "mock-model",
            "created_at": asyncio.get_event_loop().time()
        }

    async def get_status(self, task_id: str) -> Dict[str, Any]:
        """
        模拟任务状态查询

        Args:
            task_id: 任务ID

        Returns:
            模拟任务状态
        """
        self.logger.info(f"模拟状态查询，任务ID: {task_id}")

        # 根据任务ID生成确定性状态
        status_idx = hash(task_id) % len(self.task_status)
        status_keys = list(self.task_status.keys())
        status = status_keys[status_idx]

        result = {
            "task_id": task_id,
            "status": status,
            "message": self.task_status[status],
            "progress": random.randint(0, 100),
            "estimated_time": random.uniform(0.5, 10.0),
            "started_at": asyncio.get_event_loop().time() - random.uniform(10, 100),
            "updated_at": asyncio.get_event_loop().time()
        }

        if status == "completed":
            result["result"] = {"output": f"任务 {task_id} 已完成，输出: 模拟结果"}
        elif status == "failed":
            result["error"] = {"code": "MOCK_ERROR", "message": "模拟错误"}

        return result

    async def create_long_running_task(self, task_config: Dict[str, Any]) -> str:
        """
        创建模拟长时任务

        Args:
            task_config: 任务配置

        Returns:
            任务ID
        """
        import uuid
        task_id = f"mock_task_{uuid.uuid4().hex[:8]}"
        self.logger.info(f"创建模拟长时任务，ID: {task_id}")
        return task_id