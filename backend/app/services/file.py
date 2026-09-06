from __future__ import annotations

import hashlib
from pathlib import Path
from typing import BinaryIO
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.authorization import resource_not_found
from app.core.auth.context import AuthContext
from app.core.config import Settings
from app.core.exceptions import AppException
from app.infrastructure.transaction import transaction_scope
from app.models import File
from app.repositories.file import FileRepository

_TYPE_SIGNATURES: dict[str, bytes] = {
    "application/pdf": b"%PDF-",
    "image/png": b"\x89PNG\r\n\x1a\n",
    "image/jpeg": b"\xff\xd8\xff",
}
_TYPE_EXTENSIONS = {
    "application/pdf": ".pdf",
    "image/png": ".png",
    "image/jpeg": ".jpg",
}
_CHUNK_SIZE = 1024 * 1024


def validate_upload_content(content_type: str | None, first_chunk: bytes) -> None:
    if not content_type or content_type not in _TYPE_SIGNATURES:
        raise AppException(
            code="FILE_TYPE_NOT_ALLOWED",
            message="仅允许上传 PDF、PNG 或 JPEG 文件",
            status_code=422,
        )
    if not first_chunk:
        raise AppException(code="FILE_EMPTY", message="不能上传空文件", status_code=422)
    if not first_chunk.startswith(_TYPE_SIGNATURES[content_type]):
        raise AppException(
            code="FILE_CONTENT_INVALID",
            message="文件内容与声明类型不匹配",
            status_code=422,
        )


class FileService:
    """质检附件存储和元数据用例。"""

    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.repository = FileRepository(session)

    async def upload(self, context: AuthContext, upload: UploadFile) -> File:
        if context.cooperative_id is None:
            raise AppException(
                code="BAD_REQUEST",
                message="附件上传必须关联合作社",
                status_code=400,
            )
        content_type = upload.content_type
        first_chunk = await upload.read(_CHUNK_SIZE)
        validate_upload_content(content_type, first_chunk)
        assert content_type is not None
        if len(first_chunk) > self.settings.max_upload_size_bytes:
            raise AppException(
                code="FILE_TOO_LARGE",
                message="文件大小超过配置限制",
                status_code=422,
            )
        storage_dir = self.settings.file_storage_path
        storage_dir.mkdir(parents=True, exist_ok=True)
        storage_key = f"{uuid4().hex}{_TYPE_EXTENSIONS[content_type]}"
        target = self._safe_path(storage_dir, storage_key)
        size = 0
        digest = hashlib.sha256()
        try:
            with target.open("wb") as output:
                size = self._write_chunk(output, digest, first_chunk, size)
                while True:
                    chunk = await upload.read(_CHUNK_SIZE)
                    if not chunk:
                        break
                    size = self._write_chunk(output, digest, chunk, size)
                    if size > self.settings.max_upload_size_bytes:
                        raise AppException(
                            code="FILE_TOO_LARGE",
                            message="文件大小超过 10MB 限制",
                            status_code=422,
                        )
            async with transaction_scope(self.session):
                return await self.repository.add(
                    File(
                        cooperative_id=context.cooperative_id,
                        original_name=self._safe_original_name(upload.filename),
                        storage_key=storage_key,
                        mime_type=content_type,
                        size_bytes=size,
                        sha256=digest.hexdigest(),
                        uploaded_by=context.user_id,
                    )
                )
        except Exception:
            target.unlink(missing_ok=True)
            raise

    async def get(self, context: AuthContext, file_id: UUID) -> File:
        async with transaction_scope(self.session):
            file = await self.repository.get_downloadable(
                context.cooperative_id, file_id
            )
            if file is None:
                raise resource_not_found()
            target = self.storage_path_for(file.storage_key)
            if not target.is_file():
                raise AppException(
                    code="FILE_NOT_FOUND",
                    message="附件内容不存在",
                    status_code=404,
                )
            return file

    @staticmethod
    def _write_chunk(
        output: BinaryIO,
        digest: hashlib._Hash,
        chunk: bytes,
        size: int,
    ) -> int:
        output.write(chunk)
        digest.update(chunk)
        return size + len(chunk)

    @staticmethod
    def _safe_original_name(filename: str | None) -> str:
        name = Path(filename or "unnamed").name.strip()
        return (name or "unnamed")[:255]

    @staticmethod
    def _safe_path(storage_dir: Path, storage_key: str) -> Path:
        root = storage_dir.resolve()
        target = (root / storage_key).resolve()
        if target.parent != root:
            raise AppException(
                code="FILE_PATH_INVALID",
                message="附件存储路径无效",
                status_code=500,
            )
        return target

    def storage_path_for(self, storage_key: str) -> Path:
        """返回受控目录内的附件路径。"""
        return self._safe_path(self.settings.file_storage_path, storage_key)


__all__ = ["FileService", "validate_upload_content"]
