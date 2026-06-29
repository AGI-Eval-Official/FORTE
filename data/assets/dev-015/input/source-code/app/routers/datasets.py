"""
评测集管理 API 路由
"""
from typing import Optional
from fastapi import APIRouter, Depends, Header, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.dataset import DatasetCreate, DatasetUpdate
from app.services import dataset_service
from app.utils.response import ApiResponse, AppException, ErrorCode

router = APIRouter(prefix="/api/v1/datasets", tags=["评测集管理"])

DEFAULT_USER = "anonymous"


def get_operator(x_user_id: Optional[str] = Header(default=None)) -> str:
    return x_user_id or DEFAULT_USER


@router.get("", summary="获取评测集列表")
async def list_datasets(
    name: Optional[str] = Query(None, description="按名称搜索"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    items, total = await dataset_service.list_datasets(db=db, name=name, page=page, page_size=page_size)
    return ApiResponse.success(data={
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [item.model_dump() for item in items],
    })


@router.post("", summary="创建评测集")
async def create_dataset(
    data: DatasetCreate,
    operator: str = Depends(get_operator),
    db: AsyncSession = Depends(get_db),
):
    dataset = await dataset_service.create_dataset(db=db, data=data, operator=operator)
    return ApiResponse.success(data=dataset.model_dump())


@router.get("/{dataset_id}", summary="获取评测集详情")
async def get_dataset(
    dataset_id: int,
    db: AsyncSession = Depends(get_db),
):
    detail = await dataset_service.get_dataset_with_experiments(db=db, dataset_id=dataset_id)
    return ApiResponse.success(data=detail)


@router.put("/{dataset_id}", summary="编辑评测集")
async def update_dataset(
    dataset_id: int,
    data: DatasetUpdate,
    operator: str = Depends(get_operator),
    db: AsyncSession = Depends(get_db),
):
    dataset = await dataset_service.update_dataset(db=db, dataset_id=dataset_id, data=data, operator=operator)
    return ApiResponse.success(data=dataset.model_dump())


@router.delete("/{dataset_id}", summary="删除评测集")
async def delete_dataset(
    dataset_id: int,
    operator: str = Depends(get_operator),
    db: AsyncSession = Depends(get_db),
):
    await dataset_service.delete_dataset(db=db, dataset_id=dataset_id, operator=operator)
    return ApiResponse.success(data={"id": dataset_id})


@router.post("/{dataset_id}/items/import", summary="导入评测集数据")
async def import_items(
    dataset_id: int,
    file: UploadFile = File(..., description="JSON 文件，最大 50MB"),
    mode: str = Form(..., description="导入模式：append（追加）/ overwrite（清空重新导入）"),
    operator: str = Depends(get_operator),
    db: AsyncSession = Depends(get_db),
):
    """导入评测集数据，支持追加和覆盖模式"""
    if mode not in ("append", "overwrite"):
        raise AppException(ErrorCode.PARAM_INVALID, "mode 必须为 append 或 overwrite")

    file_content = await file.read()
    result = await dataset_service.import_dataset_items(
        db=db,
        dataset_id=dataset_id,
        file_content=file_content,
        mode=mode,
        operator=operator,
    )
    return ApiResponse.success(data=result)


@router.get("/{dataset_id}/items", summary="分页查询评测集数据条目")
async def list_dataset_items(
    dataset_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    items, total = await dataset_service.get_dataset_items(
        db=db, dataset_id=dataset_id, page=page, page_size=page_size
    )
    return ApiResponse.success(data={
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [item.model_dump() for item in items],
    })
