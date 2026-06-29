"""
评测实验相关 Pydantic Schema
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ExperimentCreate(BaseModel):
    """发起评测实验请求体"""
    name: str = Field(..., max_length=100, description="实验名称")
    model_id: int = Field(..., description="关联模型 ID")
    dataset_id: int = Field(..., description="关联评测集 ID")
    description: Optional[str] = Field(None, max_length=500, description="描述")
    concurrency: int = Field(default=5, ge=1, le=20, description="并发数，默认 5，范围 1-20")
    timeout_seconds: int = Field(default=30, ge=5, le=300, description="单条超时秒数，默认 30，范围 5-300")


class ExperimentResponse(BaseModel):
    """评测实验响应体"""
    id: int
    name: str
    model_id: int
    model_name: Optional[str] = None
    model_deleted: bool = False
    dataset_id: int
    dataset_name: Optional[str] = None
    dataset_deleted: bool = False
    description: Optional[str]
    concurrency: int
    timeout_seconds: int
    status: str
    created_by: str
    created_at: datetime
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class ExperimentStatistics(BaseModel):
    """评测实验统计指标"""
    total_count: Optional[int] = None
    success_count: Optional[int] = None
    failed_count: Optional[int] = None
    avg_response_ms: Optional[int] = None
    p50_ms: Optional[int] = None
    p90_ms: Optional[int] = None
    p99_ms: Optional[int] = None
    note: str = "响应时间统计仅包含成功条目"


class ExperimentResultItemResponse(BaseModel):
    """逐条评测结果响应体"""
    id: int
    seq: int
    input_text: str
    expected_output: Optional[str]
    actual_output: Optional[str]
    response_time_ms: Optional[int]
    status: str
    error_message: Optional[str]

    model_config = {"from_attributes": True}


class ExperimentDetailResponse(BaseModel):
    """评测实验详情响应体（含统计和逐条结果）"""
    id: int
    name: str
    model_id: int
    model_name: Optional[str]
    model_deleted: bool
    dataset_id: int
    dataset_name: Optional[str]
    dataset_deleted: bool
    description: Optional[str]
    concurrency: int
    timeout_seconds: int
    status: str
    created_by: str
    created_at: datetime
    completed_at: Optional[datetime]
    statistics: ExperimentStatistics
    results: dict  # 分页结果
