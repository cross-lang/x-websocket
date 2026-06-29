"""
可扩展LLM接口
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, List, Optional, Any
from enum import Enum


logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """LLM提供商枚举"""
    OPENAI = "openai"
    KIMI = "kimi"
    DEEPSEEK = "deepseek"
    MOCK = "mock"
    LOCAL = "local"


class LLMConfig:
    """LLM配置"""

    def __init__(
        self,
        provider: LLMProvider,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ):
        self.provider = provider
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.kwargs = kwargs


class BaseLLM(ABC):
    """LLM基础抽象类"""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        流式生成文本

        Args:
            prompt: 提示词
            **kwargs: 额外参数

        Yields:
            生成的文本块
        """
        pass

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        聊天接口

        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}, ...]
            **kwargs: 额外参数

        Returns:
            包含响应和元数据的字典
        """
        pass

    @abstractmethod
    async def get_status(self, task_id: str) -> Dict[str, Any]:
        """
        获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态信息
        """
        pass

    async def generate(self, prompt: str, **kwargs) -> str:
        """
        生成完整文本（非流式）

        Args:
            prompt: 提示词
            **kwargs: 额外参数

        Returns:
            生成的完整文本
        """
        full_text = ""
        async for chunk in self.generate_stream(prompt, **kwargs):
            full_text += chunk
        return full_text

    def validate_config(self) -> bool:
        """
        验证配置是否有效

        Returns:
            配置是否有效
        """
        if not self.config.api_key and self.config.provider != LLMProvider.MOCK:
            self.logger.warning(f"{self.config.provider} 缺少API密钥")
            return False
        return True


class LLMFactory:
    """LLM工厂类"""

    @staticmethod
    def create_llm(config: LLMConfig) -> BaseLLM:
        """
        创建LLM实例

        Args:
            config: LLM配置

        Returns:
            LLM实例

        Raises:
            ValueError: 不支持的提供商
        """
        provider = config.provider

        if provider == LLMProvider.OPENAI:
            from .openai import OpenAIClient
            return OpenAIClient(config)
        elif provider == LLMProvider.KIMI:
            from .kimi import KimiClient
            return KimiClient(config)
        elif provider == LLMProvider.DEEPSEEK:
            from .deepseek import DeepSeekClient
            return DeepSeekClient(config)
        elif provider == LLMProvider.MOCK:
            from .mock import MockLLM
            return MockLLM(config)
        elif provider == LLMProvider.LOCAL:
            from .local import LocalLLM
            return LocalLLM(config)
        else:
            raise ValueError(f"不支持的LLM提供商: {provider}")

    @staticmethod
    def create_from_settings(settings) -> BaseLLM:
        """
        从设置创建LLM实例

        Args:
            settings: 应用设置

        Returns:
            LLM实例
        """
        provider_name = settings.llm_provider.lower()
        provider_map = {
            "openai": LLMProvider.OPENAI,
            "kimi": LLMProvider.KIMI,
            "deepseek": LLMProvider.DEEPSEEK,
            "mock": LLMProvider.MOCK,
            "local": LLMProvider.LOCAL,
        }

        if provider_name not in provider_map:
            logger.warning(f"未知的LLM提供商: {provider_name}，使用mock")
            provider_name = "mock"

        provider = provider_map[provider_name]

        # 根据提供商获取配置
        if provider == LLMProvider.OPENAI:
            config = LLMConfig(
                provider=provider,
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
                model=settings.openai_model,
            )
        elif provider == LLMProvider.KIMI:
            config = LLMConfig(
                provider=provider,
                api_key=settings.kimi_api_key,
                base_url=settings.kimi_base_url,
                model=settings.kimi_model,
            )
        elif provider == LLMProvider.DEEPSEEK:
            config = LLMConfig(
                provider=provider,
                api_key=settings.deepseek_api_key,
                base_url=settings.deepseek_base_url,
                model=settings.deepseek_model,
            )
        elif provider == LLMProvider.LOCAL:
            config = LLMConfig(
                provider=provider,
                api_key=None,
                base_url=None,
                model=settings.local_model_name,
            )
        else:  # MOCK
            config = LLMConfig(
                provider=provider,
                api_key=None,
                base_url=None,
                model="mock",
            )

        return LLMFactory.create_llm(config)