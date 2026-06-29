"""
AES-256-GCM 加解密工具
用于 API Key 的加密存储和脱敏显示
"""
from __future__ import annotations
import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class ApiKeyCrypto:
    """API Key 加解密工具类"""

    def __init__(self, secret_key: bytes):
        """
        初始化加密工具

        Args:
            secret_key: 32 字节的加密密钥
        """
        if len(secret_key) != 32:
            raise ValueError("加密密钥必须为 32 字节")
        self.aesgcm = AESGCM(secret_key)

    def encrypt(self, plaintext: str) -> str:
        """
        加密 API Key

        Args:
            plaintext: 明文 API Key

        Returns:
            base64 编码的密文（格式：base64(nonce[12字节] + ciphertext)）
        """
        nonce = os.urandom(12)  # GCM 推荐 96-bit nonce
        ciphertext = self.aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        # 存储格式：base64(nonce + ciphertext)
        return base64.b64encode(nonce + ciphertext).decode("utf-8")

    def decrypt(self, encrypted: str) -> str:
        """
        解密 API Key

        Args:
            encrypted: base64 编码的密文

        Returns:
            明文 API Key
        """
        data = base64.b64decode(encrypted)
        nonce, ciphertext = data[:12], data[12:]
        return self.aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")

    @staticmethod
    def mask(plaintext: str) -> str:
        """
        脱敏处理：保留后 4 位，其余替换为 *

        Args:
            plaintext: 明文 API Key

        Returns:
            脱敏后的字符串
        """
        if not plaintext:
            return ""
        if len(plaintext) <= 4:
            return "****"
        return "*" * (len(plaintext) - 4) + plaintext[-4:]


# 全局加密工具实例（延迟初始化）
_crypto_instance: ApiKeyCrypto | None = None


def get_crypto() -> ApiKeyCrypto:
    """获取全局加密工具实例"""
    global _crypto_instance
    if _crypto_instance is None:
        from app.config import settings
        _crypto_instance = ApiKeyCrypto(settings.get_encryption_key_bytes())
    return _crypto_instance
