"""
评测执行引擎
负责并发调用模型端点、收集结果、计算统计指标
"""
import asyncio
import time
import statistics
import logging
from datetime import datetime, timezone
from typing import Dict, Optional

import httpx
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.experiment import Experiment, ExperimentStatus
from app.models.experiment_result import ExperimentResult, ResultStatus
from app.models.dataset_item import DatasetItem
from app.models.model import Model
from app.utils.crypto import get_crypto

logger = logging.getLogger(__name__)

# 全局任务注册表（进程内内存状态）
_running_tasks: Dict[int, asyncio.Task] = {}


class EvaluationEngine:
    """评测执行引擎"""

    async def start(self, experiment_id: int) -> None:
        """
        在后台启动评测任务

        Args:
            experiment_id: 评测实验 ID
        """
        task = asyncio.create_task(
            self._run(experiment_id),
            name=f"eval_experiment_{experiment_id}",
        )
        _running_tasks[experiment_id] = task

        # 任务完成后从注册表中移除
        task.add_done_callback(lambda t: _running_tasks.pop(experiment_id, None))

    def cancel(self, experiment_id: int) -> bool:
        """
        取消正在执行的评测任务

        Args:
            experiment_id: 评测实验 ID

        Returns:
            True 表示成功发起取消，False 表示任务不存在或已完成
        """
        task = _running_tasks.get(experiment_id)
        if task and not task.done():
            task.cancel()
            return True
        return False

    async def _run(self, experiment_id: int) -> None:
        """评测任务主流程"""
        async with AsyncSessionLocal() as db:
            try:
                await self._execute(db, experiment_id)
            except asyncio.CancelledError:
                # 保留已执行的结果，仅更新状态为 CANCELLED
                await self._update_status(db, experiment_id, ExperimentStatus.CANCELLED)
                logger.info(f"实验 {experiment_id} 已取消")
                raise  # 必须重新抛出，让 asyncio 正确处理取消
            except Exception as e:
                logger.error(f"实验 {experiment_id} 执行失败：{e}", exc_info=True)
                await self._update_status(db, experiment_id, ExperimentStatus.FAILED)

    async def _execute(self, db: AsyncSession, experiment_id: int) -> None:
        """执行评测实验"""
        # 加载实验信息
        stmt = select(Experiment).where(Experiment.id == experiment_id)
        experiment = (await db.execute(stmt)).scalar_one_or_none()
        if experiment is None:
            logger.error(f"实验 {experiment_id} 不存在")
            return

        # 加载关联模型
        model_stmt = select(Model).where(Model.id == experiment.model_id)
        model = (await db.execute(model_stmt)).scalar_one_or_none()
        if model is None:
            await self._update_status(db, experiment_id, ExperimentStatus.FAILED)
            return

        # 解密 API Key
        api_key = None
        if model.api_key_enc:
            try:
                api_key = get_crypto().decrypt(model.api_key_enc)
            except Exception:
                logger.warning(f"实验 {experiment_id}：API Key 解密失败，将不携带认证头")

        # 分批加载评测集数据（每批 500 条）
        all_items = await self._load_dataset_items(db, experiment.dataset_id)

        if not all_items:
            # 评测集为空，直接完成
            await self._finalize(db, experiment_id, [])
            return

        # 创建并发信号量
        semaphore = asyncio.Semaphore(experiment.concurrency)

        async def _evaluate_with_semaphore(item: DatasetItem):
            async with semaphore:
                return await self._evaluate_single_item(
                    experiment=experiment,
                    item=item,
                    endpoint_url=model.endpoint_url,
                    api_key=api_key,
                )

        # 并发执行所有评测任务
        tasks = [
            asyncio.create_task(_evaluate_with_semaphore(item))
            for item in all_items
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 将结果写入数据库
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        db_results = []
        for item, result in zip(all_items, results):
            if isinstance(result, Exception):
                # gather 中的异常（非 CancelledError）
                db_result = ExperimentResult(
                    experiment_id=experiment_id,
                    dataset_item_id=item.id,
                    seq=item.seq,
                    input_text=item.input_text,
                    expected_output=item.expected_output,
                    actual_output=None,
                    response_time_ms=None,
                    status=ResultStatus.FAILED,
                    error_message=str(result),
                    created_at=now,
                )
            else:
                db_result = result
                db_result.created_at = now
            db_results.append(db_result)

        # 批量写入结果
        for i in range(0, len(db_results), 500):
            batch = db_results[i:i + 500]
            db.add_all(batch)
            await db.flush()

        # 计算统计指标并更新实验状态
        await self._finalize(db, experiment_id, db_results)

    async def _load_dataset_items(
        self, db: AsyncSession, dataset_id: int
    ) -> list:
        """分批加载评测集数据（每批 500 条）"""
        all_items = []
        batch_size = 500
        offset = 0

        while True:
            stmt = (
                select(DatasetItem)
                .where(DatasetItem.dataset_id == dataset_id)
                .order_by(DatasetItem.seq)
                .offset(offset)
                .limit(batch_size)
            )
            result = await db.execute(stmt)
            batch = result.scalars().all()
            if not batch:
                break
            all_items.extend(batch)
            offset += batch_size
            if len(batch) < batch_size:
                break

        return all_items

    async def _evaluate_single_item(
        self,
        experiment: Experiment,
        item: DatasetItem,
        endpoint_url: Optional[str],
        api_key: Optional[str],
    ) -> ExperimentResult:
        """
        评测单条数据

        Returns:
            ExperimentResult ORM 对象（未设置 created_at，由调用方统一设置）
        """
        if not endpoint_url:
            return ExperimentResult(
                experiment_id=experiment.id,
                dataset_item_id=item.id,
                seq=item.seq,
                input_text=item.input_text,
                expected_output=item.expected_output,
                actual_output=None,
                response_time_ms=None,
                status=ResultStatus.FAILED,
                error_message="模型端点 URL 未配置",
            )

        start_time = time.monotonic()
        try:
            headers = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            async with httpx.AsyncClient(
                timeout=httpx.Timeout(experiment.timeout_seconds)
            ) as client:
                response = await client.post(
                    endpoint_url,
                    json={"input": item.input_text},
                    headers=headers,
                )
                response.raise_for_status()
                elapsed_ms = int((time.monotonic() - start_time) * 1000)

                # 尝试从响应中提取 output 字段
                try:
                    resp_json = response.json()
                    actual_output = resp_json.get("output", response.text)
                except Exception:
                    actual_output = response.text

                return ExperimentResult(
                    experiment_id=experiment.id,
                    dataset_item_id=item.id,
                    seq=item.seq,
                    input_text=item.input_text,
                    expected_output=item.expected_output,
                    actual_output=str(actual_output) if actual_output is not None else None,
                    response_time_ms=elapsed_ms,
                    status=ResultStatus.SUCCESS,
                    error_message=None,
                )

        except httpx.TimeoutException:
            return ExperimentResult(
                experiment_id=experiment.id,
                dataset_item_id=item.id,
                seq=item.seq,
                input_text=item.input_text,
                expected_output=item.expected_output,
                actual_output=None,
                response_time_ms=None,
                status=ResultStatus.FAILED,
                error_message="请求超时",
            )
        except httpx.HTTPStatusError as e:
            return ExperimentResult(
                experiment_id=experiment.id,
                dataset_item_id=item.id,
                seq=item.seq,
                input_text=item.input_text,
                expected_output=item.expected_output,
                actual_output=None,
                response_time_ms=None,
                status=ResultStatus.FAILED,
                error_message=f"HTTP 错误 {e.response.status_code}：{e.response.text[:200]}",
            )
        except Exception as e:
            return ExperimentResult(
                experiment_id=experiment.id,
                dataset_item_id=item.id,
                seq=item.seq,
                input_text=item.input_text,
                expected_output=item.expected_output,
                actual_output=None,
                response_time_ms=None,
                status=ResultStatus.FAILED,
                error_message=str(e),
            )

    async def _finalize(
        self,
        db: AsyncSession,
        experiment_id: int,
        results: list,
    ) -> None:
        """计算统计指标，更新实验状态为 COMPLETED"""
        total_count = len(results)
        success_results = [r for r in results if isinstance(r, ExperimentResult) and r.status == ResultStatus.SUCCESS]
        failed_count = total_count - len(success_results)

        # 计算响应时间统计（仅包含成功条目）
        response_times = [
            r.response_time_ms for r in success_results
            if r.response_time_ms is not None
        ]

        avg_response_ms = None
        p50_ms = None
        p90_ms = None
        p99_ms = None

        if response_times:
            avg_response_ms = int(sum(response_times) / len(response_times))
            sorted_times = sorted(response_times)
            n = len(sorted_times)
            p50_ms = sorted_times[int(n * 0.50)]
            p90_ms = sorted_times[int(n * 0.90)]
            p99_ms = sorted_times[int(n * 0.99) - 1]

        # 更新实验统计字段和状态
        stmt = select(Experiment).where(Experiment.id == experiment_id)
        experiment = (await db.execute(stmt)).scalar_one_or_none()
        if experiment:
            experiment.status = ExperimentStatus.COMPLETED
            experiment.total_count = total_count
            experiment.success_count = len(success_results)
            experiment.failed_count = failed_count
            experiment.avg_response_ms = avg_response_ms
            experiment.p50_ms = p50_ms
            experiment.p90_ms = p90_ms
            experiment.p99_ms = p99_ms
            experiment.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
            await db.commit()

        logger.info(
            f"实验 {experiment_id} 完成：总计 {total_count} 条，"
            f"成功 {len(success_results)} 条，失败 {failed_count} 条"
        )

    async def _update_status(
        self,
        db: AsyncSession,
        experiment_id: int,
        status: ExperimentStatus,
    ) -> None:
        """更新实验状态"""
        stmt = select(Experiment).where(Experiment.id == experiment_id)
        experiment = (await db.execute(stmt)).scalar_one_or_none()
        if experiment:
            experiment.status = status
            if status in (ExperimentStatus.COMPLETED, ExperimentStatus.CANCELLED, ExperimentStatus.FAILED):
                experiment.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
            await db.commit()


# 全局引擎实例
evaluation_engine = EvaluationEngine()
