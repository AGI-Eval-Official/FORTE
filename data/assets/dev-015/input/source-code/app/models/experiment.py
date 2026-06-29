"""
评测实验表 ORM 定义
对应数据库表：experiment
"""
import enum
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ExperimentStatus(str, enum.Enum):
    """评测实验状态枚举"""
    PENDING = "PENDING"       # 待执行
    RUNNING = "RUNNING"       # 执行中
    COMPLETED = "COMPLETED"   # 已完成
    FAILED = "FAILED"         # 失败
    CANCELLED = "CANCELLED"   # 已取消


class Experiment(Base):
    """评测实验表"""
    __tablename__ = "experiment"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="实验名称（允许重名）")
    model_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("model.id"), nullable=False, comment="关联模型 ID"
    )
    dataset_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dataset.id"), nullable=False, comment="关联评测集 ID"
    )
    description: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="描述")
    concurrency: Mapped[int] = mapped_column(
        Integer, nullable=False, default=5, comment="并发数（1-20）"
    )
    timeout_seconds: Mapped[int] = mapped_column(
        Integer, nullable=False, default=30, comment="单条超时秒数（5-300）"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PENDING",
        comment="状态：PENDING/RUNNING/COMPLETED/FAILED/CANCELLED"
    )
    # 统计字段（实验完成时预计算写入）
    total_count: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="总条数")
    success_count: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="成功条数")
    failed_count: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="失败条数")
    avg_response_ms: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="平均响应时间（ms）")
    p50_ms: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="P50 响应时间（ms）")
    p90_ms: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="P90 响应时间（ms）")
    p99_ms: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="P99 响应时间（ms）")
    # 元数据
    created_by: Mapped[str] = mapped_column(String(100), nullable=False, comment="创建人用户 ID")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), comment="创建时间"
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="完成时间"
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, default=None, comment="软删除时间"
    )

    def __repr__(self) -> str:
        return f"<Experiment id={self.id} name={self.name} status={self.status}>"
