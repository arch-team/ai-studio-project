# T037b - Prometheus Pushgateway 部署实施计划

**任务**: T037b [US1] Prometheus Pushgateway 部署 (可选)
**日期**: 2026-01-24
**规范**: tasks.md L497

---

## 任务概述

部署 Prometheus Pushgateway 服务到 EKS 集群，为训练任务提供**实时指标推送**能力，用于即时告警场景。

**注意**: 这是一个"可选"任务，主要用于：
- 实时告警场景（训练任务健康状态实时监控）
- 短生命周期 Job 的指标采集
- 补充 MLflow (T037a) 的 Pull 模式采集能力

### 与 MLflow (T037a) 的职责分离

| 特性 | MLflow (T037a) | Pushgateway (T037b) |
|------|---------------|---------------------|
| **采集模式** | Pull (定期查询) | Push (主动推送) |
| **用途** | 历史查询、停滞检测 | 实时告警、健康监控 |
| **指标类型** | 训练指标 (loss, accuracy) | 系统指标 (GPU util, memory) |
| **保留策略** | 长期存储 | 短期 (Prometheus scrape) |
| **适用场景** | 训练分析、模型比较 | 即时故障检测 |

---

## 实施范围

### 交付物

1. **K8s 部署清单**
   - `infrastructure/k8s/hyperpod-addons/ops/pushgateway-deploy.yaml` - Deployment
   - 更新 `infrastructure/k8s/hyperpod-addons/ops/kustomization.yaml` - 添加资源引用

2. **后端示例代码**
   - `backend/examples/prometheus_metrics_example.py` - SDK 使用示例

3. **配置更新**
   - `backend/src/shared/infrastructure/config.py` - 添加 Pushgateway 配置

4. **文档**
   - 代码内文档和注释

### 不在范围内

- 后端 `PrometheusMetricsService` 服务实现 (可在后续任务中按需实现)
- 后端 API 端点 (无需为 Pushgateway 创建专门的 API)
- 前端组件

---

## TDD 实施流程

### Phase 1: 红灯 - 编写测试

#### 1.1 K8s 资源验证测试

```bash
# 测试文件: infrastructure/k8s/tests/test_pushgateway.sh
# 验证点:
# - pushgateway-deploy.yaml 语法有效
# - Service 端口配置正确 (9091)
# - namespace 正确 (hyperpod-monitoring)
```

#### 1.2 配置验证测试

```python
# backend/tests/unit/test_config_pushgateway.py
def test_settings_has_pushgateway_config():
    """验证 Settings 包含 Pushgateway 配置项"""
    from src.shared.infrastructure.config import Settings
    settings = Settings()
    assert hasattr(settings, 'prometheus_pushgateway_url')
    assert hasattr(settings, 'prometheus_pushgateway_job_name')
```

#### 1.3 示例代码验证测试

```python
# backend/tests/unit/test_prometheus_example.py
def test_prometheus_example_imports():
    """验证示例代码可以正常导入和执行"""
    # 测试 prometheus_client 库可用
    import prometheus_client
    # 测试示例脚本语法正确
    import ast
    with open('backend/examples/prometheus_metrics_example.py') as f:
        ast.parse(f.read())
```

### Phase 2: 绿灯 - 实现功能

#### 2.1 K8s 资源 - pushgateway-deploy.yaml

```yaml
# infrastructure/k8s/hyperpod-addons/ops/pushgateway-deploy.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pushgateway
  namespace: hyperpod-monitoring
  labels:
    app.kubernetes.io/name: pushgateway
    app.kubernetes.io/component: metrics
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: pushgateway
  template:
    metadata:
      labels:
        app.kubernetes.io/name: pushgateway
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9091"
    spec:
      serviceAccountName: prometheus  # 复用现有 SA
      containers:
        - name: pushgateway
          image: prom/pushgateway:v1.8.0
          ports:
            - name: metrics
              containerPort: 9091
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 200m
              memory: 256Mi
          livenessProbe:
            httpGet:
              path: /-/healthy
              port: metrics
            initialDelaySeconds: 10
          readinessProbe:
            httpGet:
              path: /-/ready
              port: metrics
            initialDelaySeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: pushgateway
  namespace: hyperpod-monitoring
  labels:
    app.kubernetes.io/name: pushgateway
spec:
  type: ClusterIP
  ports:
    - name: metrics
      port: 9091
      targetPort: 9091
  selector:
    app.kubernetes.io/name: pushgateway
```

#### 2.2 更新 kustomization.yaml

```yaml
# 在 resources 列表中添加:
resources:
  # ... 现有资源 ...
  # Prometheus Pushgateway (T037b)
  - pushgateway-deploy.yaml
```

#### 2.3 更新 prometheus-config.yaml

```yaml
# 添加 scrape job:
scrape_configs:
  # ... 现有 jobs ...

  # Pushgateway metrics (T037b)
  - job_name: 'pushgateway'
    honor_labels: true  # 保留推送的 labels
    kubernetes_sd_configs:
      - role: endpoints
        namespaces:
          names:
            - hyperpod-monitoring
    relabel_configs:
      - source_labels: [__meta_kubernetes_service_name]
        action: keep
        regex: pushgateway
```

#### 2.4 配置更新 - config.py

```python
# backend/src/shared/infrastructure/config.py
class Settings(BaseSettings):
    # ... 现有配置 ...

    # Prometheus Pushgateway (T037b)
    prometheus_pushgateway_url: str = (
        "http://pushgateway.hyperpod-monitoring.svc.cluster.local:9091"
    )
    prometheus_pushgateway_job_name: str = "training_jobs"
    prometheus_pushgateway_timeout: int = 10  # 秒
```

#### 2.5 示例代码 - prometheus_metrics_example.py

```python
#!/usr/bin/env python3
"""Prometheus 指标推送示例 (T037b)

本示例展示如何在 PyTorch 训练脚本中推送实时指标到 Prometheus Pushgateway，
用于即时告警和系统健康监控。

职责分离:
- MLflow (T037a): 训练指标历史记录 (loss, accuracy) - 用于分析和停滞检测
- Pushgateway (T037b): 系统指标实时推送 (GPU util, memory) - 用于即时告警

适用场景:
- 短生命周期批处理任务的指标采集
- 实时健康状态监控
- GPU/内存使用率告警

环境变量:
- PROMETHEUS_PUSHGATEWAY_URL: Pushgateway 服务地址
- JOB_ID: 训练任务 ID (平台自动设置)

使用方法:
    # 本地测试 (需要运行 Pushgateway)
    docker run -d -p 9091:9091 prom/pushgateway
    export PROMETHEUS_PUSHGATEWAY_URL=http://localhost:9091
    export JOB_ID=12345
    python prometheus_metrics_example.py

    # HyperPod 环境 (平台自动设置环境变量)
    python prometheus_metrics_example.py
"""

import os
import random
import time

from prometheus_client import CollectorRegistry, Gauge, push_to_gateway, delete_from_gateway


def setup_metrics(registry: CollectorRegistry, job_id: str) -> dict:
    """创建指标定义

    Args:
        registry: Prometheus 指标注册表
        job_id: 训练任务 ID

    Returns:
        dict: 指标名称到 Gauge 对象的映射
    """
    # GPU 利用率 (%)
    gpu_utilization = Gauge(
        'training_gpu_utilization_percent',
        'GPU utilization percentage',
        ['job_id', 'gpu_index'],
        registry=registry,
    )

    # GPU 显存使用 (GB)
    gpu_memory_used = Gauge(
        'training_gpu_memory_used_gb',
        'GPU memory used in GB',
        ['job_id', 'gpu_index'],
        registry=registry,
    )

    # 训练吞吐量 (samples/sec)
    throughput = Gauge(
        'training_throughput_samples_per_second',
        'Training throughput in samples per second',
        ['job_id'],
        registry=registry,
    )

    # 训练进度 (epoch)
    current_epoch = Gauge(
        'training_current_epoch',
        'Current training epoch',
        ['job_id'],
        registry=registry,
    )

    # 任务健康状态 (1=healthy, 0=unhealthy)
    health_status = Gauge(
        'training_job_health',
        'Training job health status (1=healthy, 0=unhealthy)',
        ['job_id'],
        registry=registry,
    )

    return {
        'gpu_utilization': gpu_utilization,
        'gpu_memory_used': gpu_memory_used,
        'throughput': throughput,
        'current_epoch': current_epoch,
        'health_status': health_status,
    }


def push_metrics(
    gateway_url: str,
    job_name: str,
    job_id: str,
    registry: CollectorRegistry,
) -> None:
    """推送指标到 Pushgateway

    Args:
        gateway_url: Pushgateway 地址
        job_name: Prometheus job 名称
        job_id: 训练任务 ID (作为 grouping key)
        registry: 指标注册表
    """
    try:
        push_to_gateway(
            gateway_url,
            job=job_name,
            registry=registry,
            grouping_key={'job_id': job_id},
        )
    except Exception as e:
        print(f"警告: 推送指标失败 - {e}")
        # 推送失败不应中断训练


def cleanup_metrics(gateway_url: str, job_name: str, job_id: str) -> None:
    """清理任务对应的指标

    训练完成后调用，避免 stale 指标残留。

    Args:
        gateway_url: Pushgateway 地址
        job_name: Prometheus job 名称
        job_id: 训练任务 ID
    """
    try:
        delete_from_gateway(
            gateway_url,
            job=job_name,
            grouping_key={'job_id': job_id},
        )
        print(f"已清理任务 {job_id} 的指标")
    except Exception as e:
        print(f"警告: 清理指标失败 - {e}")


def simulate_training(
    metrics: dict,
    job_id: str,
    gateway_url: str,
    job_name: str,
    registry: CollectorRegistry,
    epochs: int = 10,
    push_interval: int = 5,  # 秒
):
    """模拟训练过程并推送指标

    Args:
        metrics: 指标对象字典
        job_id: 训练任务 ID
        gateway_url: Pushgateway 地址
        job_name: Prometheus job 名称
        registry: 指标注册表
        epochs: 训练 epoch 数
        push_interval: 指标推送间隔 (秒)
    """
    print(f"\n开始训练模拟 (共 {epochs} 个 epoch)")
    print("-" * 50)

    # 模拟 2 个 GPU
    num_gpus = 2

    for epoch in range(epochs):
        # 设置当前 epoch
        metrics['current_epoch'].labels(job_id=job_id).set(epoch)

        # 模拟 GPU 指标
        for gpu_idx in range(num_gpus):
            gpu_util = 80 + random.uniform(-10, 10)  # 70-90%
            gpu_mem = 10 + random.uniform(-2, 2)     # 8-12 GB

            metrics['gpu_utilization'].labels(
                job_id=job_id, gpu_index=str(gpu_idx)
            ).set(gpu_util)

            metrics['gpu_memory_used'].labels(
                job_id=job_id, gpu_index=str(gpu_idx)
            ).set(gpu_mem)

        # 模拟吞吐量
        throughput = 1000 + random.uniform(-100, 100)  # samples/sec
        metrics['throughput'].labels(job_id=job_id).set(throughput)

        # 模拟健康状态 (95% 概率健康)
        is_healthy = 1 if random.random() > 0.05 else 0
        metrics['health_status'].labels(job_id=job_id).set(is_healthy)

        # 推送指标
        push_metrics(gateway_url, job_name, job_id, registry)

        print(
            f"Epoch {epoch:3d} | "
            f"GPU0: {metrics['gpu_utilization'].labels(job_id=job_id, gpu_index='0')._value.get():.1f}% | "
            f"Throughput: {throughput:.0f} samples/s | "
            f"Health: {'OK' if is_healthy else 'WARN'}"
        )

        time.sleep(push_interval)

    print("-" * 50)
    print("训练模拟完成!")


def main():
    """主函数"""
    # 从环境变量获取配置
    gateway_url = os.getenv(
        'PROMETHEUS_PUSHGATEWAY_URL',
        'http://pushgateway.hyperpod-monitoring.svc.cluster.local:9091'
    )
    job_name = os.getenv('PROMETHEUS_JOB_NAME', 'training_jobs')
    job_id = os.getenv('JOB_ID', 'local-test')

    print(f"Prometheus Pushgateway URL: {gateway_url}")
    print(f"Job Name: {job_name}")
    print(f"Job ID: {job_id}")

    # 创建指标注册表 (每个任务独立)
    registry = CollectorRegistry()
    metrics = setup_metrics(registry, job_id)

    try:
        # 模拟训练并推送指标
        simulate_training(
            metrics=metrics,
            job_id=job_id,
            gateway_url=gateway_url,
            job_name=job_name,
            registry=registry,
            epochs=5,
            push_interval=2,
        )
    finally:
        # 清理指标 (训练完成后)
        cleanup_metrics(gateway_url, job_name, job_id)


if __name__ == "__main__":
    main()
```

### Phase 3: 重构 - 验证和优化

1. **K8s 资源验证**
   ```bash
   # 验证 YAML 语法
   kubectl apply --dry-run=client -f infrastructure/k8s/hyperpod-addons/ops/pushgateway-deploy.yaml

   # 验证 kustomize 构建
   kubectl kustomize infrastructure/k8s/hyperpod-addons/ops/
   ```

2. **后端测试**
   ```bash
   # 运行单元测试
   cd backend
   pytest tests/unit/test_config_pushgateway.py -v
   pytest tests/unit/test_prometheus_example.py -v
   ```

3. **集成验证** (需要 EKS 集群)
   ```bash
   # 部署到集群
   kubectl apply -k infrastructure/k8s/hyperpod-addons/ops/

   # 验证 Pod 运行
   kubectl get pods -n hyperpod-monitoring -l app.kubernetes.io/name=pushgateway

   # 验证 Service
   kubectl get svc -n hyperpod-monitoring pushgateway

   # 测试指标推送
   kubectl run test-push --rm -it --image=curlimages/curl -- \
     curl -X POST "http://pushgateway.hyperpod-monitoring:9091/metrics/job/test" \
     --data "test_metric 1"
   ```

---

## 文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `infrastructure/k8s/hyperpod-addons/ops/pushgateway-deploy.yaml` | 创建 | Pushgateway Deployment + Service |
| `infrastructure/k8s/hyperpod-addons/ops/kustomization.yaml` | 修改 | 添加 pushgateway 资源引用 |
| `infrastructure/k8s/hyperpod-addons/ops/prometheus-config.yaml` | 修改 | 添加 pushgateway scrape job |
| `backend/src/shared/infrastructure/config.py` | 修改 | 添加 Pushgateway 配置项 |
| `backend/examples/prometheus_metrics_example.py` | 创建 | SDK 使用示例 |
| `backend/tests/unit/test_config_pushgateway.py` | 创建 | 配置测试 |
| `backend/tests/unit/test_prometheus_example.py` | 创建 | 示例代码测试 |

---

## 验证清单

### 部署验证

- [ ] Pushgateway Pod 状态为 Running
- [ ] Pushgateway Service 端口 9091 可访问
- [ ] Prometheus 可以 scrape Pushgateway 指标

### 功能验证

- [ ] 示例脚本可以成功推送指标
- [ ] Prometheus 可以查询到推送的指标
- [ ] 训练完成后指标可以被清理

### 配置验证

- [ ] 环境变量 `PROMETHEUS_PUSHGATEWAY_URL` 可配置
- [ ] Settings 类包含所有 Pushgateway 配置项

---

## 风险和注意事项

1. **可选任务**: T037b 是可选任务，如果项目没有实时告警需求，可以跳过
2. **资源消耗**: Pushgateway 是轻量级组件，资源需求小 (100m CPU, 128Mi Memory)
3. **指标清理**: 训练完成后必须清理指标，避免 stale 指标影响告警
4. **与 MLflow 互补**: Pushgateway 用于系统指标，MLflow 用于训练指标，职责互补

---

## 依赖关系

- **前置**: T036 (HyperPod Service) ✅
- **并行**: T037a (MLflow 集成) ✅, T037c (停滞检测) ✅
- **后续**: T038 (Checkpoint 自动保存)

---

## 预估工作量

| 阶段 | 工作量 | 说明 |
|------|--------|------|
| K8s 部署 | 0.5h | YAML 编写和验证 |
| 配置更新 | 0.5h | Settings 类更新 |
| 示例代码 | 1h | prometheus_metrics_example.py |
| 测试 | 0.5h | 单元测试编写 |
| 文档 | 0.5h | 代码注释和文档 |
| **总计** | **3h** | |
