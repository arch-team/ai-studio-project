"""CloudWatch Logs 客户端单元测试 (T073)."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.shared.infrastructure.external.cloudwatch_client import CloudWatchLogsClient


@pytest.fixture
def cloudwatch_client():
    """创建 CloudWatch Logs 客户端实例."""
    return CloudWatchLogsClient()


@pytest.fixture
def mock_logs_client():
    """创建 Mock CloudWatch Logs 客户端."""
    client = MagicMock()
    # 配置异步上下文管理器
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    return client


@pytest.fixture
def sample_query_results():
    """生成示例查询结果."""
    return [
        [
            {"field": "@timestamp", "value": "2024-01-27 10:00:00"},
            {"field": "@message", "value": "Training started"},
            {"field": "job_id", "value": "job-123"},
            {"field": "@ptr", "value": "internal-pointer"},  # 应被过滤
        ],
        [
            {"field": "@timestamp", "value": "2024-01-27 10:05:00"},
            {"field": "@message", "value": "Training completed"},
            {"field": "job_id", "value": "job-123"},
        ],
    ]


@pytest.fixture
def sample_parsed_results():
    """期望的解析结果."""
    return [
        {
            "@timestamp": "2024-01-27 10:00:00",
            "@message": "Training started",
            "job_id": "job-123",
        },
        {
            "@timestamp": "2024-01-27 10:05:00",
            "@message": "Training completed",
            "job_id": "job-123",
        },
    ]


class TestCloudWatchLogsClient:
    """CloudWatch Logs 客户端测试."""

    def test_log_group_configuration(self, cloudwatch_client):
        """验证日志组配置."""
        assert cloudwatch_client.LOG_GROUP_NAME == "/aws/hyperpod/training-platform"
        assert cloudwatch_client.RETENTION_DAYS == 30

    def test_parse_results_filters_internal_fields(
        self, cloudwatch_client, sample_query_results, sample_parsed_results
    ):
        """验证 _parse_results 过滤内部字段 (@ptr)."""
        parsed = cloudwatch_client._parse_results(sample_query_results)
        assert parsed == sample_parsed_results
        assert all("@ptr" not in result for result in parsed)

    def test_parse_results_empty_input(self, cloudwatch_client):
        """验证空输入处理."""
        parsed = cloudwatch_client._parse_results([])
        assert parsed == []

    @pytest.mark.asyncio
    async def test_start_query_calls_aws_api(self, cloudwatch_client, mock_logs_client):
        """验证 _start_query 调用 AWS API."""
        mock_logs_client.start_query = AsyncMock(return_value={"queryId": "query-123"})

        with patch.object(cloudwatch_client, "_get_logs_client", return_value=mock_logs_client):
            start_time = datetime(2024, 1, 27, 10, 0, 0, tzinfo=UTC)
            end_time = datetime(2024, 1, 27, 11, 0, 0, tzinfo=UTC)
            query_string = "fields @timestamp, @message"

            query_id = await cloudwatch_client._start_query(query_string, start_time, end_time, 1000)

            assert query_id == "query-123"
            mock_logs_client.start_query.assert_called_once_with(
                logGroupName="/aws/hyperpod/training-platform",
                startTime=int(start_time.timestamp()),
                endTime=int(end_time.timestamp()),
                queryString=query_string,
                limit=1000,
            )

    @pytest.mark.asyncio
    async def test_get_query_results_success(
        self, cloudwatch_client, mock_logs_client, sample_query_results, sample_parsed_results
    ):
        """验证 _get_query_results 成功获取结果."""
        mock_logs_client.get_query_results = AsyncMock(
            return_value={"status": "Complete", "results": sample_query_results}
        )

        with patch.object(cloudwatch_client, "_get_logs_client", return_value=mock_logs_client):
            results = await cloudwatch_client._get_query_results("query-123")

            assert results == sample_parsed_results
            mock_logs_client.get_query_results.assert_called_once_with(queryId="query-123")

    @pytest.mark.asyncio
    async def test_get_query_results_retries_until_complete(
        self, cloudwatch_client, mock_logs_client, sample_query_results
    ):
        """验证 _get_query_results 轮询直到完成."""
        mock_logs_client.get_query_results = AsyncMock(
            side_effect=[
                {"status": "Running"},
                {"status": "Running"},
                {"status": "Complete", "results": sample_query_results},
            ]
        )

        with patch.object(cloudwatch_client, "_get_logs_client", return_value=mock_logs_client):
            results = await cloudwatch_client._get_query_results("query-123", max_retries=5, retry_interval=0.01)

            assert len(results) == 2
            assert mock_logs_client.get_query_results.call_count == 3

    @pytest.mark.asyncio
    async def test_get_query_results_failed_status(self, cloudwatch_client, mock_logs_client):
        """验证查询失败时抛出异常."""
        mock_logs_client.get_query_results = AsyncMock(return_value={"status": "Failed"})

        with patch.object(cloudwatch_client, "_get_logs_client", return_value=mock_logs_client):
            with pytest.raises(RuntimeError, match="查询失败: Failed"):
                await cloudwatch_client._get_query_results("query-123")

    @pytest.mark.asyncio
    async def test_get_query_results_timeout(self, cloudwatch_client, mock_logs_client):
        """验证查询超时处理."""
        mock_logs_client.get_query_results = AsyncMock(return_value={"status": "Running"})

        with patch.object(cloudwatch_client, "_get_logs_client", return_value=mock_logs_client):
            with pytest.raises(TimeoutError, match="查询超时"):
                await cloudwatch_client._get_query_results("query-123", max_retries=3, retry_interval=0.01)

    @pytest.mark.asyncio
    async def test_query_training_job_logs_generates_correct_query(self, cloudwatch_client):
        """验证 query_training_job_logs 生成正确的查询语句."""
        with patch.object(cloudwatch_client, "query_logs", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = []
            start_time = datetime(2024, 1, 27, 10, 0, 0, tzinfo=UTC)
            end_time = datetime(2024, 1, 27, 11, 0, 0, tzinfo=UTC)

            await cloudwatch_client.query_training_job_logs("job-123", start_time, end_time, limit=500)

            args, kwargs = mock_query.call_args
            query = args[0]
            assert 'filter job_id = "job-123"' in query
            assert "fields @timestamp, @message" in query
            assert "sort @timestamp desc" in query
            assert "limit 500" in query

    @pytest.mark.asyncio
    async def test_search_logs_generates_correct_query(self, cloudwatch_client):
        """验证 search_logs 生成正确的搜索查询."""
        with patch.object(cloudwatch_client, "query_logs", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = []
            start_time = datetime(2024, 1, 27, 10, 0, 0, tzinfo=UTC)
            end_time = datetime(2024, 1, 27, 11, 0, 0, tzinfo=UTC)

            await cloudwatch_client.search_logs("error", start_time, end_time, limit=100)

            args, kwargs = mock_query.call_args
            query = args[0]
            assert "filter @message like /error/" in query
            assert "fields @timestamp, @message, job_id" in query
            assert "limit 100" in query

    @pytest.mark.asyncio
    async def test_query_logs_integration(self, cloudwatch_client, mock_logs_client, sample_query_results):
        """验证 query_logs 端到端流程."""
        mock_logs_client.start_query = AsyncMock(return_value={"queryId": "query-123"})
        mock_logs_client.get_query_results = AsyncMock(
            return_value={"status": "Complete", "results": sample_query_results}
        )

        with patch.object(cloudwatch_client, "_get_logs_client", return_value=mock_logs_client):
            start_time = datetime(2024, 1, 27, 10, 0, 0, tzinfo=UTC)
            end_time = datetime(2024, 1, 27, 11, 0, 0, tzinfo=UTC)

            results = await cloudwatch_client.query_logs("fields @timestamp", start_time, end_time, 1000)

            assert len(results) == 2
            assert results[0]["job_id"] == "job-123"
            assert "@ptr" not in results[0]
