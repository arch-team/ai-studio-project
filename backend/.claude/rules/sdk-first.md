# SDK 优先 (SDK-First)

> **职责**: SDK 优先原则，定义 SDK 决策流程和异常处理模式。

> Claude 生成代码时优先查阅

**核心原则**: 尽可能使用 SDK 简化代码实现，避免重复造轮子。

---

## SDK 决策流程

```
需要实现某功能?
    |
官方 SDK 支持? --是--> 直接使用 SDK
    |
   否
    |
社区库评估通过? --是--> 使用社区库
    |
   否
    |
自定义实现 (需 Tech Lead 审批)
```

---

## 推荐 SDK

| 领域 | 推荐方案 | 替代 | 原因 |
|------|---------|------|------|
| **AWS 异步操作** | aioboto3 | boto3 + run_in_executor | 原生异步 I/O，无线程池开销 |
| **后台任务** | K8s CronJob + Watch API | Celery + Redis | 利用现有 EKS，无需额外组件 |
| **认证** | Authlib | python-jose 手写 | 完整 OAuth2/OIDC，支持 AWS IAM |
| **日志** | structlog | 标准 logging | 结构化 JSON，上下文绑定 |
| **监控** | OpenTelemetry | 厂商特定 SDK | CNCF 标准，可切换后端 |
| **实验追踪** | MLflow | 自建系统 | 行业标准，支持模型注册 |

---

## AWS 异步操作规范 (强制)

**规则**: 所有 AWS S3/FSx 等需要异步的操作，**必须**使用 `aioboto3`，**禁止**自己封装 `run_in_executor`。

```python
# 禁止: 手动封装同步 boto3
import boto3
import asyncio

class S3Client:
    def __init__(self):
        self._client = boto3.client("s3")

    async def upload_file(self, ...):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._sync_upload)

# 正确: 使用 aioboto3 原生异步
import aioboto3

class S3Client:
    def __init__(self):
        self._session = aioboto3.Session()

    async def upload_file(self, local_path: str, remote_path: str) -> str:
        async with self._session.client("s3", region_name=self._region) as s3:
            await s3.upload_file(local_path, self._bucket, remote_path)
        return remote_path
```

**原因**:
- `run_in_executor` 使用线程池，有额外开销
- aioboto3 提供真正的异步 I/O，性能更好
- 代码更简洁，减少重复的包装模式

**参考实现**:
- `src/shared/infrastructure/storage/s3_client.py` - S3 基础操作
- `src/modules/datasets/infrastructure/s3/multipart_upload_client.py` - 分片上传

---

## 后台任务实现指南

**定时任务 -> Kubernetes CronJob**
- 训练卡住检测（每30分钟）
- 存储容量告警（每5分钟）
- 检查点迁移（每30分钟）

**事件驱动 -> Kubernetes Watch API**
- HyperPod/Kueue 状态变化监控
- 抢占事件检测

---

## 优先级说明

### 优先级 1: 直接使用官方 SDK

无需封装，直接调用。

### 优先级 2: SDK + 薄封装层

**封装原则**: < 100 行 | 不改变 SDK 行为 | 暴露原生类型

### 优先级 3: 社区库

| 指标 | 最低要求 |
|------|---------|
| GitHub Stars | > 1,000 |
| 最近提交 | < 3 个月 |
| 许可证 | MIT / Apache 2.0 |

### 优先级 4: 自定义实现

**必须流程**: research.md 记录 -> 说明理由 -> Tech Lead 审批

---

## SDK 异常处理

```python
# 模式: SDK 异常 -> Problem 域异常
try:
    self._client.operation(...)
except ClientError as e:
    raise DomainError(f"操作失败: {e}") from e
```

| SDK | 原始异常 | 域异常 | HTTP |
|-----|---------|--------|------|
| boto3 | `ClientError (NoSuchKey)` | `EntityNotFoundError` | 404 |
| boto3 | `ClientError (AccessDenied)` | `PermissionError` | 403 |
| SQLAlchemy | `IntegrityError` | `DuplicateEntityError` | 409 |

---

## 实现前检查清单

1. 搜索 PyPI 是否有现成方案
2. 检查 FastAPI 生态集成 (awesome-fastapi)
3. AWS 功能优先用 boto3 官方 SDK
4. 复杂功能找专业库，简单功能用标准库

---

## 反模式

```python
# 禁止: 过度封装 - 模糊接口，隐藏 SDK 行为
class SuperAwesomeS3Wrapper:
    def magic_upload(self, thing): ...

# 正确: 薄封装 - 明确接口，直接委托 SDK
class S3Adapter:
    def upload_file(self, local: Path, uri: S3Uri) -> None:
        self._client.upload_file(str(local), uri.bucket, uri.key)
```

---

## PR Review 检查清单

完整检查清单见 [checklist.md](checklist.md) SDK 使用章节
