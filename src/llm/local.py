"""
本地模型集成（占位符）
"""
import asyncio
import logging
from typing import AsyncGenerator, Dict, List, Any
from .base import BaseLLM, LLMConfig
from .mock import MockLLM  # 暂时使用模拟实现


logger = logging.getLogger(__name__)


class LocalLLM(BaseLLM):
    """本地模型客户端（占位符，当前使用模拟实现）"""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info(f"初始化本地模型客户端，模型: {config.model}")

        # 暂时使用MockLLM作为实现
        self.mock_llm = MockLLM(config)

    async def generate_stream(
        self,
        prompt: str,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        本地模型流式生成（占位符）

        Args:
            prompt: 提示词
            **kwargs: 额外参数

        Yields:
            生成的文本块
        """
        self.logger.info(f"本地模型流式生成（占位符），提示词长度: {len(prompt)}")

        # 暂时使用模拟实现
        async for chunk in self.mock_llm.generate_stream(prompt, **kwargs):
            yield chunk

    async def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        本地模型聊天接口（占位符）

        Args:
            messages: 消息列表
            **kwargs: 额外参数

        Returns:
            聊天响应
        """
        self.logger.info(f"本地模型聊天（占位符），消息数: {len(messages)}")

        # 暂时使用模拟实现
        return await self.mock_llm.chat(messages, **kwargs)

    async def get_status(self, task_id: str) -> Dict[str, Any]:
        """
        获取本地模型任务状态（占位符）

        Args:
            task_id: 任务ID

        Returns:
            任务状态信息
        """
        self.logger.info(f"本地模型状态查询（占位符），任务ID: {task_id}")

        # 暂时使用模拟实现
        return await self.mock_llm.get_status(task_id)

    def validate_config(self) -> bool:
        """
        验证本地模型配置

        Returns:
            配置是否有效
        """
        if not self.config.model:
            self.logger.warning("本地模型名称未设置")
            return False

        self.logger.info(f"本地模型配置验证通过，模型: {self.config.model}")
        return True