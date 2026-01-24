# HyperPodClient 缺失方法实现计划

> **任务**: 为 E2E 测试补充 HyperPodClient 缺失方法
> **AWS Region**: us-east-1
> **SDK 优先级**: sagemaker-hyperpod SDK 3.5.0
> **状态**: ✅ 实现完成 + 状态同步修复

---

## 0. 状态同步问题修复 (2026-01-24 新增)

### 问题描述
E2E 测试中发现 `job.status` 始终为 None，`refresh()` 方法抛出 KeyError: 'status'。

### 根本原因
HyperPod SDK 在执行训练任务操作前需要先调用 `set_cluster_context()` 配置 kubeconfig，否则 SDK 无法与 Kubernetes API 交互。

### 解决方案

1. **添加 `set_cluster_context` 导入**:
```python
try:
    from sagemaker.hyperpod import set_cluster_context
except ImportError:
    set_cluster_context = None
```

2. **添加集群上下文管理**:
```python
# 类级别缓存
_cluster_contexts: set[str] = set()

def _ensure_cluster_context(self, cluster_name: str | None = None) -> None:
    """确保集群上下文已设置"""
    target_cluster = cluster_name or self._default_cluster_name
    if target_cluster in self._cluster_contexts:
        return
    set_cluster_context(target_cluster)
    self._cluster_contexts.add(target_cluster)
```

3. **构造函数支持默认集群**:
```python
def __init__(
    self,
    region: str = "us-east-1",
    default_cluster_name: str | None = None,
) -> None:
```

4. **在所有 SDK 操作前调用上下文检查**:
- `submit_training_job()`
- `get_training_job_status()`
- `stop_training_job()`
- `list_training_job_pods()`
- `get_pod_status()`
- `resume_training_job()`
- `trigger_preemption()`

### 单元测试
新增 6 个测试用例验证集群上下文功能：
- `test_client_accepts_default_cluster_name`
- `test_ensure_cluster_context_called_on_submit`
- `test_ensure_cluster_context_called_on_get_status`
- `test_cluster_context_cached_across_calls`
- `test_cluster_context_set_for_each_cluster`
- `test_ensure_cluster_context_uses_default_if_no_cluster_provided`

**测试结果**: 37 passed ✅

---

## 1. 背景

E2E 测试 (`tests/e2e/aws/test_e2e_preemption_sla.py`) 需要以下方法，但当前 `HyperPodClient` 未实现：

| 方法 | E2E 测试场景 | 实现策略 |
|------|-------------|---------|
| `trigger_preemption` | 触发抢占测试 | Kueue Workload API |
| `list_checkpoints` | 验证检查点保存 | S3 + 数据库查询 |
| `verify_checkpoint_exists` | 验证检查点存在 | S3 API |
| `get_pod_status` | 验证 Pod 释放 | HyperPod SDK |
| `resume_training_job` | 抢占后恢复 | HyperPodPytorchJob |
| `cancel_training_job` | 清理测试资源 | 别名 stop_training_job |
| `get_job_pods` | 获取 Pod 列表 | 别名 list_training_job_pods |

---

## 2. 实现计划

### 2.1 修改 Region 默认值

**文件**: `src/modules/training/infrastructure/hyperpod/client.py:37`

```python
# Before
def __init__(self, region: str = "us-west-2") -> None:

# After
def __init__(self, region: str = "us-east-1") -> None:
```

---

### 2.2 新增方法实现

#### 方法 1: `cancel_training_job` (别名)

```python
async def cancel_training_job(self, job_id: str) -> dict[str, Any]:
    """取消训练任务 (stop_training_job 的别名)"""
    return await self.stop_training_job(cluster_name="", job_name=job_id)
```

#### 方法 2: `get_job_pods` (别名)

```python
async def get_job_pods(self, job_id: str) -> list[dict[str, Any]]:
    """获取任务 Pod 列表 (list_training_job_pods 的别名)"""
    return await self.list_training_job_pods(cluster_name="", job_name=job_id)
```

#### 方法 3: `get_pod_status`

**实现策略**: 通过 HyperPod SDK `list_pods()` 过滤特定 Pod

```python
async def get_pod_status(
    self, cluster_name: str, job_name: str, pod_name: str
) -> dict[str, Any]:
    """获取单个 Pod 状态"""
    def _get_status() -> dict[str, Any]:
        if HyperPodPytorchJob is None:
            raise RuntimeError("HyperPod SDK not available")

        job = HyperPodPytorchJob.get(name=job_name)
        pods = job.list_pods()

        for pod in pods:
            if pod.get("name") == pod_name:
                return {
                    "name": pod_name,
                    "phase": pod.get("phase", "Unknown"),
                    "status": pod.get("status", {}),
                }

        raise ValueError(f"Pod {pod_name} not found")

    return await self._run_in_executor(_get_status)
```

#### 方法 4: `verify_checkpoint_exists`

**实现策略**: 使用 boto3 S3 head_object 检查文件存在

```python
async def verify_checkpoint_exists(self, s3_path: str) -> bool:
    """验证 S3 检查点文件是否存在

    Args:
        s3_path: S3 路径, 格式 s3://bucket/key
    """
    def _check_exists() -> bool:
        import re
        match = re.match(r"s3://([^/]+)/(.+)", s3_path)
        if not match:
            raise ValueError(f"Invalid S3 path: {s3_path}")

        bucket, key = match.groups()
        s3_client = boto3.client("s3", region_name=self._region)

        try:
            s3_client.head_object(Bucket=bucket, Key=key)
            return True
        except s3_client.exceptions.ClientError:
            return False

    return await self._run_in_executor(_check_exists)
```

#### 方法 5: `list_checkpoints`

**实现策略**: S3 list_objects_v2 + 检查点路径前缀

```python
async def list_checkpoints(
    self, job_id: str, checkpoint_base_path: str
) -> list[dict[str, Any]]:
    """列出任务的所有检查点

    Args:
        job_id: 训练任务 ID
        checkpoint_base_path: 检查点 S3 基础路径 (s3://bucket/prefix)
    """
    def _list() -> list[dict[str, Any]]:
        import re
        match = re.match(r"s3://([^/]+)/(.+)", checkpoint_base_path)
        if not match:
            return []

        bucket, prefix = match.groups()
        s3_client = boto3.client("s3", region_name=self._region)

        # 构造检查点目录前缀
        checkpoint_prefix = f"{prefix.rstrip('/')}/{job_id}/"

        response = s3_client.list_objects_v2(
            Bucket=bucket,
            Prefix=checkpoint_prefix,
        )

        checkpoints = []
        for obj in response.get("Contents", []):
            checkpoints.append({
                "key": obj["Key"],
                "size": obj["Size"],
                "last_modified": obj["LastModified"].isoformat(),
                "etag": obj["ETag"],
            })

        return checkpoints

    return await self._run_in_executor(_list)
```

#### 方法 6: `resume_training_job`

**实现策略**: 使用 HyperPodPytorchJob 重新创建任务，指定检查点路径

```python
async def resume_training_job(
    self,
    cluster_name: str,
    job_name: str,
    checkpoint_path: str | None = None,
    job_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """从检查点恢复训练任务

    Args:
        cluster_name: 集群名称
        job_name: 新任务名称
        checkpoint_path: 检查点 S3 路径
        job_config: 任务配置 (复用原任务配置)
    """
    def _resume() -> dict[str, Any]:
        if HyperPodPytorchJob is None:
            raise RuntimeError("HyperPod SDK not available")

        if job_config is None:
            raise ValueError("job_config is required for resume")

        # 添加检查点恢复环境变量
        env = job_config.get("environment", {}).copy()
        if checkpoint_path:
            env["CHECKPOINT_PATH"] = checkpoint_path
            env["RESUME_FROM_CHECKPOINT"] = "true"

        job = HyperPodPytorchJob(
            name=job_name,
            image_uri=job_config.get("image_uri"),
            instance_type=job_config.get("instance_type"),
            node_count=job_config.get("node_count", 1),
            tasks_per_node=job_config.get("tasks_per_node", 1),
            command=job_config.get("command"),
            environment=env,
            volumes=job_config.get("volumes"),
        )
        job.create()

        return {
            "job_name": job.name,
            "status": _map_status(job.status),
            "cluster_name": cluster_name,
            "checkpoint_path": checkpoint_path,
            "resumed": True,
        }

    return await self._run_in_executor(_resume)
```

#### 方法 7: `trigger_preemption`

**实现策略**: 通过提交高优先级任务间接触发 Kueue 抢占机制 ✅ 用户确认

> **原理**: Kueue 的抢占机制基于优先级。当资源不足时，高优先级任务会触发低优先级任务的抢占。

```python
async def trigger_preemption(
    self,
    cluster_name: str,
    target_job_name: str,
    preemption_job_config: dict[str, Any],
) -> dict[str, Any]:
    """通过提交高优先级任务触发抢占

    工作原理:
    1. 获取目标任务的资源占用信息
    2. 提交一个 critical 优先级的任务抢占资源
    3. Kueue 自动触发低优先级任务的 preemption
    4. 返回高优先级任务信息和抢占状态

    Args:
        cluster_name: 集群名称
        target_job_name: 要被抢占的低优先级任务名称
        preemption_job_config: 高优先级任务配置 (必须包含 priority="critical")
    """
    def _trigger() -> dict[str, Any]:
        if HyperPodPytorchJob is None:
            raise RuntimeError("HyperPod SDK not available")

        # 验证目标任务存在
        target_job = HyperPodPytorchJob.get(name=target_job_name)
        if target_job.status != "Running":
            raise ValueError(f"Target job {target_job_name} is not running")

        # 生成高优先级任务名称
        import time
        preemption_job_name = f"preempt-{target_job_name}-{int(time.time())}"

        # 确保高优先级配置
        env = preemption_job_config.get("environment", {}).copy()
        env["KUEUE_PRIORITY_CLASS"] = "critical"

        # 提交高优先级任务
        preemption_job = HyperPodPytorchJob(
            name=preemption_job_name,
            image_uri=preemption_job_config.get("image_uri"),
            instance_type=preemption_job_config.get("instance_type"),
            node_count=preemption_job_config.get("node_count", 1),
            command=preemption_job_config.get("command"),
            environment=env,
        )
        preemption_job.create()

        return {
            "target_job_name": target_job_name,
            "preemption_job_name": preemption_job_name,
            "preemption_job_status": _map_status(preemption_job.status),
            "mechanism": "high_priority_task",
        }

    return await self._run_in_executor(_trigger)
```

---

### 2.3 更新接口定义

**文件**: `src/modules/training/application/interfaces.py`

在 `IHyperPodClient` 类中添加新方法签名：

```python
@abstractmethod
async def cancel_training_job(self, job_id: str) -> dict[str, Any]:
    """取消训练任务"""

@abstractmethod
async def get_job_pods(self, job_id: str) -> list[dict[str, Any]]:
    """获取任务 Pod 列表"""

@abstractmethod
async def get_pod_status(
    self, cluster_name: str, job_name: str, pod_name: str
) -> dict[str, Any]:
    """获取单个 Pod 状态"""

@abstractmethod
async def verify_checkpoint_exists(self, s3_path: str) -> bool:
    """验证检查点文件存在"""

@abstractmethod
async def list_checkpoints(
    self, job_id: str, checkpoint_base_path: str
) -> list[dict[str, Any]]:
    """列出任务检查点"""

@abstractmethod
async def resume_training_job(
    self,
    cluster_name: str,
    job_name: str,
    checkpoint_path: str | None = None,
    job_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """从检查点恢复任务"""

@abstractmethod
async def trigger_preemption(
    self,
    cluster_name: str,
    target_job_name: str,
    preemption_job_config: dict[str, Any],
) -> dict[str, Any]:
    """通过提交高优先级任务触发抢占"""
```

---

## 3. 关键文件清单

| 文件路径 | 修改类型 |
|---------|---------|
| `src/modules/training/infrastructure/hyperpod/client.py` | 添加 7 个方法 + 修改默认 region |
| `src/modules/training/application/interfaces.py` | 添加 7 个接口方法 |
| `tests/unit/training/test_svc_hyperpod_client.py` | 添加新方法单元测试 |

---

## 4. 验证步骤

### 4.1 单元测试

```bash
# 运行 HyperPodClient 单元测试
pytest tests/unit/training/test_svc_hyperpod_client.py -v
```

### 4.2 E2E 测试

```bash
# 设置 AWS 区域
export AWS_REGION=us-east-1
export E2E_READ_ONLY=false

# 运行抢占 SLA E2E 测试
pytest tests/e2e/aws/test_e2e_preemption_sla.py -v --override-ini="addopts="
```

### 4.3 预期结果

- 单元测试: 新增 7 个测试用例全部通过
- E2E 测试: 6 个场景从 skipped 变为 passed (需要 HyperPod 集群环境)

---

## 5. 风险与替代方案

### 风险 1: Kueue 抢占触发 ✅ 已解决

**决策**: 采用高优先级任务触发方案

**优势**:
- 符合真实生产场景的抢占机制
- 不需要额外的 Kubernetes API 配置
- 通过 HyperPod SDK 完成，保持代码一致性

### 风险 2: HyperPod SDK 能力限制

**问题**: SDK 可能不支持所有 Pod 级别操作

**替代方案**:
- 使用 `exec_command` 在 Pod 内执行命令
- 直接通过 boto3 SageMaker API 操作

---

## 6. 实现顺序

1. 修改 region 默认值 → us-east-1
2. 实现别名方法 (cancel_training_job, get_job_pods)
3. 实现 S3 相关方法 (verify_checkpoint_exists, list_checkpoints)
4. 实现 Pod 相关方法 (get_pod_status)
5. 实现恢复方法 (resume_training_job)
6. 实现抢占触发 (trigger_preemption) - 高优先级任务方案 ✅
7. 更新接口定义 (IHyperPodClient)
8. 编写单元测试

---

## 7. 预计变更行数

| 文件 | 新增行数 | 修改行数 |
|------|---------|---------|
| `client.py` | ~180 行 | ~5 行 |
| `interfaces.py` | ~40 行 | 0 行 |
| `test_svc_hyperpod_client.py` | ~150 行 | 0 行 |
| **总计** | **~370 行** | **~5 行** |
