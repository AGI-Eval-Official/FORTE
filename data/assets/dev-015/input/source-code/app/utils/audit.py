"""
操作日志工具
记录创建、修改、删除操作的审计日志
"""
import json
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditAction:
    """操作类型常量"""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class AuditResourceType:
    """资源类型常量"""
    MODEL = "model"
    DATASET = "dataset"
    EXPERIMENT = "experiment"


async def record_audit_log(
    db: AsyncSession,
    operator: str,
    action: str,
    resource_type: str,
    resource_id: int,
    detail: Optional[Dict[str, Any]] = None,
) -> None:
    """
    记录操作日志

    Args:
        db: 数据库 Session
        operator: 操作人用户 ID
        action: 操作类型（CREATE/UPDATE/DELETE）
        resource_type: 资源类型（model/dataset/experiment）
        resource_id: 资源 ID
        detail: 操作详情（变更前后的关键字段值）
    """
    log = AuditLog(
        operator=operator,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        detail=json.dumps(detail, ensure_ascii=False) if detail else None,
    )
    db.add(log)
    # 注意：不在此处 commit，由调用方统一提交事务
