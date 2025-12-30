"""日志配置

提供统一的日志配置和日志工具
"""

import logging
import sys
from pathlib import Path
from typing import Any

from .settings import settings

# 日志格式
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
JSON_LOG_FORMAT = '{"time":"%(asctime)s","name":"%(name)s","level":"%(levelname)s","message":"%(message)s"}'


def setup_logging() -> None:
    """配置应用日志系统"""
    # 获取日志级别
    log_level = getattr(logging, settings.log_level)

    # 创建根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # 清除现有处理器
    root_logger.handlers.clear()

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # 根据环境选择格式
    if settings.is_production:
        # 生产环境使用JSON格式便于日志聚合
        formatter = logging.Formatter(JSON_LOG_FORMAT)
    else:
        # 开发环境使用人类可读格式
        formatter = logging.Formatter(
            LOG_FORMAT,
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 如果是开发环境，添加文件处理器
    if settings.is_development:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        file_handler = logging.FileHandler(log_dir / "app.log")
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # 调整第三方库日志级别
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("kubernetes").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志记录器

    Args:
        name: 日志记录器名称，通常使用 __name__

    Returns:
        logging.Logger: 日志记录器实例
    """
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """自定义日志适配器，支持添加上下文信息"""

    def process(self, msg: str, kwargs: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        """处理日志消息，添加额外的上下文信息

        Args:
            msg: 日志消息
            kwargs: 关键字参数

        Returns:
            处理后的消息和参数
        """
        # 从extra中获取上下文信息
        extra = kwargs.get("extra", {})

        # 构建上下文字符串
        context_parts = []
        for key, value in self.extra.items():
            context_parts.append(f"{key}={value}")

        if context_parts:
            context = " | ".join(context_parts)
            msg = f"[{context}] {msg}"

        return msg, kwargs


def get_logger_with_context(name: str, **context: Any) -> LoggerAdapter:
    """获取带上下文的日志记录器

    Args:
        name: 日志记录器名称
        **context: 上下文信息

    Returns:
        LoggerAdapter: 带上下文的日志适配器

    Example:
        logger = get_logger_with_context(__name__, user_id=123, request_id="abc")
        logger.info("User action")  # 输出: [user_id=123 | request_id=abc] User action
    """
    logger = get_logger(name)
    return LoggerAdapter(logger, context)


# 初始化日志系统
setup_logging()

# 导出常用函数
__all__ = [
    "setup_logging",
    "get_logger",
    "get_logger_with_context",
    "LoggerAdapter",
]
