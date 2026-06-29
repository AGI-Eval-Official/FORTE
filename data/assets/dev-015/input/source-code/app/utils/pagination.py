"""
分页工具
提供统一的分页参数和响应格式
"""
from typing import TypeVar, Generic, List
from pydantic import BaseModel, Field


T = TypeVar("T")


class PageParams(BaseModel):
    """分页查询参数"""
    page: int = Field(default=1, ge=1, description="页码，从 1 开始")
    page_size: int = Field(default=20, ge=1, le=100, description="每页条数，最大 100")

    @property
    def offset(self) -> int:
        """计算 SQL OFFSET"""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """计算 SQL LIMIT"""
        return self.page_size


class PageResult(BaseModel, Generic[T]):
    """分页查询结果"""
    total: int = Field(description="总条数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页条数")
    items: List[T] = Field(description="数据列表")

    @classmethod
    def create(cls, items: List[T], total: int, page: int, page_size: int) -> "PageResult[T]":
        """创建分页结果"""
        return cls(total=total, page=page, page_size=page_size, items=items)
