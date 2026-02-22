"""Datetime utilities with timezone awareness."""

from datetime import UTC, datetime, timezone


def utc_now() -> datetime:
    """Get current UTC time with timezone info."""
    return datetime.now(UTC)


def ensure_aware(dt: datetime) -> datetime:
    """确保 datetime 是 timezone-aware。

    MySQL DATETIME 列不存储时区信息，SQLAlchemy 读取时返回 naive datetime。
    本函数将 naive datetime 视为 UTC 并添加 tzinfo。
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt
