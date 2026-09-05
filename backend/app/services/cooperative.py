from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.authorization import (
    ensure_cooperative_scope,
    permission_denied,
    resource_not_found,
)
from app.core.auth.context import AuthContext
from app.core.exceptions import AppException
from app.infrastructure.transaction import transaction_scope
from app.models import Cooperative
from app.repositories.cooperative import CooperativeRepository
from app.schemas.cooperative import (
    CooperativeCreate,
    CooperativeListParams,
    CooperativeUpdate,
)

COOPERATIVE_ADMIN_ROLE_CODE = "COOPERATIVE_ADMIN"
COOPERATIVE_MANAGE_PERMISSION = "cooperative:manage"


class CooperativeService:
    """合作社业务用例，统一在 Service 建立事务边界。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = CooperativeRepository(session)

    async def list(
        self,
        context: AuthContext,
        params: CooperativeListParams,
    ) -> tuple[list[Cooperative], int]:
        self._require_manage_permission(context)
        async with transaction_scope(self.session):
            return await self.repository.list_scoped(
                context.cooperative_id,
                keyword=params.keyword,
                status=params.status,
                page=params.page,
                page_size=params.page_size,
                sort_by=params.sort_by,
                sort_order=params.sort_order,
            )

    async def get(self, context: AuthContext, cooperative_id: UUID) -> Cooperative:
        if not context.has_permission(COOPERATIVE_MANAGE_PERMISSION) and (
            context.role_code != COOPERATIVE_ADMIN_ROLE_CODE
        ):
            raise permission_denied()
        ensure_cooperative_scope(context, cooperative_id)
        async with transaction_scope(self.session):
            cooperative = await self.repository.get_scoped(
                context.cooperative_id, cooperative_id
            )
            if cooperative is None:
                raise resource_not_found()
            return cooperative

    async def create(
        self,
        context: AuthContext,
        payload: CooperativeCreate,
    ) -> Cooperative:
        self._require_manage_permission(context)
        async with transaction_scope(self.session):
            return await self.repository.add(
                Cooperative(**payload.model_dump(exclude_none=True))
            )

    async def update(
        self,
        context: AuthContext,
        cooperative_id: UUID,
        payload: CooperativeUpdate,
    ) -> Cooperative:
        self._require_manage_permission(context)
        ensure_cooperative_scope(context, cooperative_id)
        values = payload.model_dump(exclude_unset=True)
        if not values:
            raise AppException(
                code="BAD_REQUEST",
                message="至少提供一个需要更新的字段",
                status_code=400,
            )
        async with transaction_scope(self.session):
            cooperative = await self.repository.get_scoped(
                context.cooperative_id, cooperative_id
            )
            if cooperative is None:
                raise resource_not_found()
            return await self.repository.update(cooperative, values)

    @staticmethod
    def _require_manage_permission(context: AuthContext) -> None:
        if not context.has_permission(COOPERATIVE_MANAGE_PERMISSION):
            raise permission_denied()


__all__ = ["CooperativeService"]
