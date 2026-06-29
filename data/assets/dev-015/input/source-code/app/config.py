"""
配置管理模块
从环境变量读取配置，提供全局配置对象
"""
import os
import base64
import secrets
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # 应用基础配置
    app_name: str = "评测平台"
    app_version: str = "1.0.0"
    debug: bool = False

    # 数据库配置
    database_url: str = "sqlite+aiosqlite:///./eval_platform.db"

    # 加密密钥（base64 编码的 32 字节随机值）
    # 若未设置，自动生成一个（仅用于开发环境，生产环境应通过环境变量注入）
    encryption_key: str = ""

    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000

    # 文件上传限制（50MB）
    max_upload_size: int = 50 * 1024 * 1024

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def get_encryption_key_bytes(self) -> bytes:
        """获取 32 字节加密密钥"""
        if self.encryption_key:
            return base64.b64decode(self.encryption_key)
        # 开发环境：使用固定密钥（生产环境必须通过环境变量设置）
        fixed_key = b"eval-platform-dev-key-32bytes!!!"
        return fixed_key[:32]


# 全局配置实例
settings = Settings()
