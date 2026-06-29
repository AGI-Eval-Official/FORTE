"""
评测实验 API 路由
"""
import json
from typing import Optional
from fastapi import APIRouter, Depends, Header, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.experiment import ExperimentCreate
from app.services import experiment_service
from app.utils.response import ApiResponse

router = APIRouter(prefix="/api/v1/experiments", tags=["评测实验"])

DEFAULT_USER = "anonymous"


def get_operator(x_user_id: Optional[str] = Header(default=None)) -> str:
    return x_user_id or DEFAULT_USER


@router.get("", summary="获取评测实验列表")
async def list_experiments(
    name: Optional[str] = Query(None, description="按名称搜索"),
    status: Optional[str] = Query(None, description="按状态筛选"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    items, total = await experiment_service.list_experiments(
        db=db, name=name, status=status, page=page, page_size=page_size
    )
    return ApiResponse.success(data={
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    })


@router.post("", summary="发起评测实验")
async def create_experiment(
    data: ExperimentCreate,
    operator: str = Depends(get_operator),
    db: AsyncSession = Depends(get_db),
):
    experiment = await experiment_service.create_experiment(db=db, data=data, operator=operator)
    return ApiResponse.success(data=experiment.model_dump())


@router.get("/{experiment_id}", summary="获取评测实验详情")
async def get_experiment_detail(
    experiment_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    result_status: Optional[str] = Query(None, description="筛选结果状态：SUCCESS/FAILED"),
    db: AsyncSession = Depends(get_db),
):
    detail = await experiment_service.get_experiment_detail(
        db=db,
        experiment_id=experiment_id,
        page=page,
        page_size=page_size,
        result_status=result_status,
    )
    return ApiResponse.success(data=detail)


@router.post("/{experiment_id}/cancel", summary="取消评测实验")
async def cancel_experiment(
    experiment_id: int,
    operator: str = Depends(get_operator),
    db: AsyncSession = Depends(get_db),
):
    result = await experiment_service.cancel_experiment(
        db=db, experiment_id=experiment_id, operator=operator
    )
    return ApiResponse.success(data=result)


@router.get("/{experiment_id}/results", summary="分页查询逐条评测结果")
async def list_results(
    experiment_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    result_status: Optional[str] = Query(None, description="筛选状态：SUCCESS/FAILED"),
    db: AsyncSession = Depends(get_db),
):
    items, total = await experiment_service.get_experiment_results(
        db=db,
        experiment_id=experiment_id,
        page=page,
        page_size=page_size,
        result_status=result_status,
    )
    return ApiResponse.success(data={
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    })


@router.get("/{experiment_id}/results/export", summary="导出评测结果为 JSON 文件")
async def export_results(
    experiment_id: int,
    db: AsyncSession = Depends(get_db),
):
    """流式导出评测结果为 JSON 文件"""
    results = await experiment_service.export_experiment_results(db=db, experiment_id=experiment_id)

    def generate():
        yield json.dumps(results, ensure_ascii=False, indent=2).encode("utf-8")

    return StreamingResponse(
        generate(),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=experiment_{experiment_id}_results.json"
        },
    )
