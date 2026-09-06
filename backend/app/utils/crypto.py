from __future__ import annotations

import hashlib


def sha256_hex(value: str | bytes) -> str:
    """返回字符串（UTF-8）或字节序列的 SHA-256 十六进制摘要。"""
    encoded = value.encode("utf-8") if isinstance(value, str) else value
    return hashlib.sha256(encoded).hexdigest()


__all__ = ["sha256_hex"]
