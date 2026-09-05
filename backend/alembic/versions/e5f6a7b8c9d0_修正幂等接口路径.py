"""修正幂等接口路径

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-09-05 11:15:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e5f6a7b8c9d0"
down_revision: str | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """将旧版演示幂等记录更新为接口文档规定的出库路径。"""
    op.execute(
        sa.text(
            """
            UPDATE idempotency_records
            SET endpoint = '/api/v1/inventory-issues'
            WHERE endpoint = '/api/v1/inventory-outbounds'
            """
        )
    )


def downgrade() -> None:
    """恢复旧版演示幂等记录路径。"""
    op.execute(
        sa.text(
            """
            UPDATE idempotency_records
            SET endpoint = '/api/v1/inventory-outbounds'
            WHERE endpoint = '/api/v1/inventory-issues'
              AND idempotency_key LIKE 'synthetic-request-%'
            """
        )
    )
