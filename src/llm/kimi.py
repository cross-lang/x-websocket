"""
Kimi模型集成
"""
import logging
from typing import AsyncGenerator, Dict, List, Any
from .openai import OpenAIClient
from .base import LLMConfig


logger = logging.getLogger(__name__)


class KimiClient(OpenAIClient):
    """Kimi AI客户端（基于OpenAI兼容API）"""

    def __init__(self, config: LLMConfig):
        # 确保使用正确的默认值
        if not config.base_url:
            config.base_url = "https://api.moonshot.cn/v1"
        if not config.model:
            config.model = "moonshot-v1-8k"

        super().__init__(config)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info(f"初始化Kimi客户端，base_url: {config.base_url}, model: {config.model}")

    async def generate_stream(
        self,
        prompt: str,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Kimi流式生成

        Args:
            prompt: 提示词
            **kwargs: 额外参数

        Yields:
            生成的文本块
        """
        self.logger.info(f"Kimi流式生成，提示词长度: {len(prompt)}")

        # 调用父类的OpenAI兼容实现
        async for chunk in super().generate_stream(prompt, **kwargs):
            yield chunk

    async def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Kimi聊天接口

        Args:
            messages: 消息列表
            **kwargs: 额外参数

        Returns:
            聊天响应
        """
        self.logger.info(f"Kimi聊天，消息数: {len(messages)}")

        # 调用父类的OpenAI兼容实现
        return await super().chat(messages, **kwargs)

    async def get_status(self, task_id: str) -> Dict[str, Any]:
        """
        获取Kimi任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态信息
        """
        self.logger.info(f"Kimi状态查询，任务ID: {task_id}")

        # Kimi API可能不提供任务状态查询
        # 返回一个基本状态
        return {
            "task_id": task_id,
            "status": "completed",
            "message": "Kimi API任务通常是即时完成的",
            "progress": 100,
            "model": self.config.model,
            "provider": "kimi"
        }

    def validate_config(self) -> bool:
        """
        验证Kimi配置

        Returns:
            配置是否有效
        """
        if not self.config.api_key:
            self.logger.warning("Kimi API密钥未设置")
            return False

        # 检查API密钥格式（Kimi密钥通常以'sk-'开头）
        if not self.config.api_key.startswith("sk-"):
            self.logger.warning("Kimi API密钥格式可能不正确，应以'sk-'开头")

        return True