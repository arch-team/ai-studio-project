"""Structlog 结构化日志配置。

提供开发环境彩色输出和生产环境 JSON 结构化输出的统一日志配置。
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor

from src.shared.infrastructure.config import get_settings


def _add_module_info(
    logger: logging.Logger, method_name: str, event_dict: EventDict
) -> EventDict:
    """添加模块信息到日志上下文。"""
    # structlog 的 logger 可能是字符串（logger name）或 logging.Logger
    if isinstance(logger, str):
        event_dict["module"] = logger
    elif hasattr(logger, "name"):
        event_dict["module"] = logger.name
    return event_dict


def _drop_color_message(
    logger: logging.Logger, method_name: str, event_dict: EventDict
) -> EventDict:
    """移除 uvicorn 产生的 color_message 字段。"""
    event_dict.pop("color_message", None)
    return event_dict


def _ensure_exception_info(
    logger: logging.Logger, method_name: str, event_dict: EventDict
) -> EventDict:
    """确保异常信息被正确记录。"""
    if method_name in ("exception", "error"):
        exc_info = event_dict.get("exc_info")
        if exc_info is True:
            event_dict["exc_info"] = sys.exc_info()
    return event_dict


def get_processors(is_json: bool = False) -> list[Processor]:
    """获取日志处理器链。

    Args:
        is_json: 是否为 JSON 输出模式（生产环境）

    Returns:
        处理器列表
    """
    # 共享处理器
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        _add_module_info,
        _drop_color_message,
        _ensure_exception_info,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if is_json:
        # 生产环境：JSON 格式
        shared_processors.extend([
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ])
    else:
        # 开发环境：彩色控制台输出
        shared_processors.extend([
            structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.plain_traceback,
            ),
        ])

    return shared_processors


def configure_logging(
    level: str = "INFO",
    json_output: bool | None = None,
) -> None:
    """配置 structlog 日志系统。

    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
        json_output: 是否使用 JSON 输出，None 时根据环境自动判断
    """
    settings = get_settings()

    # 自动判断输出格式
    if json_output is None:
        json_output = settings.environment == "production"

    # 配置日志级别
    log_level = getattr(logging, level.upper(), logging.INFO)

    # 配置标准库 logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
        force=True,
    )

    # 配置第三方库日志级别
    _configure_third_party_loggers(log_level)

    # 获取处理器链
    processors = get_processors(is_json=json_output)

    # 配置 structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def _configure_third_party_loggers(level: int) -> None:
    """配置第三方库日志级别，减少噪音。"""
    # 降低 uvicorn 和其他库的日志级别
    quiet_loggers = [
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
        "sqlalchemy.engine",
        "sqlalchemy.pool",
        "boto3",
        "botocore",
        "aiobotocore",
        "httpcore",
        "httpx",
    ]

    # 对于 DEBUG 级别，保持第三方库为 INFO
    third_party_level = max(level, logging.INFO)

    for logger_name in quiet_loggers:
        logging.getLogger(logger_name).setLevel(third_party_level)


def get_logger(name: str | None = None) -> structlog.BoundLogger:
    """获取结构化日志记录器。

    Args:
        name: 日志记录器名称，通常传入 __name__

    Returns:
        结构化日志记录器
    """
    return structlog.get_logger(name)  # type: ignore[no-any-return]


def bind_context(**kwargs: Any) -> None:
    """绑定上下文信息到当前请求的所有日志。

    Args:
        **kwargs: 要绑定的上下文键值对

    Example:
        bind_context(request_id="abc-123", user_id=42)
    """
    structlog.contextvars.bind_contextvars(**kwargs)


def clear_context() -> None:
    """清除当前请求的所有上下文信息。"""
    structlog.contextvars.clear_contextvars()


def unbind_context(*keys: str) -> None:
    """解绑指定的上下文键。

    Args:
        *keys: 要解绑的键名
    """
    structlog.contextvars.unbind_contextvars(*keys)
