"""
评测集管理业务逻辑层
"""
import json
import io
from datetime import datetime, timezone
from typing import Optional, List, Tuple

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset import Dataset
from app.models.dataset_item import DatasetItem
from app.models.experiment import Experiment, ExperimentStatus
from app.schemas.dataset import DatasetCreate, DatasetUpdate, DatasetResponse, DatasetItemResponse
from app.utils.audit import record_audit_log, AuditAction, AuditResourceType
from app.utils.response import AppException, ErrorCode
from app.config import settings


def _build_dataset_response(dataset: Dataset) -> DatasetResponse:
    """将 ORM 对象转换为响应体"""
    return DatasetResponse(
        id=dataset.id,
        name=dataset.name,
        version=dataset.version,
        description=dataset.description,
        item_count=dataset.item_count,
        created_by=dataset.created_by,
        updated_by=dataset.updated_by,
        created_at=dataset.created_at,
        updated_at=dataset.updated_at,
    )


async def list_datasets(
    db: AsyncSession,
    name: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> Tuple[List[DatasetResponse], int]:
    """获取评测集列表"""
    conditions = [Dataset.deleted_at.is_(None)]
    if name:
        conditions.append(Dataset.name.ilike(f"%{name}%"))

    where_clause = and_(*conditions)

    count_stmt = select(func.count()).select_from(Dataset).where(where_clause)
    total = (await db.execute(count_stmt)).scalar_one()

    offset = (page - 1) * page_size
    stmt = (
        select(Dataset)
        .where(where_clause)
        .order_by(Dataset.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    datasets = result.scalars().all()

    return [_build_dataset_response(d) for d in datasets], total


async def get_dataset(db: AsyncSession, dataset_id: int) -> Dataset:
    """获取评测集（未删除），不存在则抛出异常"""
    stmt = select(Dataset).where(Dataset.id == dataset_id, Dataset.deleted_at.is_(None))
    result = await db.execute(stmt)
    dataset = result.scalar_one_or_none()
    if dataset is None:
        raise AppException(ErrorCode.NOT_FOUND, "评测集不存在")
    return dataset


async def create_dataset(
    db: AsyncSession,
    data: DatasetCreate,
    operator: str,
) -> DatasetResponse:
    """创建评测集"""
    # 检查名称唯一性
    stmt = select(Dataset).where(Dataset.name == data.name, Dataset.deleted_at.is_(None))
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        raise AppException(ErrorCode.NAME_EXISTS, "评测集名称已存在")

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    dataset = Dataset(
        name=data.name,
        version=data.version,
        description=data.description,
        item_count=0,
        created_by=operator,
        updated_by=operator,
        created_at=now,
        updated_at=now,
    )
    db.add(dataset)
    await db.flush()

    await record_audit_log(
        db=db,
        operator=operator,
        action=AuditAction.CREATE,
        resource_type=AuditResourceType.DATASET,
        resource_id=dataset.id,
        detail={"name": dataset.name},
    )

    return _build_dataset_response(dataset)


async def update_dataset(
    db: AsyncSession,
    dataset_id: int,
    data: DatasetUpdate,
    operator: str,
) -> DatasetResponse:
    """编辑评测集基本信息"""
    dataset = await get_dataset(db, dataset_id)

    before = {"name": dataset.name, "version": dataset.version, "description": dataset.description}

    # 如果修改了名称，检查唯一性
    if data.name is not None and data.name != dataset.name:
        stmt = select(Dataset).where(
            Dataset.name == data.name,
            Dataset.deleted_at.is_(None),
            Dataset.id != dataset_id,
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            raise AppException(ErrorCode.NAME_EXISTS, "评测集名称已存在")
        dataset.name = data.name

    if data.version is not None:
        dataset.version = data.version
    if data.description is not None:
        dataset.description = data.description

    dataset.updated_by = operator
    dataset.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    after = {"name": dataset.name, "version": dataset.version, "description": dataset.description}
    await record_audit_log(
        db=db,
        operator=operator,
        action=AuditAction.UPDATE,
        resource_type=AuditResourceType.DATASET,
        resource_id=dataset.id,
        detail={"before": before, "after": after},
    )

    return _build_dataset_response(dataset)


async def delete_dataset(
    db: AsyncSession,
    dataset_id: int,
    operator: str,
) -> None:
    """软删除评测集（有进行中实验时拒绝）"""
    dataset = await get_dataset(db, dataset_id)

    # 检查是否有进行中的评测实验
    stmt = select(func.count()).select_from(Experiment).where(
        Experiment.dataset_id == dataset_id,
        Experiment.status == ExperimentStatus.RUNNING,
        Experiment.deleted_at.is_(None),
    )
    running_count = (await db.execute(stmt)).scalar_one()
    if running_count > 0:
        raise AppException(ErrorCode.OPERATION_NOT_ALLOWED, "该评测集有进行中的评测实验，无法删除")

    dataset.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    dataset.updated_by = operator
    dataset.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    await record_audit_log(
        db=db,
        operator=operator,
        action=AuditAction.DELETE,
        resource_type=AuditResourceType.DATASET,
        resource_id=dataset.id,
        detail={"name": dataset.name},
    )


async def import_dataset_items(
    db: AsyncSession,
    dataset_id: int,
    file_content: bytes,
    mode: str,  # "append" or "overwrite"
    operator: str,
) -> dict:
    """
    导入评测集数据

    Args:
        file_content: JSON 文件内容（字节）
        mode: 导入模式，append=追加，overwrite=清空重新导入
    """
    # 检查文件大小
    if len(file_content) > settings.max_upload_size:
        raise AppException(ErrorCode.FILE_TOO_LARGE, "文件大小超限，最大支持 50MB")

    dataset = await get_dataset(db, dataset_id)

    # 解析 JSON 文件（流式解析）
    items_data = _parse_json_file(file_content)

    if mode == "overwrite":
        # 清空现有数据
        from sqlalchemy import delete
        await db.execute(delete(DatasetItem).where(DatasetItem.dataset_id == dataset_id))
        start_seq = 1
    else:
        # 追加模式：获取当前最大 seq
        stmt = select(func.max(DatasetItem.seq)).where(DatasetItem.dataset_id == dataset_id)
        max_seq = (await db.execute(stmt)).scalar_one_or_none() or 0
        start_seq = max_seq

    # 批量插入数据
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    batch_size = 500
    imported_count = 0

    for i in range(0, len(items_data), batch_size):
        batch = items_data[i:i + batch_size]
        db_items = [
            DatasetItem(
                dataset_id=dataset_id,
                seq=start_seq + i + j,
                input_text=item["input"],
                expected_output=item.get("expected_output"),
                created_at=now,
            )
            for j, item in enumerate(batch)
        ]
        db.add_all(db_items)
        imported_count += len(batch)

    # 更新 item_count
    if mode == "overwrite":
        dataset.item_count = imported_count
    else:
        dataset.item_count += imported_count

    dataset.updated_by = operator
    dataset.updated_at = now

    await db.flush()

    return {
        "dataset_id": dataset_id,
        "imported_count": imported_count,
        "total_count": dataset.item_count,
        "mode": mode,
    }


def _parse_json_file(file_content: bytes) -> list:
    """
    解析 JSON 文件，校验格式

    Returns:
        解析后的数据列表

    Raises:
        AppException: 文件格式错误
    """
    try:
        text = file_content.decode("utf-8")
        data = json.loads(text)
    except UnicodeDecodeError:
        raise AppException(ErrorCode.FILE_FORMAT_ERROR, "文件编码错误，请使用 UTF-8 编码")
    except json.JSONDecodeError as e:
        raise AppException(ErrorCode.FILE_FORMAT_ERROR, f"JSON 格式错误：{str(e)}")

    if not isinstance(data, list):
        raise AppException(ErrorCode.FILE_FORMAT_ERROR, "JSON 文件格式错误，应为数组格式")

    # 校验每条数据
    for idx, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            raise AppException(ErrorCode.FILE_FORMAT_ERROR, f"第 {idx} 条数据格式错误，应为对象")
        if "input" not in item:
            raise AppException(ErrorCode.FILE_FORMAT_ERROR, f"第 {idx} 行缺少 input 字段")
        if not isinstance(item["input"], str):
            raise AppException(ErrorCode.FILE_FORMAT_ERROR, f"第 {idx} 行 input 字段必须为字符串")
        if "expected_output" in item and item["expected_output"] is not None:
            if not isinstance(item["expected_output"], str):
                raise AppException(ErrorCode.FILE_FORMAT_ERROR, f"第 {idx} 行 expected_output 字段必须为字符串")

    return data


async def get_dataset_items(
    db: AsyncSession,
    dataset_id: int,
    page: int = 1,
    page_size: int = 50,
) -> Tuple[List[DatasetItemResponse], int]:
    """分页查询评测集数据条目"""
    await get_dataset(db, dataset_id)  # 确认评测集存在

    count_stmt = select(func.count()).select_from(DatasetItem).where(
        DatasetItem.dataset_id == dataset_id
    )
    total = (await db.execute(count_stmt)).scalar_one()

    offset = (page - 1) * page_size
    stmt = (
        select(DatasetItem)
        .where(DatasetItem.dataset_id == dataset_id)
        .order_by(DatasetItem.seq)
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    items = result.scalars().all()

    return [DatasetItemResponse.model_validate(item) for item in items], total


async def get_dataset_with_experiments(
    db: AsyncSession,
    dataset_id: int,
) -> dict:
    """获取评测集详情（含关联实验历史最近 10 条）"""
    dataset = await get_dataset(db, dataset_id)

    stmt = (
        select(Experiment)
        .where(
            Experiment.dataset_id == dataset_id,
            Experiment.deleted_at.is_(None),
        )
        .order_by(Experiment.created_at.desc())
        .limit(10)
    )
    result = await db.execute(stmt)
    experiments = result.scalars().all()

    dataset_resp = _build_dataset_response(dataset)
    return {
        **dataset_resp.model_dump(),
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
