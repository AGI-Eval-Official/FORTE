"""
操作日志表 ORM 定义
对应数据库表：audit_log
"""
from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AuditLog(Base):
    """操作日志表"""
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    operator: Mapped[str] = mapped_column(String(100), nullable=False, comment="操作人用户 ID")
    action: Mapped[str] = mapped_column(String(50), nullable=False, comment="操作类型：CREATE/UPDATE/DELETE")
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="资源类型：model/dataset/experiment")
    resource_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="操作的资源 ID")
    detail: Mapped[str | None] = mapped_column(Text, nullable=True, comment="操作详情（JSON 格式，记录变更前后值）")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), comment="操作时间"
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog id={self.id} operator={self.operator} "
            f"action={self.action} resource={self.resource_type}:{self.resource_id}>"
        )
