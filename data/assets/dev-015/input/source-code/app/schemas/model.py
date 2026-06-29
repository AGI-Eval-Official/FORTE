"""
模型管理相关 Pydantic Schema
"""
import re
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, model_validator


# 版本号格式正则
VERSION_PATTERN = re.compile(r"^v\d+\.\d+\.\d+$")


class ModelCreate(BaseModel):
    """创建模型请求体"""
    name: str = Field(..., max_length=100, description="模型名称，全局唯一")
    model_type: str = Field(..., description="模型类型：LLM/CLASSIFICATION/REGRESSION/OTHER")
    version: Optional[str] = Field(None, max_length=20, description="版本号，格式 vX.Y.Z")
    description: Optional[str] = Field(None, max_length=500, description="描述")
    endpoint_url: Optional[str] = Field(None, description="模型端点 URL")
    api_key: Optional[str] = Field(None, description="API Key（明文，存储时加密）")

    @field_validator("model_type")
    @classmethod
    def validate_model_type(cls, v: str) -> str:
        allowed = {"LLM", "CLASSIFICATION", "REGRESSION", "OTHER"}
        if v not in allowed:
            raise ValueError(f"model_type 必须为 {allowed} 之一")
        return v

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not VERSION_PATTERN.match(v):
            raise ValueError("version 格式错误，应为 vX.Y.Z（如 v1.0.0）")
        return v


class ModelUpdate(BaseModel):
    """编辑模型请求体（名称不可修改）"""
    model_type: Optional[str] = Field(None, description="模型类型")
    version: Optional[str] = Field(None, max_length=20, description="版本号")
    description: Optional[str] = Field(None, max_length=500, description="描述")
    endpoint_url: Optional[str] = Field(None, description="模型端点 URL")
    api_key: Optional[str] = Field(None, description="API Key（明文，存储时加密）")
    status: Optional[str] = Field(None, description="状态：ACTIVE/DISABLED")

    @field_validator("model_type")
    @classmethod
    def validate_model_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed = {"LLM", "CLASSIFICATION", "REGRESSION", "OTHER"}
            if v not in allowed:
                raise ValueError(f"model_type 必须为 {allowed} 之一")
        return v

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not VERSION_PATTERN.match(v):
            raise ValueError("version 格式错误，应为 vX.Y.Z（如 v1.0.0）")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in {"ACTIVE", "DISABLED"}:
            raise ValueError("status 必须为 ACTIVE 或 DISABLED")
        return v


class ModelResponse(BaseModel):
    """模型响应体"""
    id: int
    name: str
    model_type: str
    version: Optional[str]
    description: Optional[str]
    endpoint_url: Optional[str]
    api_key_masked: Optional[str] = Field(None, description="脱敏后的 API Key")
    status: str
    created_by: str
    updated_by: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ModelListQuery(BaseModel):
    """模型列表查询参数"""
    name: Optional[str] = Field(None, description="按名称搜索（模糊匹配）")
    model_type: Optional[str] = Field(None, description="按模型类型筛选")
    status: Optional[str] = Field(None, description="按状态筛选")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页条数")
