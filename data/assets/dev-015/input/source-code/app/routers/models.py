"""
模型管理 API 路由
"""
from typing import Optional
from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.model import ModelCreate, ModelUpdate
from app.services import model_service
from app.utils.response import ApiResponse

router = APIRouter(prefix="/api/v1/models", tags=["模型管理"])

DEFAULT_USER = "anonymous"


def get_operator(x_user_id: Optional[str] = Header(default=None)) -> str:
    """从请求头获取操作人 ID"""
    return x_user_id or DEFAULT_USER


@router.get("", summary="获取模型列表")
async def list_models(
    name: Optional[str] = Query(None, description="按名称搜索"),
    model_type: Optional[str] = Query(None, description="按模型类型筛选"),
    status: Optional[str] = Query(None, description="按状态筛选"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页条数"),
    db: AsyncSession = Depends(get_db),
):
    """获取模型列表，支持搜索、筛选、分页"""
    items, total = await model_service.list_models(
        db=db,
        name=name,
        model_type=model_type,
        status=status,
        page=page,
        page_size=page_size,
    )
    return ApiResponse.success(data={
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [item.model_dump() for item in items],
    })


@router.post("", summary="创建模型")
async def create_model(
    data: ModelCreate,
    operator: str = Depends(get_operator),
    db: AsyncSession = Depends(get_db),
):
    """创建新模型"""
    model = await model_service.create_model(db=db, data=data, operator=operator)
    return ApiResponse.success(data=model.model_dump())


@router.get("/{model_id}", summary="获取模型详情")
async def get_model(
    model_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取模型详情（含关联实验历史最近 10 条）"""
    detail = await model_service.get_model_with_experiments(db=db, model_id=model_id)
    return ApiResponse.success(data=detail)


@router.put("/{model_id}", summary="编辑模型")
async def update_model(
    model_id: int,
    data: ModelUpdate,
    operator: str = Depends(get_operator),
    db: AsyncSession = Depends(get_db),
):
    """编辑模型（名称不可修改）"""
    model = await model_service.update_model(db=db, model_id=model_id, data=data, operator=operator)
    return ApiResponse.success(data=model.model_dump())


@router.delete("/{model_id}", summary="删除模型")
async def delete_model(
    model_id: int,
    operator: str = Depends(get_operator),
    db: AsyncSession = Depends(get_db),
):
    """软删除模型（有进行中实验时拒绝）"""
    await model_service.delete_model(db=db, model_id=model_id, operator=operator)
    return ApiResponse.success(data={"id": model_id})
