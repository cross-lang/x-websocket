"""
配置管理模块
"""
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用设置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # 服务器配置
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8765)
    debug: bool = Field(default=True)

    # 认证配置
    jwt_secret: str = Field(...)
    jwt_algorithm: str = Field(default="HS256")
    token_expire_minutes: int = Field(default=60)

    # 模型提供商配置
    llm_provider: str = Field(default="openai")

    # OpenAI 配置
    openai_api_key: Optional[str] = Field(default=None)
    openai_base_url: Optional[str] = Field(default=None)
    openai_model: Optional[str] = Field(default="gpt-3.5-turbo")

    # Kimi 配置
    kimi_api_key: Optional[str] = Field(default=None)
    kimi_base_url: Optional[str] = Field(default=None)
    kimi_model: Optional[str] = Field(default="moonshot-v1-8k")

    # DeepSeek 配置
    deepseek_api_key: Optional[str] = Field(default=None)
    deepseek_base_url: Optional[str] = Field(default=None)
    deepseek_model: Optional[str] = Field(default="deepseek-chat")

    # 本地模型配置
    local_model_path: Optional[str] = Field(default=None)
    local_model_name: Optional[str] = Field(default=None)

    # 加密配置
    encryption_key: Optional[str] = Field(default=None)

    # 日志配置
    log_level: str = Field(default="INFO")
    log_file: Optional[str] = Field(default=None)


# 全局设置实例
settings = Settings()