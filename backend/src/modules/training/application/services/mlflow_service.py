"""MLflow 集成服务 (T037a)

职责:
- 实现 IMetricsService 接口
- 从 MLflow Tracking Server 查询训练指标
- 为 T037c 停滞检测提供数据源

参考: spec.md L890-979 MLflow 集成方案
"""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from mlflow.exceptions import MlflowException
from mlflow.tracking import MlflowClient

from src.modules.training.application.interfaces import IMetricsService, MetricPoint

logger = logging.getLogger(__name__)


class MLflowServiceError(Exception):
    """MLflow 服务异常"""

    pass


class MLflowService(IMetricsService):
    """MLflow 指标服务实现

    实现 IMetricsService 接口，从 MLflow Tracking Server 查询训练指标。
    支持 job_id 到 MLflow run_id 的映射查询。

    注意: 本类使用 run_in_executor 包装同步 MLflow SDK 调用。
    这是可接受的例外情况，因为 mlflow.tracking.MlflowClient 没有官方异步版本。
    参见 backend/CLAUDE.md "AWS 异步操作规范" 中的例外说明。

    TODO: 监控第三方异步 MLflow 客户端 (如 aiomlflow) 的发布，适时迁移。
    """

    def __init__(
        self,
        tracking_uri: str,
        experiment_prefix: str = "ai-training-platform",
        timeout: int = 30,
        max_retries: int = 3,
    ) -> None:
        """初始化 MLflow 服务

        Args:
            tracking_uri: MLflow Tracking Server 地址
            experiment_prefix: 实验名称前缀
            timeout: 请求超时时间 (秒)
            max_retries: 最大重试次数
        """
        self._client = MlflowClient(tracking_uri=tracking_uri)
        self._experiment_prefix = experiment_prefix
        self._timeout = timeout
        self._max_retries = max_retries

    async def get_metric_history(
        self,
        job_id: int,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
    ) -> list[MetricPoint]:
        """从 MLflow 查询指标历史

        Args:
            job_id: 训练任务 ID
            metric_name: 指标名称 (如 'loss', 'accuracy')
            start_time: 查询起始时间
            end_time: 查询结束时间

        Returns:
            list[MetricPoint]: 指标数据点列表，按时间升序排列
        """
        # 1. 查找对应的 MLflow run
        run = await self._find_run_by_job_id(job_id)
        if not run:
            logger.debug(f"未找到 job_id={job_id} 对应的 MLflow run")
            return []

        run_id = run.info.run_id

        # 2. 获取指标历史
        try:
            metrics = await self._get_metric_history_with_retry(run_id, metric_name)
        except MlflowException as e:
            raise MLflowServiceError(f"MLflow unavailable: Failed to get metrics for run {run_id}: {e}") from e

        # 3. 转换时间戳并过滤
        start_ts = start_time.timestamp() * 1000
        end_ts = end_time.timestamp() * 1000

        result = []
        for m in metrics:
            if start_ts <= m.timestamp <= end_ts:
                # MLflow 时间戳是毫秒级
                ts = datetime.fromtimestamp(m.timestamp / 1000, tz=UTC)
                result.append(MetricPoint(timestamp=ts, value=m.value))

        # 4. 按时间升序排序
        result.sort(key=lambda p: p.timestamp)

        return result

    async def get_experiment(self, experiment_name: str) -> dict[str, Any]:
        """获取实验信息

        Args:
            experiment_name: 实验名称 (会自动添加前缀)

        Returns:
            dict: 实验信息

        Raises:
            MLflowServiceError: 实验不存在
        """
        full_name = f"{self._experiment_prefix}/{experiment_name}"

        def _get() -> Any:
            return self._client.get_experiment_by_name(full_name)

        experiment = await asyncio.get_event_loop().run_in_executor(None, _get)

        if experiment is None:
            raise MLflowServiceError(f"Experiment '{full_name}' not found")

        return {
            "experiment_id": experiment.experiment_id,
            "name": experiment.name,
            "artifact_location": experiment.artifact_location,
            "lifecycle_stage": experiment.lifecycle_stage,
        }

    async def list_runs(
        self,
        experiment_id: str,
        filter_string: str | None = None,
        max_results: int = 100,
    ) -> list[dict[str, Any]]:
        """列出实验下的运行

        Args:
            experiment_id: 实验 ID
            filter_string: 过滤条件
            max_results: 最大返回数量

        Returns:
            list[dict]: 运行信息列表
        """

        def _search() -> list[Any]:
            return self._client.search_runs(
                experiment_ids=[experiment_id],
                filter_string=filter_string or "",
                max_results=max_results,
                order_by=["start_time DESC"],
            )

        runs = await asyncio.get_event_loop().run_in_executor(None, _search)

        return [{"run_id": r.info.run_id, "status": r.info.status} for r in runs]

    async def check_health(self) -> bool:
        """健康检查

        Returns:
            bool: MLflow 服务是否可用
        """

        def _check() -> None:
            self._client.search_experiments(max_results=1)

        try:
            await asyncio.get_event_loop().run_in_executor(None, _check)
            return True
        except MlflowException:
            return False
        except Exception as e:
            logger.warning(
                f"MLflow 健康检查失败: {type(e).__name__}: {e}",
                exc_info=True,
            )
            return False

    async def _find_run_by_job_id(self, job_id: int) -> Any | None:
        """根据 job_id 查找 MLflow run

        使用 tags.job_id 进行过滤，返回最新的 run。

        Args:
            job_id: 训练任务 ID

        Returns:
            MLflow Run 对象，未找到返回 None
        """
        filter_string = f"tags.job_id = '{job_id}'"

        runs = await self._search_runs_with_retry(filter_string)

        if not runs:
            return None

        # 返回最新的 run (已按 start_time DESC 排序)
        return runs[0]

    async def _search_runs_with_retry(self, filter_string: str) -> list[Any]:
        """带重试的 run 搜索

        Args:
            filter_string: 过滤条件

        Returns:
            list: Run 列表
        """
        last_error = None

        for attempt in range(self._max_retries):
            try:

                def _search() -> list[Any]:
                    return self._client.search_runs(
                        experiment_ids=[],  # 搜索所有实验
                        filter_string=filter_string,
                        max_results=10,
                        order_by=["start_time DESC"],
                    )

                return await asyncio.get_event_loop().run_in_executor(None, _search)

            except MlflowException as e:
                last_error = e
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(0.1 * (attempt + 1))  # 指数退避
                    logger.debug(f"重试 MLflow 搜索 (attempt {attempt + 1})")
                continue

        raise MLflowServiceError(f"MLflow unavailable after {self._max_retries} retries: {last_error}")

    async def _get_metric_history_with_retry(self, run_id: str, metric_name: str) -> list[Any]:
        """带重试的指标历史查询

        Args:
            run_id: MLflow run ID
            metric_name: 指标名称

        Returns:
            list: 指标数据点列表
        """

        def _get() -> list[Any]:
            return self._client.get_metric_history(run_id, metric_name)

        return await asyncio.get_event_loop().run_in_executor(None, _get)


__all__ = ["MLflowService", "MLflowServiceError"]
