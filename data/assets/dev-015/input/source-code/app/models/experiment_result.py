"""
逐条评测结果表 ORM 定义
对应数据库表：experiment_result
"""
import enum
from datetime import datetime
from sqlalchemy import Integer, Text, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ResultStatus(str, enum.Enum):
    """评测结果状态枚举"""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class ExperimentResult(Base):
    """逐条评测结果表"""
    __tablename__ = "experiment_result"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    experiment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("experiment.id"), nullable=False, comment="所属实验 ID"
    )
    dataset_item_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dataset_item.id"), nullable=False, comment="对应评测集条目 ID"
    )
    seq: Mapped[int] = mapped_column(Integer, nullable=False, comment="对应评测集中的序号")
    input_text: Mapped[str] = mapped_column(Text, nullable=False, comment="快照：执行时的 input")
    expected_output: Mapped[str | None] = mapped_column(Text, nullable=True, comment="快照：执行时的 expected_output")
    actual_output: Mapped[str | None] = mapped_column(Text, nullable=True, comment="模型返回的输出")
    response_time_ms: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="响应时间（ms），失败时为 NULL"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="状态：SUCCESS/FAILED"
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True, comment="失败时的错误信息")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), comment="创建时间"
    )

    def __repr__(self) -> str:
        return (
            f"<ExperimentResult id={self.id} experiment_id={self.experiment_id} "
            f"seq={self.seq} status={self.status}>"
        )
