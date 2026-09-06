from __future__ import annotations


def contains_pattern(keyword: str) -> str:
    """构造保持现有 SQL LIKE 通配符语义的包含匹配模式。"""
    return f"%{keyword.strip()}%"


__all__ = ["contains_pattern"]
