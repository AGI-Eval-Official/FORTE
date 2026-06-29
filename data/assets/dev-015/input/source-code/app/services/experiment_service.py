"""
评测实验业务逻辑层
"""
import json
from datetime import datetime, timezone
from typing import Optional, List, Tuple

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.experiment import Experiment, ExperimentStatus
from app.models.experiment_result import ExperimentResult, ResultStatus
from app.models.model import Model, ModelStatus
from app.models.dataset import Dataset
from app.schemas.experiment import ExperimentCreate, ExperimentResponse, ExperimentStatistics
from app.utils.audit import record_audit_log, AuditAction, AuditResourceType
from app.utils.response import AppException, ErrorCode


def _build_experiment_response(
    experiment: Experiment,
    model_name: Optional[str] = None,
    model_deleted: bool = False,
    dataset_name: Optional[str] = None,
    dataset_deleted: bool = False,
) -> ExperimentResponse:
    """将 ORM 对象转换为响应体"""
    return ExperimentResponse(
        id=experiment.id,
        name=experiment.name,
        model_id=experiment.model_id,
        model_name=model_name,
        model_deleted=model_deleted,
        dataset_id=experiment.dataset_id,
        dataset_name=dataset_name,
        dataset_deleted=dataset_deleted,
        description=experiment.description,
        concurrency=experiment.concurrency,
        timeout_seconds=experiment.timeout_seconds,
        status=experiment.status,
        created_by=experiment.created_by,
        created_at=experiment.created_at,
        completed_at=experiment.completed_at,
    )


async def _get_model_info(db: AsyncSession, model_id: int) -> Tuple[Optional[str], bool]:
    """获取模型名称和是否已删除"""
    stmt = select(Model).where(Model.id == model_id)
    model = (await db.execute(stmt)).scalar_one_or_none()
    if model is None:
        return None, True
    return model.name, model.deleted_at is not None


async def _get_dataset_info(db: AsyncSession, dataset_id: int) -> Tuple[Optional[str], bool]:
    """获取评测集名称和是否已删除"""
    stmt = select(Dataset).where(Dataset.id == dataset_id)
    dataset = (await db.execute(stmt)).scalar_one_or_none()
    if dataset is None:
        return None, True
    return dataset.name, dataset.deleted_at is not None


async def list_experiments(
    db: AsyncSession,
    name: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> Tuple[List[dict], int]:
    """获取评测实验列表"""
    conditions = [Experiment.deleted_at.is_(None)]
    if name:
        conditions.append(Experiment.name.ilike(f"%{name}%"))
    if status:
        conditions.append(Experiment.status == status)

    where_clause = and_(*conditions)

    count_stmt = select(func.count()).select_from(Experiment).where(where_clause)
    total = (await db.execute(count_stmt)).scalar_one()

    offset = (page - 1) * page_size
    stmt = (
        select(Experiment)
        .where(where_clause)
        .order_by(Experiment.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    experiments = result.scalars().all()

    items = []
    for exp in experiments:
        model_name, model_deleted = await _get_model_info(db, exp.model_id)
        dataset_name, dataset_deleted = await _get_dataset_info(db, exp.dataset_id)
        resp = _build_experiment_response(exp, model_name, model_deleted, dataset_name, dataset_deleted)
        items.append(resp.model_dump())

    return items, total


async def create_experiment(
    db: AsyncSession,
    data: ExperimentCreate,
    operator: str,
) -> ExperimentResponse:
    """发起评测实验"""
    # 校验模型存在且未删除
    model_stmt = select(Model).where(Model.id == data.model_id, Model.deleted_at.is_(None))
    model = (await db.execute(model_stmt)).scalar_one_or_none()
    if model is None:
        raise AppException(ErrorCode.NOT_FOUND, "模型不存在")
    if model.status == ModelStatus.DISABLED:
        raise AppException(ErrorCode.OPERATION_NOT_ALLOWED, "该模型已禁用，无法发起评测实验")

    # 校验评测集存在且未删除
    dataset_stmt = select(Dataset).where(Dataset.id == data.dataset_id, Dataset.deleted_at.is_(None))
    dataset = (await db.execute(dataset_stmt)).scalar_one_or_none()
    if dataset is None:
        raise AppException(ErrorCode.NOT_FOUND, "评测集不存在")

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    experiment = Experiment(
        name=data.name,
        model_id=data.model_id,
        dataset_id=data.dataset_id,
        description=data.description,
        concurrency=data.concurrency,
        timeout_seconds=data.timeout_seconds,
        status=ExperimentStatus.RUNNING,
        created_by=operator,
        created_at=now,
    )
    db.add(experiment)
    await db.flush()

    await record_audit_log(
        db=db,
        operator=operator,
        action=AuditAction.CREATE,
        resource_type=AuditResourceType.EXPERIMENT,
        resource_id=experiment.id,
        detail={"name": experiment.name, "model_id": data.model_id, "dataset_id": data.dataset_id},
    )

    # 提交事务后再启动后台任务（确保实验记录已写入数据库）
    await db.commit()

    # 启动后台评测任务
    from app.engine.evaluation_engine import evaluation_engine
    await evaluation_engine.start(experiment.id)

    return _build_experiment_response(experiment, model.name, False, dataset.name, False)


async def get_experiment(db: AsyncSession, experiment_id: int) -> Experiment:
    """获取实验（未删除），不存在则抛出异常"""
    stmt = select(Experiment).where(
        Experiment.id == experiment_id,
        Experiment.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    experiment = result.scalar_one_or_none()
    if experiment is None:
        raise AppException(ErrorCode.NOT_FOUND, "评测实验不存在")
    return experiment


async def get_experiment_detail(
    db: AsyncSession,
    experiment_id: int,
    page: int = 1,
    page_size: int = 50,
    result_status: Optional[str] = None,
) -> dict:
    """获取评测实验详情（含统计和逐条结果）"""
    experiment = await get_experiment(db, experiment_id)

    model_name, model_deleted = await _get_model_info(db, experiment.model_id)
    dataset_name, dataset_deleted = await _get_dataset_info(db, experiment.dataset_id)

    # 构建统计信息
    statistics = ExperimentStatistics(
        total_count=experiment.total_count,
        success_count=experiment.success_count,
        failed_count=experiment.failed_count,
        avg_response_ms=experiment.avg_response_ms,
        p50_ms=experiment.p50_ms,
        p90_ms=experiment.p90_ms,
        p99_ms=experiment.p99_ms,
    )

    # 查询逐条结果
    result_conditions = [ExperimentResult.experiment_id == experiment_id]
    if result_status:
        result_conditions.append(ExperimentResult.status == result_status)

    result_where = and_(*result_conditions)

    count_stmt = select(func.count()).select_from(ExperimentResult).where(result_where)
    result_total = (await db.execute(count_stmt)).scalar_one()

    offset = (page - 1) * page_size
    results_stmt = (
        select(ExperimentResult)
        .where(result_where)
        .order_by(ExperimentResult.seq)
        .offset(offset)
        .limit(page_size)
    )
    results_data = (await db.execute(results_stmt)).scalars().all()

    return {
        "id": experiment.id,
        "name": experiment.name,
        "model_id": experiment.model_id,
        "model_name": model_name,
        "model_deleted": model_deleted,
        "dataset_id": experiment.dataset_id,
        "dataset_name": dataset_name,
        "dataset_deleted": dataset_deleted,
        "description": experiment.description,
        "concurrency": experiment.concurrency,
        "timeout_seconds": experiment.timeout_seconds,
        "status": experiment.status,
        "created_by": experiment.created_by,
        "created_at": experiment.created_at.isoformat() if experiment.created_at else None,
        "completed_at": experiment.completed_at.isoformat() if experiment.completed_at else None,
        "statistics": statistics.model_dump(),
        "results": {
            "total": result_total,
            "page": page,
            "page_size": page_size,
            "items": [
                {
                    "id": r.id,
                    "seq": r.seq,
                    "input_text": r.input_text,
                    "expected_output": r.expected_output,
                    "actual_output": r.actual_output,
                    "response_time_ms": r.response_time_ms,
                    "status": r.status,
                    "error_message": r.error_message,
                }
                for r in results_data
            ],
        },
    }


async def cancel_experiment(
    db: AsyncSession,
    experiment_id: int,
    operator: str,
) -> dict:
    """取消评测实验"""
    experiment = await get_experiment(db, experiment_id)

    if experiment.status != ExperimentStatus.RUNNING:
        raise AppException(ErrorCode.OPERATION_NOT_ALLOWED, "只有执行中的实验可以取消")

    # 调用引擎取消任务
    from app.engine.evaluation_engine import evaluation_engine
    cancelled = evaluation_engine.cancel(experiment_id)

    if not cancelled:
        # 任务可能已经完成，重新检查状态
        await db.refresh(experiment)
        if experiment.status != ExperimentStatus.RUNNING:
            raise AppException(ErrorCode.OPERATION_NOT_ALLOWED, "实验已不在执行中状态")
        # 强制更新状态（任务已完成但状态未更新的边界情况）
        experiment.status = ExperimentStatus.CANCELLED
        experiment.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)

    return {"id": experiment_id, "status": ExperimentStatus.CANCELLED}


async def get_experiment_results(
    db: AsyncSession,
    experiment_id: int,
    page: int = 1,
    page_size: int = 50,
    result_status: Optional[str] = None,
) -> Tuple[List[dict], int]:
    """分页查询逐条评测结果"""
    await get_experiment(db, experiment_id)

    conditions = [ExperimentResult.experiment_id == experiment_id]
    if result_status:
        conditions.append(ExperimentResult.status == result_status)

    where_clause = and_(*conditions)

    count_stmt = select(func.count()).select_from(ExperimentResult).where(where_clause)
    total = (await db.execute(count_stmt)).scalar_one()

    offset = (page - 1) * page_size
    stmt = (
        select(ExperimentResult)
        .where(where_clause)
        .order_by(ExperimentResult.seq)
        .offset(offset)
        .limit(page_size)
    )
    results = (await db.execute(stmt)).scalars().all()

    return [
        {
            "id": r.id,
            "seq": r.seq,
            "input_text": r.input_text,
            "expected_output": r.expected_output,
            "actual_output": r.actual_output,
            "response_time_ms": r.response_time_ms,
            "status": r.status,
            "error_message": r.error_message,
        }
        for r in results
    ], total


async def export_experiment_results(
    db: AsyncSession,
    experiment_id: int,
) -> list:
    """导出全部评测结果（用于流式响应）"""
    await get_experiment(db, experiment_id)

    stmt = (
        select(ExperimentResult)
        .where(ExperimentResult.experiment_id == experiment_id)
        .order_by(ExperimentResult.seq)
    )
    results = (await db.execute(stmt)).scalars().all()

    return [
        {
            "seq": r.seq,
            "input_text": r.input_text,
            "expected_output": r.expected_output,
            "actual_output": r.actual_output,
            "response_time_ms": r.response_time_ms,
            "status": r.status,
            "error_message": r.error_message,
        }
        for r in results
    ]
