"""TLS/SSL配置

配置HTTPS服务的TLS版本和密码套件
"""

import ssl
from typing import Any

# TLS最低版本: TLS 1.2+
MIN_TLS_VERSION = ssl.TLSVersion.TLSv1_2

# 推荐的密码套件(按优先级排序)
# 使用现代密码套件,优先AEAD(如GCM),禁用弱密码
CIPHER_SUITES = [
    # TLS 1.3密码套件(推荐)
    "TLS_AES_256_GCM_SHA384",
    "TLS_AES_128_GCM_SHA256",
    "TLS_CHACHA20_POLY1305_SHA256",
    # TLS 1.2密码套件
    "ECDHE-ECDSA-AES256-GCM-SHA384",
    "ECDHE-RSA-AES256-GCM-SHA384",
    "ECDHE-ECDSA-AES128-GCM-SHA256",
    "ECDHE-RSA-AES128-GCM-SHA256",
    "ECDHE-ECDSA-CHACHA20-POLY1305",
    "ECDHE-RSA-CHACHA20-POLY1305",
    # 兼容性密码套件(如需支持较旧客户端)
    "ECDHE-ECDSA-AES256-SHA384",
    "ECDHE-RSA-AES256-SHA384",
    "ECDHE-ECDSA-AES128-SHA256",
    "ECDHE-RSA-AES128-SHA256",
]

# 密码套件字符串(OpenSSL格式)
CIPHER_SUITE_STRING = ":".join(CIPHER_SUITES)


def create_ssl_context(
    certfile: str,
    keyfile: str,
    min_tls_version: ssl.TLSVersion = MIN_TLS_VERSION,
    ciphers: str = CIPHER_SUITE_STRING,
) -> ssl.SSLContext:
    """创建SSL上下文

    Args:
        certfile: SSL证书文件路径
        keyfile: SSL私钥文件路径
        min_tls_version: 最低TLS版本
        ciphers: 密码套件字符串

    Returns:
        ssl.SSLContext: 配置好的SSL上下文
    """
    # 创建SSL上下文
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

    # 加载证书和私钥
    context.load_cert_chain(certfile=certfile, keyfile=keyfile)

    # 设置最低TLS版本
    context.minimum_version = min_tls_version

    # 设置密码套件
    context.set_ciphers(ciphers)

    # 安全选项
    context.options |= ssl.OP_NO_SSLv2  # 禁用SSLv2
    context.options |= ssl.OP_NO_SSLv3  # 禁用SSLv3
    context.options |= ssl.OP_NO_TLSv1  # 禁用TLS 1.0
    context.options |= ssl.OP_NO_TLSv1_1  # 禁用TLS 1.1
    context.options |= ssl.OP_NO_COMPRESSION  # 禁用TLS压缩(防止CRIME攻击)

    # 优先使用服务器密码套件顺序
    context.options |= ssl.OP_CIPHER_SERVER_PREFERENCE

    return context


def get_uvicorn_ssl_config(certfile: str, keyfile: str) -> dict[str, Any]:
    """获取Uvicorn的SSL配置

    Args:
        certfile: SSL证书文件路径
        keyfile: SSL私钥文件路径

    Returns:
        dict: Uvicorn SSL配置字典
    """
    return {
        "ssl_keyfile": keyfile,
        "ssl_certfile": certfile,
        "ssl_version": MIN_TLS_VERSION,
        "ssl_ciphers": CIPHER_SUITE_STRING,
    }


__all__ = [
    "MIN_TLS_VERSION",
    "CIPHER_SUITES",
    "CIPHER_SUITE_STRING",
    "create_ssl_context",
    "get_uvicorn_ssl_config",
]
