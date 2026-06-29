"""
数据库连接与 Session 管理
使用 SQLAlchemy 2.0 异步引擎 + aiosqlite
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import event, text

from app.config import settings


# 创建异步引擎
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    connect_args={"check_same_thread": False},
)

# 异步 Session 工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """所有 ORM 模型的基类"""
    pass


async def init_db():
    """初始化数据库：建表、设置 PRAGMA"""
    async with engine.begin() as conn:
        # 启用外键约束
        await conn.execute(text("PRAGMA foreign_keys = ON"))
        # 启用 WAL 模式，提升并发读写性能
        await conn.execute(text("PRAGMA journal_mode = WAL"))
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    """FastAPI 依赖注入：获取数据库 Session"""
    async with AsyncSessionLocal() as session:
        try:
            # 每次连接时启用外键约束（SQLite 需要每次连接设置）
            await session.execute(text("PRAGMA foreign_keys = ON"))
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
