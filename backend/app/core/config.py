"""
Configuration management for the backend application.
Loads environment variables from .env files using python-dotenv.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    default_llm_provider: str = Field(
        default="deepseek",
        description="Default LLM provider: deepseek/openai/qwen",
    )
    default_llm_model: str = Field(
        default="",
        description="Optional default model override in provider:model format",
    )

    # DeepSeek API Configuration
    deepseek_api_key: str = Field(
        default="", description="DeepSeek API key for LLM calls"
    )
    deepseek_model: str = Field(
        default="deepseek-chat", description="Model name for DeepSeek API"
    )
    deepseek_api_base: str = Field(
        default="https://api.deepseek.com", description="Base URL for DeepSeek API"
    )
    deepseek_context_window: int = Field(
        default=64000,
        description="Estimated DeepSeek context window tokens",
        ge=1024,
    )

    openai_api_key: str = Field(
        default="",
        description="OpenAI API key for LLM calls",
    )
    openai_api_base: str = Field(
        default="https://api.openai.com/v1",
        description="Base URL for OpenAI-compatible API",
    )
    openai_model: str = Field(
        default="gpt-4o-mini",
        description="Default OpenAI model",
    )
    openai_context_window: int = Field(
        default=128000,
        description="Estimated OpenAI context window tokens",
        ge=1024,
    )

    qwen_api_key: str = Field(
        default="",
        description="Qwen API key for LLM calls",
    )
    qwen_api_base: str = Field(
        default="https://dashscope.aliyuncs.com/compatible-mode/v1",
        description="Base URL for Qwen OpenAI-compatible API",
    )
    qwen_model: str = Field(
        default="qwen-plus",
        description="Default Qwen model",
    )
    qwen_context_window: int = Field(
        default=32000,
        description="Estimated Qwen context window tokens",
        ge=1024,
    )

    llm_context_ratio: float = Field(
        default=0.7,
        description="Max ratio of context window used by chat history",
        ge=0.1,
        le=0.95,
    )
    llm_history_min_messages: int = Field(
        default=2,
        description="Minimum history messages retained in prompt",
        ge=0,
    )
    llm_history_token_floor: int = Field(
        default=256,
        description="Minimum token budget reserved for history",
        ge=1,
    )
    llm_default_context_window: int = Field(
        default=32768,
        description="Fallback context window when model window is unknown",
        ge=1024,
    )

    siliconflow_api_key: str = Field(
        default="", description="SiliconFlow API key for embedding models"
    )
    siliconflow_api_base: str = Field(
        default="https://api.siliconflow.cn/v1",
        description="Base URL for SiliconFlow API",
    )
    embedding_model: str = Field(
        default="BAAI/bge-m3", description="Embedding model name (SiliconFlow)"
    )

    # Application Configuration
    log_level: str = Field(default="INFO", description="Logging level")

    # Admin Configuration
    admin_email: str = Field(
        default="",
        description="Email address for admin user (auto-assigned admin role). Leave empty to disable auto-admin.",
    )

    auth_lock_max_attempts: int = Field(
        default=5,
        description="Maximum failed login attempts before temporary lock",
        ge=1,
    )
    auth_lock_window_minutes: int = Field(
        default=15,
        description="Temporary lock duration after max failed login attempts",
        ge=1,
    )

    enable_code_node: bool = Field(
        default=False,
        description="Feature flag default for code node",
    )
    enable_http_node: bool = Field(
        default=False,
        description="Feature flag default for HTTP node",
    )
    enable_openai_api: bool = Field(
        default=False,
        description="Feature flag default for OpenAI-compatible publish API",
    )
    enable_public_embed: bool = Field(
        default=False,
        description="Feature flag default for public embed pages",
    )
    http_node_allow_domains: str = Field(
        default="",
        description="Comma-separated allowlist domains for HTTP node",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


def get_settings() -> Settings:
    """
    Load and return application settings.

    This function loads environment variables from .env files
    in the following order (later files override earlier ones):
    1. Project root .env file
    2. Backend .env file

    Returns:
        Settings: Configured application settings
    """
    # Load .env files in order of specificity
    project_root = Path(__file__).parent.parent.parent
    backend_dir = Path(__file__).parent.parent

    # Load project root .env first, then backend .env
    load_dotenv(project_root / ".env", override=False)
    load_dotenv(backend_dir / ".env", override=True)

    return Settings()


# Global settings instance (lazy loaded)
_settings: Settings | None = None


def settings() -> Settings:
    """
    Get the global settings instance.

    Returns:
        Settings: The configured settings object
    """
    global _settings
    if _settings is None:
        _settings = get_settings()
    return _settings
