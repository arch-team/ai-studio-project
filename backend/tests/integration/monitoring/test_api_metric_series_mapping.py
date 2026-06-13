"""指标趋势端点语义指标名映射集成测试 - TDD Red-Green-Refactor。

修复真实端到端裂缝：前端「指标趋势」Tab 传业务语义指标名
（cpu_utilization / memory_utilization / gpu_utilization），后端
GET /api/v1/monitoring/metrics 须把这些语义名映射为真实 PromQL 再查 AMP，
否则字面量当 PromQL 查不到任何数据 → 折线图恒为空。

断言要点：
1. 传语义名时，query_metrics 收到的是真实 PromQL（而非字面 cpu_utilization）。
2. 响应 MetricSeries.metric_name 仍为前端传入的语义名（图表 label 正确）。
3. 未知名（如直接传 DCGM_FI_DEV_GPU_UTIL）原样当 PromQL（向后兼容）。
"""

from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from src.main import app
from src.modules.monitoring.api.dependencies import get_prometheus_service
from src.modules.monitoring.application.services.prometheus_service import (
    _UTILIZATION_QUERIES,
    MetricDataPoint,
)
from src.shared.utils import utc_now


def _make_service_returning(metric_to_points: dict[str, list[MetricDataPoint]]) -> AsyncMock:
    """构造一个 mock PrometheusService，query_metrics 回显传入的 metric_names。

    回显语义：query_metrics 返回 dict 的 key 为传入的 metric_names（PromQL），
    与真实 PrometheusService.query_metrics 行为一致（key=查询字符串）。
    """
    svc = AsyncMock()

    async def _query_metrics(metric_names: list[str], start_time, end_time, step="1m"):  # type: ignore[no-untyped-def]
        return {name: metric_to_points.get(name, []) for name in metric_names}

    svc.query_metrics = AsyncMock(side_effect=_query_metrics)
    return svc


class TestMetricSeriesSemanticMapping:
    """GET /api/v1/monitoring/metrics 语义指标名 → 真实 PromQL 映射。"""

    @pytest.mark.asyncio
    async def test_semantic_names_mapped_to_real_promql(
        self, client: AsyncClient, engineer_auth_headers: dict[str, str]
    ) -> None:
        """传 cpu/memory/gpu_utilization 时，query_metrics 收到真实 PromQL。"""
        svc = _make_service_returning({})
        app.dependency_overrides[get_prometheus_service] = lambda: svc
        try:
            resp = await client.get(
                "/api/v1/monitoring/metrics",
                params={"metric_names": "cpu_utilization,memory_utilization,gpu_utilization"},
                headers=engineer_auth_headers,
            )
            assert resp.status_code == 200

            # query_metrics 必须被调用，且收到的是真实 PromQL 而非字面语义名
            svc.query_metrics.assert_called_once()
            passed_names = svc.query_metrics.call_args.kwargs["metric_names"]
            assert _UTILIZATION_QUERIES["cpu"] in passed_names
            assert _UTILIZATION_QUERIES["memory"] in passed_names
            assert _UTILIZATION_QUERIES["gpu"] in passed_names
            # 字面语义名不应作为 PromQL 传入
            assert "cpu_utilization" not in passed_names
            assert "gpu_utilization" not in passed_names
        finally:
            app.dependency_overrides.pop(get_prometheus_service, None)

    @pytest.mark.asyncio
    async def test_response_metric_name_keeps_semantic_label(
        self, client: AsyncClient, engineer_auth_headers: dict[str, str]
    ) -> None:
        """响应 metric_name 仍为前端语义名，且携带真实数据点。"""
        now = utc_now()
        # mock 让 cpu/memory/gpu 的真实 PromQL 各返回一个非空数据点
        svc = _make_service_returning(
            {
                _UTILIZATION_QUERIES["cpu"]: [MetricDataPoint(timestamp=now, value=45.0)],
                _UTILIZATION_QUERIES["memory"]: [MetricDataPoint(timestamp=now, value=60.0)],
                _UTILIZATION_QUERIES["gpu"]: [MetricDataPoint(timestamp=now, value=30.0)],
            }
        )
        app.dependency_overrides[get_prometheus_service] = lambda: svc
        try:
            resp = await client.get(
                "/api/v1/monitoring/metrics",
                params={"metric_names": "cpu_utilization,memory_utilization,gpu_utilization"},
                headers=engineer_auth_headers,
            )
            assert resp.status_code == 200
            series = resp.json()
            by_name = {s["metric_name"]: s for s in series}

            # 响应 key 是语义名（前端图表 label 正确），非 PromQL
            assert set(by_name) == {"cpu_utilization", "memory_utilization", "gpu_utilization"}
            # 每条序列携带非空数据点（折线图不再「暂无数据」）
            assert by_name["cpu_utilization"]["data_points"][0]["value"] == 45.0
            assert by_name["memory_utilization"]["data_points"][0]["value"] == 60.0
            assert by_name["gpu_utilization"]["data_points"][0]["value"] == 30.0
        finally:
            app.dependency_overrides.pop(get_prometheus_service, None)

    @pytest.mark.asyncio
    async def test_unknown_metric_name_passed_through_as_promql(
        self, client: AsyncClient, engineer_auth_headers: dict[str, str]
    ) -> None:
        """未在映射表的名字（裸 PromQL）原样透传，保持向后兼容。"""
        svc = _make_service_returning({})
        app.dependency_overrides[get_prometheus_service] = lambda: svc
        try:
            resp = await client.get(
                "/api/v1/monitoring/metrics",
                params={"metric_names": "DCGM_FI_DEV_GPU_UTIL"},
                headers=engineer_auth_headers,
            )
            assert resp.status_code == 200

            svc.query_metrics.assert_called_once()
            passed_names = svc.query_metrics.call_args.kwargs["metric_names"]
            # 裸 PromQL 原样传入，不被改写
            assert passed_names == ["DCGM_FI_DEV_GPU_UTIL"]
            # 响应 metric_name 仍为原始传入名
            series = resp.json()
            assert series[0]["metric_name"] == "DCGM_FI_DEV_GPU_UTIL"
        finally:
            app.dependency_overrides.pop(get_prometheus_service, None)

    @pytest.mark.asyncio
    async def test_default_names_unchanged_when_no_metric_names(
        self, client: AsyncClient, engineer_auth_headers: dict[str, str]
    ) -> None:
        """不传 metric_names 时默认行为不变（仍用真实指标名作 PromQL）。"""
        svc = _make_service_returning({})
        app.dependency_overrides[get_prometheus_service] = lambda: svc
        try:
            resp = await client.get(
                "/api/v1/monitoring/metrics",
                headers=engineer_auth_headers,
            )
            assert resp.status_code == 200

            svc.query_metrics.assert_called_once()
            passed_names = svc.query_metrics.call_args.kwargs["metric_names"]
            # 默认指标名是真实指标名，保持原样
            assert "DCGM_FI_DEV_GPU_UTIL" in passed_names
        finally:
            app.dependency_overrides.pop(get_prometheus_service, None)
