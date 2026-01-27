# Cost Explorer Client 使用指南

## 概述

`CostExplorerClient` 是 AWS Cost Explorer API 的异步封装，提供成本数据查询能力。

## 功能特性

- 使用 `aioboto3` 进行异步 AWS 调用
- 支持按时间范围、服务类型、资源标签查询成本数据
- 单例模式，避免重复创建客户端
- 支持缓存策略 (通过 lru_cache 实现)

## 使用示例

### 基本用法

```python
from datetime import datetime
from src.modules.billing.infrastructure.external import get_cost_explorer_client

# 获取客户端单例
client = get_cost_explorer_client()

# 查询月度成本
result = await client.get_cost_and_usage(
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 1, 31),
    granularity='MONTHLY'
)

print(result['ResultsByTime'][0]['Total']['UnblendedCost']['Amount'])
```

### 按服务分组

```python
# 查询各服务成本
result = await client.get_cost_and_usage(
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 1, 31),
    granularity='MONTHLY',
    group_by=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
)

for group in result['ResultsByTime'][0]['Groups']:
    service = group['Keys'][0]
    cost = group['Metrics']['UnblendedCost']['Amount']
    print(f"{service}: ${cost}")
```

### 按标签过滤

```python
# 查询特定项目的成本
result = await client.get_cost_and_usage(
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 1, 31),
    granularity='MONTHLY',
    filter_tags={
        'project': 'ml-training',
        'env': 'production'
    }
)
```

### 查询日度成本

```python
# 查询每日成本趋势
result = await client.get_cost_and_usage(
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 1, 31),
    granularity='DAILY'
)

for day_data in result['ResultsByTime']:
    date = day_data['TimePeriod']['Start']
    cost = day_data['Total']['UnblendedCost']['Amount']
    print(f"{date}: ${cost}")
```

## API 参考

### get_cost_and_usage

```python
async def get_cost_and_usage(
    start_date: datetime,
    end_date: datetime,
    granularity: str = "MONTHLY",
    metrics: list[str] | None = None,
    group_by: list[dict[str, str]] | None = None,
    filter_tags: dict[str, str] | None = None,
) -> dict[str, Any]
```

**参数说明**:

- `start_date`: 查询起始日期
- `end_date`: 查询结束日期
- `granularity`: 时间粒度 (`DAILY`, `MONTHLY`, `HOURLY`)
- `metrics`: 指标列表 (默认: `['UnblendedCost']`)
- `group_by`: 分组维度 (如: `[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]`)
- `filter_tags`: 按标签过滤 (如: `{'project': 'ml-training'}`)

**返回值**:

Cost Explorer API 返回的成本数据结构，包含 `ResultsByTime` 数组。

## 架构说明

### 接口定义

`ICostExplorerClient` 定义在 `application/interfaces/cost_explorer_client.py`，符合 Clean Architecture 的依赖倒置原则。

### 实现类

`CostExplorerClient` 实现在 `infrastructure/external/cost_explorer_client.py`，使用 `aioboto3` 进行异步调用。

### 单例模式

通过 `@lru_cache(maxsize=1)` 装饰 `get_cost_explorer_client()` 函数实现单例模式。

## 测试

单元测试位于 `tests/unit/modules/billing/test_cost_explorer_client.py`，包含:

- 接口契约测试
- 基本功能测试
- 标签过滤测试
- 服务分组测试
- 日期格式转换测试
- 单例模式测试

运行测试:

```bash
pytest tests/unit/modules/billing/test_cost_explorer_client.py -v
```

## 注意事项

1. 需要配置 AWS 凭证 (通过环境变量或 `~/.aws/credentials`)
2. IAM 角色需要 `ce:GetCostAndUsage` 权限
3. Cost Explorer API 有速率限制，建议实现缓存策略
4. 日期格式自动转换为 `YYYY-MM-DD` 格式
5. 多标签过滤使用 AND 逻辑
