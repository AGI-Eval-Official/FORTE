"""
评测集数据条目表 ORM 定义
对应数据库表：dataset_item
"""
from datetime import datetime
from sqlalchemy import Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DatasetItem(Base):
    """评测集数据条目表"""
    __tablename__ = "dataset_item"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    dataset_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dataset.id"), nullable=False, comment="所属评测集 ID"
    )
    seq: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="序号（在该评测集内从 1 开始）"
    )
    input_text: Mapped[str] = mapped_column(Text, nullable=False, comment="评测输入")
    expected_output: Mapped[str | None] = mapped_column(Text, nullable=True, comment="期望输出（可为空）")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), comment="创建时间"
    )

    def __repr__(self) -> str:
        return f"<DatasetItem id={self.id} dataset_id={self.dataset_id} seq={self.seq}>"
