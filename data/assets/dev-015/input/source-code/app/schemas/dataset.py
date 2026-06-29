"""
评测集管理相关 Pydantic Schema
"""
import re
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


VERSION_PATTERN = re.compile(r"^v\d+\.\d+\.\d+$")


class DatasetCreate(BaseModel):
    """创建评测集请求体"""
    name: str = Field(..., max_length=100, description="评测集名称，全局唯一")
    version: Optional[str] = Field(None, max_length=20, description="版本号，格式 vX.Y.Z")
    description: Optional[str] = Field(None, max_length=500, description="描述")

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not VERSION_PATTERN.match(v):
            raise ValueError("version 格式错误，应为 vX.Y.Z（如 v1.0.0）")
        return v


class DatasetUpdate(BaseModel):
    """编辑评测集请求体"""
    name: Optional[str] = Field(None, max_length=100, description="评测集名称")
    version: Optional[str] = Field(None, max_length=20, description="版本号")
    description: Optional[str] = Field(None, max_length=500, description="描述")

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not VERSION_PATTERN.match(v):
            raise ValueError("version 格式错误，应为 vX.Y.Z（如 v1.0.0）")
        return v


class DatasetResponse(BaseModel):
    """评测集响应体"""
    id: int
    name: str
    version: Optional[str]
    description: Optional[str]
    item_count: int
    created_by: str
    updated_by: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DatasetItemResponse(BaseModel):
    """评测集数据条目响应体"""
    id: int
    seq: int
    input_text: str
    expected_output: Optional[str]

    model_config = {"from_attributes": True}
