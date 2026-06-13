"""训练模块应用层接口。

将大型 interfaces.py 拆分为多个专门的接口文件:
- hyperpod_client.py: SageMaker HyperPod 操作契约
- metrics_service.py: 训练指标查询契约
- notification_service.py: 告警通知契约
- storage_service.py: 检查点存储操作契约
- log_client.py: 训练日志获取契约
- kueue_client.py: Kueue 队列状态查询契约
"""

from .hyperpod_client import IHyperPodClient
from .kueue_client import IKueueClient, KueueWorkloadData, PreemptionEventData
from .log_client import ITrainingLogClient, LogEntryData
from .metrics_service import IMetricsService, MetricData, MetricPoint
from .notification_service import Alert, INotificationService, NotificationChannel
from .storage_service import IStorageService, StorageInfo

__all__ = [
    "IHyperPodClient",
    "IKueueClient",
    "ITrainingLogClient",
    "IMetricsService",
    "KueueWorkloadData",
    "LogEntryData",
    "MetricData",
    "MetricPoint",
    "PreemptionEventData",
    "Alert",
    "INotificationService",
    "NotificationChannel",
    "IStorageService",
    "StorageInfo",
]
