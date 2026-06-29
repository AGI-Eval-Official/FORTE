"""
统一响应格式工具
"""
from typing import Any, Optional
from pydantic import BaseModel
from fastapi import HTTPException


class ApiResponse(BaseModel):
    """统一 API 响应格式"""
    code: int = 0
    message: str = "success"
    data: Any = None

    @classmethod
    def success(cls, data: Any = None, message: str = "success") -> "ApiResponse":
        """成功响应"""
        return cls(code=0, message=message, data=data)

    @classmethod
    def error(cls, code: int, message: str) -> "ApiResponse":
        """错误响应"""
        return cls(code=code, message=message, data=None)


class AppException(Exception):
    """应用业务异常"""

    def __init__(self, code: int, message: str, http_status: int = 400):
        self.code = code
        self.message = message
        self.http_status = http_status
        super().__init__(message)


# 错误码常量
class ErrorCode:
    PARAM_INVALID = 40001       # 参数校验失败
    NAME_EXISTS = 40002         # 资源名称已存在
    NOT_FOUND = 40003           # 资源不存在
    OPERATION_NOT_ALLOWED = 40004  # 操作不允许
    FILE_FORMAT_ERROR = 40005   # 文件格式错误
    FILE_TOO_LARGE = 40006      # 文件大小超限
    NO_PERMISSION = 40301       # 无操作权限
    INTERNAL_ERROR = 50001      # 服务器内部错误
