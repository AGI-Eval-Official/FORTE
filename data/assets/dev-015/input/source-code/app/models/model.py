"""
模型表 ORM 定义
对应数据库表：model
"""
import enum
from datetime import datetime
from sqlalchemy import String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ModelType(str, enum.Enum):
    """模型类型枚举"""
    LLM = "LLM"
    CLASSIFICATION = "CLASSIFICATION"
    REGRESSION = "REGRESSION"
    OTHER = "OTHER"


class ModelStatus(str, enum.Enum):
    """模型状态枚举"""
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"


class Model(Base):
    """AI 模型表"""
    __tablename__ = "model"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="模型名称")
    model_type: Mapped[str] = mapped_column(String(20), nullable=False, comment="模型类型")
    version: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="版本号，格式 vX.Y.Z")
    description: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="描述")
    endpoint_url: Mapped[str | None] = mapped_column(Text, nullable=True, comment="模型端点 URL")
    api_key_enc: Mapped[str | None] = mapped_column(Text, nullable=True, comment="AES-256-GCM 加密后的 API Key")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE", comment="状态：ACTIVE/DISABLED")
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
        return f"<Model id={self.id} name={self.name} type={self.model_type}>"
