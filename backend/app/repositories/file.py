from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import File, InspectionFile, QualityInspection


class FileRepository:
    """质检附件元数据访问，所有资源查询带合作社范围。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_scoped(
        self,
        cooperative_id: UUID,
        file_ids: list[UUID],
    ) -> list[File]:
        if not file_ids:
            return []
        result = await self.session.scalars(
            select(File).where(
                File.cooperative_id == cooperative_id,
                File.id.in_(file_ids),
            )
        )
        return list(result)

    async def get_scoped(self, cooperative_id: UUID, file_id: UUID) -> File | None:
        return await self.session.scalar(
            select(File).where(
                File.cooperative_id == cooperative_id,
                File.id == file_id,
            )
        )

    async def get_downloadable(
        self, cooperative_id: UUID | None, file_id: UUID
    ) -> File | None:
        """只返回已关联质检记录且在当前合作社范围内的附件。"""
        statement = (
            select(File)
            .join(InspectionFile, InspectionFile.file_id == File.id)
            .join(QualityInspection, QualityInspection.id == InspectionFile.inspection_id)
            .where(File.id == file_id)
            .distinct()
        )
        if cooperative_id is not None:
            statement = statement.where(
                File.cooperative_id == cooperative_id,
                QualityInspection.cooperative_id == cooperative_id,
            )
        return await self.session.scalar(statement)

    async def add(self, file: File) -> File:
        self.session.add(file)
        await self.session.flush()
        return file


__all__ = ["FileRepository"]
