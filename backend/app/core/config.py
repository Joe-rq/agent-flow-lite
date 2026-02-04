"""
Configuration management for the backend application.
Loads environment variables from .env files using python-dotenv.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # DeepSeek API Configuration
    deepseek_api_key: str = Field(
        default="",
        description="DeepSeek API key for LLM calls"
    )
    deepseek_model: str = Field(
        default="deepseek-chat",
        description="Model name for DeepSeek API"
    )
    deepseek_api_base: str = Field(
        default="https://api.deepseek.com",
        description="Base URL for DeepSeek API"
    )

    siliconflow_api_key: str = Field(
        default="",
        description="SiliconFlow API key for embedding models"
    )
    siliconflow_api_base: str = Field(
        default="https://api.siliconflow.cn/v1",
        description="Base URL for SiliconFlow API"
    )
    embedding_model: str = Field(
        default="BAAI/bge-m3",
        description="Embedding model name (SiliconFlow)"
    )

    zep_api_key: str = Field(
        default="",
        description="Zep API key for session memory"
    )
    zep_api_url: str = Field(
        default="https://api.getzep.com",
        description="Base URL for Zep API"
    )
    zep_enabled: bool = Field(
        default=False,
        description="Enable Zep session memory integration"
    )

    # Application Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )

    # Admin Configuration
    admin_email: str = Field(
        default="admin@mail.com",
        description="Email address for admin user (auto-assigned admin role)"
    )
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


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
