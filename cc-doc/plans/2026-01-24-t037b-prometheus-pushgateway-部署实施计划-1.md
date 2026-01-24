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

创建 `backend/examples/prometheus_metrics_example.py`，包含：
- `setup_metrics()` - 创建指标定义
- `push_metrics()` - 推送指标到 Pushgateway
- `cleanup_metrics()` - 清理任务指标
- `simulate_training()` - 模拟训练过程
- `main()` - 主函数

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
| `backend/tests/unit/shared/test_config_pushgateway.py` | 创建 | 配置测试 |
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
