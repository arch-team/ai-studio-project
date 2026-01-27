# Shared External Clients

AWS 外部服务客户端封装。

## CloudWatch Logs 客户端

封装 CloudWatch Logs Insights API，支持训练任务日志查询。

### 使用方式

```python
from datetime import datetime, timedelta, UTC
from src.shared.infrastructure.external import get_cloudwatch_logs_client

# 获取客户端单例
client = get_cloudwatch_logs_client()

# 1. 查询指定训练任务的日志
end_time = datetime.now(UTC)
start_time = end_time - timedelta(hours=1)

logs = await client.query_training_job_logs(
    job_id="job-123",
    start_time=start_time,
    end_time=end_time,
    limit=1000,
)

# 2. 搜索包含关键字的日志
error_logs = await client.search_logs(
    keyword="error",
    start_time=start_time,
    end_time=end_time,
    limit=500,
)

# 3. 自定义 Logs Insights 查询
custom_logs = await client.query_logs(
    query="""
    fields @timestamp, @message, job_id
    | filter log_level = "ERROR"
    | sort @timestamp desc
    """,
    start_time=start_time,
    end_time=end_time,
    limit=100,
)
```

### 配置

- **日志组**: `/aws/hyperpod/training-platform`
- **保留期**: 30 天
- **查询超时**: 30 次重试 (默认 30 秒)

### 依赖注入示例

```python
# modules/training/api/dependencies.py
from src.shared.infrastructure.external import ICloudWatchLogsClient, get_cloudwatch_logs_client

async def get_logs_client() -> ICloudWatchLogsClient:
    return get_cloudwatch_logs_client()

# modules/training/api/endpoints.py
@router.get("/{job_id}/logs")
async def get_job_logs(
    job_id: str,
    logs_client: ICloudWatchLogsClient = Depends(get_logs_client),
):
    logs = await logs_client.query_training_job_logs(job_id, ...)
    return {"logs": logs}
```

### 测试覆盖

- 日志组配置验证
- 查询结果解析（过滤内部字段 `@ptr`）
- AWS API 调用验证
- 轮询重试机制
- 失败/超时处理
- 端到端查询流程

参见: `tests/unit/shared/infrastructure/external/test_cloudwatch_client.py`
