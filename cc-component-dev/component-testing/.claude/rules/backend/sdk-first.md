---
paths:
  - "backend/**/*.py"
---

# SDK 优先原则

优先使用成熟 SDK，避免重复造轮子。

## 推荐方案

| 领域 | 推荐 | 避免 | 原因 |
|------|------|------|------|
| 后台任务 | K8s CronJob + Watch API | Celery + Redis | 利用现有 EKS |
| 认证 | Authlib | python-jose 手写 | 完整 OAuth2/OIDC |
| 日志 | structlog | 标准 logging | 结构化 JSON |
| 监控 | OpenTelemetry | 厂商特定 SDK | CNCF 标准 |
| AWS | boto3 官方 SDK | 直接 HTTP | 官方维护 |

## 实现前检查清单

1. 搜索 PyPI 是否有现成方案
2. 检查 FastAPI 生态集成 (awesome-fastapi)
3. AWS 功能优先用 boto3 官方 SDK
4. 复杂功能找专业库，简单功能用标准库

## 后台任务实现

**定时任务 → Kubernetes CronJob**
- 训练卡住检测（每30分钟）
- 存储容量告警（每5分钟）
- 检查点迁移（每30分钟）

**事件驱动 → Kubernetes Watch API**
- HyperPod/Kueue 状态变化监控
- 抢占事件检测
