"""
模型管理业务逻辑层
"""
from datetime import datetime, timezone
from typing import Optional, List, Tuple

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model import Model
from app.models.experiment import Experiment, ExperimentStatus
from app.schemas.model import ModelCreate, ModelUpdate, ModelResponse
from app.utils.crypto import get_crypto
from app.utils.audit import record_audit_log, AuditAction, AuditResourceType
from app.utils.response import AppException, ErrorCode


def _build_model_response(model: Model) -> ModelResponse:
    """将 ORM 模型对象转换为响应体，处理 API Key 脱敏"""
    crypto = get_crypto()
    api_key_masked = None
    if model.api_key_enc:
        try:
            plaintext = crypto.decrypt(model.api_key_enc)
            api_key_masked = crypto.mask(plaintext)
        except Exception:
            api_key_masked = "****"

    return ModelResponse(
        id=model.id,
        name=model.name,
        model_type=model.model_type,
        version=model.version,
        description=model.description,
        endpoint_url=model.endpoint_url,
        api_key_masked=api_key_masked,
        status=model.status,
        created_by=model.created_by,
        updated_by=model.updated_by,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


async def list_models(
    db: AsyncSession,
    name: Optional[str] = None,
    model_type: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> Tuple[List[ModelResponse], int]:
    """
    获取模型列表（支持搜索、筛选、分页）

    Returns:
        (模型列表, 总条数)
    """
    # 构建查询条件
    conditions = [Model.deleted_at.is_(None)]
    if name:
        conditions.append(Model.name.ilike(f"%{name}%"))
    if model_type:
        conditions.append(Model.model_type == model_type)
    if status:
        conditions.append(Model.status == status)

    where_clause = and_(*conditions)

    # 查询总数
    count_stmt = select(func.count()).select_from(Model).where(where_clause)
    total = (await db.execute(count_stmt)).scalar_one()

    # 查询数据
    offset = (page - 1) * page_size
    stmt = (
        select(Model)
        .where(where_clause)
        .order_by(Model.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    models = result.scalars().all()

    return [_build_model_response(m) for m in models], total


async def get_model(db: AsyncSession, model_id: int) -> Model:
    """
    获取模型（未删除），不存在则抛出异常

    Returns:
        Model ORM 对象
    """
    stmt = select(Model).where(Model.id == model_id, Model.deleted_at.is_(None))
    result = await db.execute(stmt)
    model = result.scalar_one_or_none()
    if model is None:
        raise AppException(ErrorCode.NOT_FOUND, "模型不存在")
    return model


async def create_model(
    db: AsyncSession,
    data: ModelCreate,
    operator: str,
) -> ModelResponse:
    """创建模型"""
    # 检查名称唯一性（软删除记录不参与）
    stmt = select(Model).where(Model.name == data.name, Model.deleted_at.is_(None))
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        raise AppException(ErrorCode.NAME_EXISTS, "模型名称已存在")

    # 加密 API Key
    crypto = get_crypto()
    api_key_enc = None
    if data.api_key:
        api_key_enc = crypto.encrypt(data.api_key)

    model = Model(
        name=data.name,
        model_type=data.model_type,
        version=data.version,
        description=data.description,
        endpoint_url=data.endpoint_url,
        api_key_enc=api_key_enc,
        status="ACTIVE",
        created_by=operator,
        updated_by=operator,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        updated_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.add(model)
    await db.flush()  # 获取自增 ID

    # 记录审计日志
    await record_audit_log(
        db=db,
        operator=operator,
        action=AuditAction.CREATE,
        resource_type=AuditResourceType.MODEL,
        resource_id=model.id,
        detail={"name": model.name, "model_type": model.model_type},
    )

    return _build_model_response(model)


async def update_model(
    db: AsyncSession,
    model_id: int,
    data: ModelUpdate,
    operator: str,
) -> ModelResponse:
    """编辑模型（名称不可修改）"""
    model = await get_model(db, model_id)

    # 记录变更前的值（用于审计日志）
    before = {
        "model_type": model.model_type,
        "version": model.version,
        "description": model.description,
        "status": model.status,
    }

    # 更新字段
    crypto = get_crypto()
    if data.model_type is not None:
        model.model_type = data.model_type
    if data.version is not None:
        model.version = data.version
    if data.description is not None:
        model.description = data.description
    if data.endpoint_url is not None:
        model.endpoint_url = data.endpoint_url
    if data.api_key is not None:
        model.api_key_enc = crypto.encrypt(data.api_key)
    if data.status is not None:
        model.status = data.status

    model.updated_by = operator
    model.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    # 记录审计日志
    after = {
        "model_type": model.model_type,
        "version": model.version,
        "description": model.description,
        "status": model.status,
    }
    await record_audit_log(
        db=db,
        operator=operator,
        action=AuditAction.UPDATE,
        resource_type=AuditResourceType.MODEL,
        resource_id=model.id,
        detail={"before": before, "after": after},
    )

    return _build_model_response(model)


async def delete_model(
    db: AsyncSession,
    model_id: int,
    operator: str,
) -> None:
    """软删除模型（有进行中实验时拒绝）"""
    model = await get_model(db, model_id)

    # 检查是否有进行中的评测实验
    stmt = select(func.count()).select_from(Experiment).where(
        Experiment.model_id == model_id,
        Experiment.status == ExperimentStatus.COMPLETED,
        Experiment.deleted_at.is_(None),
    )
    running_count = (await db.execute(stmt)).scalar_one()
    if running_count > 0:
        raise AppException(ErrorCode.OPERATION_NOT_ALLOWED, "该模型有进行中的评测实验，无法删除")

    # 软删除
    model.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    model.updated_by = operator
    model.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    # 记录审计日志
    await record_audit_log(
        db=db,
        operator=operator,
        action=AuditAction.DELETE,
        resource_type=AuditResourceType.MODEL,
        resource_id=model.id,
        detail={"name": model.name},
    )


async def get_model_with_experiments(
    db: AsyncSession,
    model_id: int,
) -> dict:
    """获取模型详情（含关联实验历史最近 10 条）"""
    model = await get_model(db, model_id)

    # 查询关联实验历史（最近 10 条）
    stmt = (
        select(Experiment)
        .where(
            Experiment.model_id == model_id,
            Experiment.deleted_at.is_(None),
        )
        .order_by(Experiment.created_at.desc())
        .limit(10)
    )
    result = await db.execute(stmt)
    experiments = result.scalars().all()

    model_resp = _build_model_response(model)
    return {
        **model_resp.model_dump(),
        "recent_experiments": [
            {
                "id": exp.id,
                "name": exp.name,
                "status": exp.status,
                "created_at": exp.created_at.isoformat() if exp.created_at else None,
                "completed_at": exp.completed_at.isoformat() if exp.completed_at else None,
            }
            for exp in experiments
        ],
    }
