"""安全工具

提供密码哈希和JWT令牌生成验证功能
"""

from datetime import datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from config.settings import settings

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码

    Args:
        plain_password: 明文密码
        hashed_password: 密码哈希

    Returns:
        bool: 密码是否匹配
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码哈希

    Args:
        password: 明文密码

    Returns:
        str: 密码哈希
    """
    return pwd_context.hash(password)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """创建JWT访问令牌

    Args:
        data: 要编码的数据
        expires_delta: 过期时间增量

    Returns:
        str: JWT令牌
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def create_refresh_token(data: dict[str, Any]) -> str:
    """创建JWT刷新令牌

    Args:
        data: 要编码的数据

    Returns:
        str: JWT令牌
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.jwt_refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def decode_token(token: str) -> dict[str, Any]:
    """解码JWT令牌

    Args:
        token: JWT令牌

    Returns:
        dict: 解码后的数据

    Raises:
        JWTError: 令牌无效或过期
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError as e:
        raise ValueError(f"Invalid token: {str(e)}") from e


def verify_token(token: str, token_type: str = "access") -> dict[str, Any]:
    """验证JWT令牌

    Args:
        token: JWT令牌
        token_type: 令牌类型（access或refresh）

    Returns:
        dict: 解码后的数据

    Raises:
        ValueError: 令牌无效或类型不匹配
    """
    payload = decode_token(token)

    if payload.get("type") != token_type:
        raise ValueError(f"Invalid token type, expected {token_type}")

    return payload


__all__ = [
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "verify_token",
]
