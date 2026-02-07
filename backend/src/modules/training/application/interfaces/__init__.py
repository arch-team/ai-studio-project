"""训练模块应用层接口。

将大型 interfaces.py 拆分为多个专门的接口文件:
- hyperpod_client.py: SageMaker HyperPod 操作契约
- metrics_service.py: 训练指标查询契约
- notification_service.py: 告警通知契约
- storage_service.py: 检查点存储操作契约
"""

from .hyperpod_client import IHyperPodClient
from .metrics_service import IMetricsService, MetricData, MetricPoint
from .notification_service import Alert, INotificationService, NotificationChannel
from .storage_service import IStorageService

__all__ = [
    "IHyperPodClient",
    "IMetricsService",
    "MetricData",
    "MetricPoint",
    "Alert",
    "INotificationService",
    "NotificationChannel",
    "IStorageService",
]
