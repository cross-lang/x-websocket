"""
OpenAI兼容客户端
"""
import asyncio
import logging
from typing import AsyncGenerator, Dict, List, Any, Optional
from openai import AsyncOpenAI, APIError
from .base import BaseLLM, LLMConfig


logger = logging.getLogger(__name__)


class OpenAIClient(BaseLLM):
    """OpenAI兼容客户端"""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """初始化OpenAI客户端"""
        api_key = self.config.api_key
        base_url = self.config.base_url

        if not api_key:
            self.logger.warning("OpenAI API密钥未设置，使用模拟模式")
            # 如果没有API密钥，可以回退到模拟模式
            # 在实际使用中，应该抛出错误或使用备用方案
            return

        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=30.0,
            max_retries=3
        )
        self.logger.info(f"初始化OpenAI客户端，base_url: {base_url}")

    async def generate_stream(
        self,
        prompt: str,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        使用OpenAI API流式生成文本

        Args:
            prompt: 提示词
            **kwargs: 额外参数

        Yields:
            生成的文本块

        Raises:
            ValueError: 客户端未初始化或API调用失败
        """
        if not self.client:
            self.logger.error("OpenAI客户端未初始化，回退到模拟模式")
            # 回退到模拟响应
            mock_response = f"OpenAI客户端未初始化。提示词: {prompt[:50]}..."
            for word in mock_response.split():
                await asyncio.sleep(0.1)
                yield word + " "
            return

        model = kwargs.get("model", self.config.model)
        temperature = kwargs.get("temperature", self.config.temperature)
        max_tokens = kwargs.get("max_tokens", self.config.max_tokens)

        self.logger.info(f"OpenAI流式生成，模型: {model}, 提示词长度: {len(prompt)}")

        try:
            stream = await self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                stream=True,
                temperature=temperature,
                max_tokens=max_tokens,
                **{k: v for k, v in kwargs.items() if k not in ["model", "temperature", "max_tokens"]}
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    yield content

        except APIError as e:
            self.logger.error(f"OpenAI API错误: {e}")
            yield f"[API错误: {str(e)}]"
        except Exception as e:
            self.logger.error(f"OpenAI流式生成错误: {e}")
            yield f"[错误: {str(e)}]"

    async def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        使用OpenAI API进行聊天

        Args:
            messages: 消息列表
            **kwargs: 额外参数

        Returns:
            聊天响应

        Raises:
            ValueError: 客户端未初始化或API调用失败
        """
        if not self.client:
            self.logger.error("OpenAI客户端未初始化，回退到模拟模式")
            return {
                "content": "OpenAI客户端未初始化。请检查API密钥配置。",
                "role": "assistant",
                "tokens": 0,
                "finish_reason": "stop"
            }

        model = kwargs.get("model", self.config.model)
        temperature = kwargs.get("temperature", self.config.temperature)
        max_tokens = kwargs.get("max_tokens", self.config.max_tokens)

        self.logger.info(f"OpenAI聊天，模型: {model}, 消息数: {len(messages)}")

        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                stream=False,
                temperature=temperature,
                max_tokens=max_tokens,
                **{k: v for k, v in kwargs.items() if k not in ["model", "temperature", "max_tokens"]}
            )

            if response.choices and response.choices[0].message:
                message = response.choices[0].message
                return {
                    "content": message.content,
                    "role": message.role,
                    "tokens": response.usage.total_tokens if response.usage else 0,
                    "finish_reason": response.choices[0].finish_reason,
                    "model": response.model,
                    "created_at": asyncio.get_event_loop().time()
                }
            else:
                raise ValueError("OpenAI响应格式无效")

        except APIError as e:
            self.logger.error(f"OpenAI API错误: {e}")
            return {
                "content": f"API错误: {str(e)}",
                "role": "assistant",
                "tokens": 0,
                "finish_reason": "error"
            }
        except Exception as e:
            self.logger.error(f"OpenAI聊天错误: {e}")
            return {
                "content": f"错误: {str(e)}",
                "role": "assistant",
                "tokens": 0,
                "finish_reason": "error"
            }

    async def get_status(self, task_id: str) -> Dict[str, Any]:
        """
        获取任务状态（OpenAI通常不支持此功能）

        Args:
            task_id: 任务ID

        Returns:
            任务状态信息
        """
        self.logger.info(f"OpenAI状态查询，任务ID: {task_id}")

        # OpenAI API通常不提供任务状态查询
        # 这里返回一个模拟状态
        return {
            "task_id": task_id,
            "status": "completed",
            "message": "OpenAI API任务通常是即时完成的",
            "progress": 100,
            "result": {"note": "OpenAI API不提供任务状态跟踪"}
        }

    def validate_config(self) -> bool:
        """
        验证OpenAI配置

        Returns:
            配置是否有效
        """
        if not self.config.api_key:
            self.logger.warning("OpenAI API密钥未设置")
            return False
        return True