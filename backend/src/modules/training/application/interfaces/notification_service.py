"""告警通知服务接口。"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any


class NotificationChannel(str, Enum):
    """通知渠道"""

    EMAIL = "email"
    SLACK = "slack"
    DINGTALK = "dingtalk"
    SMS = "sms"
    WEBHOOK = "webhook"


@dataclass
class Alert:
    """告警消息"""

    title: str
    message: str
    severity: str  # 'info', 'warning', 'error', 'critical'
    recipient_ids: list[int]  # 接收者用户 ID 列表
    metadata: dict[str, Any] | None = None
    channels: list[NotificationChannel] | None = None


class INotificationService(ABC):
    """通知服务接口

    提供告警通知发送能力。
    实现可以对接邮件、Slack、钉钉等通知渠道。
    """

    @abstractmethod
    async def send_alert(self, alert: Alert) -> None:
        """发送告警通知

        Args:
            alert: 告警消息
        """

    @abstractmethod
    async def send_batch_alerts(self, alerts: list[Alert]) -> None:
        """批量发送告警通知

        Args:
            alerts: 告警消息列表
        """

    @abstractmethod
    async def test_channel(self, channel: NotificationChannel, config: dict[str, Any]) -> bool:
        """测试通知渠道连通性

        Args:
            channel: 通知渠道
            config: 渠道配置

        Returns:
            bool: 测试是否成功
        """
