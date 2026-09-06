from __future__ import annotations

from pathlib import Path

from app.core.exceptions import AppException


def safe_export_path(storage_dir: Path, filename: str) -> Path:
    """只允许访问导出根目录下的文件，拒绝路径穿越。"""
    root = storage_dir.resolve()
    target = (root / filename).resolve()
    if target.parent != root:
        raise AppException(
            code="EXPORT_PATH_INVALID", message="导出文件路径无效", status_code=500
        )
    return target


__all__ = ["safe_export_path"]
