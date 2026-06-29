"""
FastAPI 应用入口
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os

from app.database import init_db
from app.routers import models, datasets, experiments
from app.utils.response import AppException, ApiResponse, ErrorCode

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    logger.info("初始化数据库...")
    await init_db()

    # 启动恢复：将 RUNNING 状态的实验标记为 FAILED（进程重启导致任务丢失）
    await _recover_running_experiments()

    logger.info("应用启动完成")
    yield
    logger.info("应用关闭")


async def _recover_running_experiments():
    """启动恢复：将 RUNNING 状态的实验标记为 FAILED"""
    from app.database import AsyncSessionLocal
    from app.models.experiment import Experiment, ExperimentStatus
    from sqlalchemy import select, update
    from datetime import datetime, timezone

    async with AsyncSessionLocal() as db:
        stmt = (
            update(Experiment)
            .where(Experiment.status == ExperimentStatus.RUNNING)
            .values(
                status=ExperimentStatus.FAILED,
                completed_at=datetime.now(timezone.utc).replace(tzinfo=None),
            )
        )
        result = await db.execute(stmt)
        if result.rowcount > 0:
            logger.warning(f"启动恢复：将 {result.rowcount} 个 RUNNING 实验标记为 FAILED")
        await db.commit()


# 创建 FastAPI 应用
app = FastAPI(
    title="评测平台 API",
    description="AI 模型评测平台后端接口",
    version="1.0.0",
    lifespan=lifespan,
)

# 配置 CORS（允许前端开发服务器跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理器
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """处理业务异常，返回统一格式"""
    return JSONResponse(
        status_code=exc.http_status,
        content={"code": exc.code, "message": exc.message, "data": None},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """处理未预期的异常"""
    logger.error(f"未处理的异常：{exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"code": ErrorCode.INTERNAL_ERROR, "message": "服务器内部错误", "data": None},
    )


# 注册路由
app.include_router(models.router)
app.include_router(datasets.router)
app.include_router(experiments.router)


# 健康检查接口
@app.get("/health", tags=["系统"])
async def health_check():
    return {"status": "ok", "version": "1.0.0"}


# 挂载前端静态文件（生产环境）
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
