# T037a: SageMaker Managed MLflow 集成 - 实施计划

**任务 ID**: T037a
**任务类型**: HyperPod 集成服务
**优先级**: P1 (US1 - 训练任务管理)
**预估工作量**: 1-1.5 人日
**TDD 流程**: 红灯 → 绿灯 → 重构

---

## 任务概述

实现 SageMaker Managed MLflow 集成服务，为训练任务提供指标查询能力，满足以下需求：
- **T037c 停滞检测服务**需要从 MLflow 查询训练指标 (已实现，等待 IMetricsService 实现)
- **前端监控页面**需要展示训练指标曲线 (T220/T221 依赖)
- **指标记录最佳实践**文档化供用户训练脚本使用

### 核心交付物

| 交付物 | 文件路径 | 说明 |
|--------|---------|------|
| MLflow Service | `backend/src/modules/training/application/services/mlflow_service.py` | 实现 IMetricsService 接口 |
| 单元测试 | `backend/tests/unit/modules/training/application/services/test_mlflow_service.py` | ≥80% 覆盖率 |
| 集成测试 | `backend/tests/integration/test_mlflow_integration.py` | 端到端验证 |
| 示例代码 | `backend/examples/mlflow_training_example.py` | 训练脚本集成示例 |

---

## 技术方案

### 架构设计

```
┌─────────────────────────────────────────────────────────┐
│ StallDetectionService (T037c - 已实现)                   │
│ └─ 依赖: IMetricsService.get_metric_history()           │
└───────────────┬─────────────────────────────────────────┘
                │
                ↓
┌─────────────────────────────────────────────────────────┐
│ MLflowService (T037a - 本任务)                           │
│ ├─ 实现 IMetricsService 接口                             │
│ ├─ get_metric_history(job_id, metric_name, time_range)  │
│ ├─ get_experiment(experiment_name)                      │
│ ├─ list_runs(experiment_id, filters)                    │
│ └─ check_health()                                       │
└───────────────┬─────────────────────────────────────────┘
                │
                ↓ (MLflow Python SDK)
┌─────────────────────────────────────────────────────────┐
│ SageMaker Managed MLflow Tracking Server                │
│ URL: ${MLFLOW_TRACKING_URI}                             │
│ 默认: http://mlflow.kubeflow.svc.cluster.local:5000     │
└─────────────────────────────────────────────────────────┘
```

### 现有接口 (interfaces.py)

```python
# 已定义在 backend/src/modules/training/application/interfaces.py

@dataclass
class MetricPoint:
    timestamp: datetime
    value: float

class IMetricsService(ABC):
    @abstractmethod
    async def get_metric_history(
        self,
        job_id: int,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
    ) -> list[MetricPoint]:
        pass
```

### 任务依赖关系

```
T036 (HyperPod Service) ✅ 已完成
    ↓
T037a (MLflow 集成) ← 本任务
    ↓
T037c (停滞检测) ✅ 已实现，等待 MLflowService
    ↓
T220 (训练指标查询 API) ⏳ 待实现
    ↓
T221 (指标展示组件) ⏳ 待实现
```

---

## TDD 实施步骤

### 阶段 1: 🔴 红灯 - 编写失败测试 (30 min)

#### 1.1 创建单元测试文件

**文件**: `backend/tests/unit/modules/training/application/services/test_mlflow_service.py`

**测试用例清单**:

```python
# 核心功能测试
class TestMLflowServiceGetMetricHistory:
    async def test_returns_metric_points_for_valid_job(self):
        """验证能正确返回指标数据点"""

    async def test_returns_empty_list_when_no_metrics(self):
        """验证无指标时返回空列表"""

    async def test_filters_by_time_range(self):
        """验证时间范围过滤正确"""

    async def test_maps_job_id_to_mlflow_run_id(self):
        """验证 job_id 到 MLflow run_id 的映射"""

# 实验查询测试
class TestMLflowServiceExperiment:
    async def test_get_experiment_by_name_success(self):
        """验证按名称获取实验"""

    async def test_get_experiment_not_found(self):
        """验证实验不存在时抛出异常"""

# 容错测试
class TestMLflowServiceErrorHandling:
    async def test_raises_service_error_when_mlflow_unavailable(self):
        """验证 MLflow 不可用时抛出 ServiceError"""

    async def test_retries_on_transient_error(self):
        """验证瞬时错误时重试"""

    async def test_health_check_returns_false_when_unavailable(self):
        """验证健康检查返回正确状态"""
```

### 阶段 2: 🟢 绿灯 - 实现服务 (2 hours)

#### 2.1 添加 MLflow 依赖

**文件**: `backend/requirements.txt`

```diff
+ # MLflow for experiment tracking
+ mlflow>=2.10.0
```

#### 2.2 扩展配置

**文件**: `backend/src/shared/infrastructure/config.py`

```python
# MLflow Configuration
mlflow_tracking_uri: str = "http://mlflow.kubeflow.svc.cluster.local:5000"
mlflow_experiment_prefix: str = "ai-training-platform"
mlflow_request_timeout: int = 30  # 秒
mlflow_max_retries: int = 3
```

#### 2.3 实现 MLflowService

**文件**: `backend/src/modules/training/application/services/mlflow_service.py`

```python
"""MLflow 集成服务 (T037a)

职责:
- 实现 IMetricsService 接口
- 从 MLflow Tracking Server 查询训练指标
- 为 T037c 停滞检测提供数据源

参考: spec.md L890-979 MLflow 集成方案
"""

from datetime import datetime
from mlflow.tracking import MlflowClient
from mlflow.exceptions import MlflowException

from src.modules.training.application.interfaces import (
    IMetricsService,
    MetricPoint,
)

class MLflowService(IMetricsService):
    """MLflow 指标服务实现"""

    def __init__(
        self,
        tracking_uri: str,
        experiment_prefix: str = "ai-training-platform",
        timeout: int = 30,
        max_retries: int = 3,
    ) -> None:
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
        """从 MLflow 查询指标历史"""
        # 1. 根据 job_id 查找对应的 MLflow run_id
        # 2. 调用 client.get_metric_history(run_id, metric_name)
        # 3. 过滤时间范围
        # 4. 转换为 MetricPoint 列表
        pass

    async def get_experiment(self, experiment_name: str) -> dict:
        """获取实验信息"""
        pass

    async def list_runs(self, experiment_id: str, **filters) -> list[dict]:
        """列出实验下的运行"""
        pass

    async def check_health(self) -> bool:
        """健康检查"""
        pass
```

#### 2.4 添加依赖注入

**文件**: `backend/src/modules/training/api/dependencies.py`

```python
from functools import lru_cache
from src.modules.training.application.services.mlflow_service import MLflowService

@lru_cache(maxsize=1)
def get_mlflow_service() -> MLflowService:
    """Singleton MLflowService instance."""
    settings = get_settings()
    return MLflowService(
        tracking_uri=settings.mlflow_tracking_uri,
        experiment_prefix=settings.mlflow_experiment_prefix,
        timeout=settings.mlflow_request_timeout,
        max_retries=settings.mlflow_max_retries,
    )
```

#### 2.5 更新服务 __init__.py

**文件**: `backend/src/modules/training/application/services/__init__.py`

```python
from .mlflow_service import MLflowService

__all__ = [
    # ... existing exports
    "MLflowService",
]
```

### 阶段 3: 🔄 重构 - 优化代码 (30 min)

- 提取 job_id 到 run_id 映射逻辑
- 添加结构化日志 (structlog)
- 优化错误消息本地化
- 完善类型注解

### 阶段 4: 集成测试 (30 min)

**文件**: `backend/tests/integration/test_mlflow_integration.py`

```python
"""MLflow 集成测试

需要运行 MLflow 服务: docker-compose up mlflow
"""
import pytest

@pytest.mark.integration
@pytest.mark.skipif(not mlflow_available(), reason="MLflow service not available")
class TestMLflowIntegration:
    async def test_end_to_end_metric_query(self):
        """端到端指标查询测试"""

    async def test_service_degradation_when_unavailable(self):
        """服务不可用时的降级处理"""
```

### 阶段 5: 示例代码和文档 (30 min)

#### 5.1 创建示例目录

```bash
mkdir -p backend/examples
```

#### 5.2 创建示例代码

**文件**: `backend/examples/mlflow_training_example.py`

```python
"""MLflow 训练指标记录示例 (T037a)

本示例展示如何在 PyTorch 训练脚本中集成 MLflow。

指标命名规范:
- 损失函数: loss, train_loss, val_loss
- 准确率: accuracy, train_accuracy, val_accuracy
- 学习率: learning_rate, lr
- 吞吐量: throughput, samples_per_second

记录频率建议:
- 训练损失: 每 100 steps
- 验证指标: 每 epoch
- 学习率: 调度器更新时

环境变量:
- MLFLOW_TRACKING_URI: MLflow 服务地址
- MLFLOW_EXPERIMENT_NAME: 实验名称

使用方法:
    export MLFLOW_TRACKING_URI=http://mlflow:5000
    python mlflow_training_example.py
"""

import os
import mlflow
import mlflow.pytorch
import torch
import torch.nn as nn

def main():
    # 配置 MLflow
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
    mlflow.set_experiment(os.getenv("MLFLOW_EXPERIMENT_NAME", "ai-training-platform/demo"))

    with mlflow.start_run():
        # 记录超参数
        mlflow.log_params({
            "learning_rate": 0.001,
            "batch_size": 32,
            "epochs": 10,
            "optimizer": "Adam",
        })

        # 模拟训练循环
        for epoch in range(10):
            train_loss = 1.0 / (epoch + 1)  # 模拟递减的 loss
            train_accuracy = 0.5 + epoch * 0.05  # 模拟递增的 accuracy

            # 记录指标 (step=epoch)
            mlflow.log_metrics({
                "train_loss": train_loss,
                "train_accuracy": train_accuracy,
            }, step=epoch)

            print(f"Epoch {epoch}: loss={train_loss:.4f}, accuracy={train_accuracy:.4f}")

        # 记录模型 (可选)
        # model = MyModel()
        # mlflow.pytorch.log_model(model, "model")

        print("Training completed. Run ID:", mlflow.active_run().info.run_id)

if __name__ == "__main__":
    main()
```

---

## 文件清单

| 文件路径 | 操作 | 说明 |
|---------|------|------|
| `backend/requirements.txt` | 修改 | 添加 `mlflow>=2.10.0` |
| `backend/src/shared/infrastructure/config.py` | 修改 | 添加 MLflow 配置项 |
| `backend/src/modules/training/application/services/mlflow_service.py` | 创建 | MLflow 服务实现 |
| `backend/src/modules/training/application/services/__init__.py` | 修改 | 导出 MLflowService |
| `backend/src/modules/training/api/dependencies.py` | 修改 | 添加 `get_mlflow_service()` |
| `backend/tests/unit/modules/training/application/services/test_mlflow_service.py` | 创建 | 单元测试 |
| `backend/tests/integration/test_mlflow_integration.py` | 创建 | 集成测试 |
| `backend/examples/mlflow_training_example.py` | 创建 | 示例代码 |

---

## 验证命令

### 1. 运行单元测试
```bash
cd backend
pytest tests/unit/modules/training/application/services/test_mlflow_service.py -v
```

### 2. 检查测试覆盖率
```bash
pytest tests/unit/modules/training/application/services/test_mlflow_service.py --cov=src/modules/training/application/services/mlflow_service --cov-report=term-missing
```

### 3. 代码质量检查
```bash
black src/modules/training/application/services/mlflow_service.py
ruff check src/modules/training/application/services/mlflow_service.py
mypy src/modules/training/application/services/mlflow_service.py
```

### 4. 运行集成测试 (需要 MLflow 服务)
```bash
# 启动 MLflow (如果有 docker-compose)
# docker-compose up -d mlflow

pytest tests/integration/test_mlflow_integration.py -v -m integration
```

### 5. 验证示例代码
```bash
# 需要 MLflow 服务运行
cd backend/examples
python mlflow_training_example.py
```

---

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| MLflow 服务不可用 | 指标查询失败 | 实现重试机制 + 健康检查 |
| job_id 与 run_id 映射缺失 | 无法查询指标 | 在训练任务提交时记录映射关系 |
| 网络延迟 | 查询超时 | 配置合理超时 (30s) + 异步查询 |

---

## 完成标志

- [ ] 单元测试全部通过 (≥80% 覆盖率)
- [ ] 代码质量检查通过 (black, ruff, mypy)
- [ ] 示例代码可运行
- [ ] 集成测试通过 (可选，依赖 MLflow 服务)
- [ ] 更新 `specs/001-ai-training-platform/tasks.md` 标记 T037a 为 `[X]`
