from __future__ import annotations

import secrets

_CODE_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_CODE_LENGTH = 6


def new_prefixed_code(prefix: str) -> str:
    """生成带固定业务前缀的 6 位大写字母数字编码。"""
    suffix = "".join(secrets.choice(_CODE_ALPHABET) for _ in range(_CODE_LENGTH))
    return f"{prefix}-{suffix}"


__all__ = ["new_prefixed_code"]
