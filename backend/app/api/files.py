from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, UploadFile
from fastapi import File as FastAPIFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import CurrentAuthContext
from app.core.config import Settings, get_settings
from app.infrastructure.database import get_db_session
from app.models import File as FileModel
from app.schemas.common import ApiResponse
from app.schemas.file import FileData
from app.services.file import FileService

router = APIRouter(prefix="/files", tags=["files"])


def get_file_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> FileService:
    return FileService(session, settings)


def _file_data(file: FileModel) -> FileData:
    return FileData(
        id=file.id,
        original_name=file.original_name,
        content_type=file.mime_type,
        size=file.size_bytes,
        download_url=f"/api/v1/files/{file.id}",
        created_at=file.created_at,
    )


@router.post("", response_model=ApiResponse[FileData], status_code=201)
async def upload_file(
    upload: Annotated[UploadFile, FastAPIFile(description="质检附件")],
    context: CurrentAuthContext,
    service: Annotated[FileService, Depends(get_file_service)],
) -> ApiResponse[FileData]:
    file = await service.upload(context, upload)
    return ApiResponse(data=_file_data(file))


@router.get("/{fileId}")
async def download_file(
    file_id: Annotated[UUID, Path(alias="fileId")],
    context: CurrentAuthContext,
    service: Annotated[FileService, Depends(get_file_service)],
) -> FileResponse:
    file = await service.get(context, file_id)
    return FileResponse(
        path=service.storage_path_for(file.storage_key),
        media_type=file.mime_type,
        filename=file.original_name,
    )


__all__ = ["get_file_service", "router"]
