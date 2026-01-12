"""通用单例工厂实现.

提供可复用的单例模式，消除服务层的重复代码。
"""

from typing import Callable, Optional, TypeVar

T = TypeVar("T")


def create_singleton_getter(cls: type[T]) -> Callable[[], T]:
    """创建单例获取函数.

    Args:
        cls: 需要创建单例的类

    Returns:
        返回单例实例的函数

    Example:
        >>> class MyService:
        ...     pass
        >>> get_my_service = create_singleton_getter(MyService)
        >>> service1 = get_my_service()
        >>> service2 = get_my_service()
        >>> assert service1 is service2
    """
    _instance: Optional[T] = None

    def getter() -> T:
        nonlocal _instance
        if _instance is None:
            _instance = cls()
        return _instance

    # 添加重置方法用于测试
    def reset() -> None:
        nonlocal _instance
        _instance = None

    getter.reset = reset  # type: ignore[attr-defined]
    return getter
