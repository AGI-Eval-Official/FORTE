"""
评测集表 ORM 定义
对应数据库表：dataset
"""
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Dataset(Base):
    """评测集表"""
    __tablename__ = "dataset"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="评测集名称")
    version: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="版本号，格式 vX.Y.Z")
    description: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="描述")
    item_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="数据条数（冗余字段，避免 COUNT 查询）"
    )
    created_by: Mapped[str] = mapped_column(String(100), nullable=False, comment="创建人用户 ID")
    updated_by: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="最后修改人用户 ID")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now(), comment="更新时间"
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, default=None, comment="软删除时间，NULL 表示未删除"
    )

    def __repr__(self) -> str:
        return f"<Dataset id={self.id} name={self.name} item_count={self.item_count}>"
