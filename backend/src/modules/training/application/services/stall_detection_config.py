"""停滞检测配置和数据模型.

定义停滞检测的配置参数和结果数据结构。
"""

from dataclasses import dataclass, field

# 默认指标回退顺序
DEFAULT_METRIC_FALLBACK = ["loss", "accuracy", "perplexity"]


@dataclass
class StallDetectionConfig:
    """停滞检测配置"""

    primary_metric: str = "loss"
    detection_window_minutes: int = 30
    change_rate_threshold: float = 0.001  # 0.1%
    enabled: bool = True


@dataclass
class StallCheckResult:
    """停滞检查结果"""

    job_id: int
    is_stalled: bool
    metric_name: str | None = None
    metric_values: list[float] = field(default_factory=list)
    change_rate: float | None = None
    detection_window_minutes: int = 30
    skipped: bool = False
    skip_reason: str | None = None
