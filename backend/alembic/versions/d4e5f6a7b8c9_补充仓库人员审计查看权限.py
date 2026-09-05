"""补充仓库人员审计查看权限

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-09-05 11:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: str | None = "c3d4e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """允许仓库工作人员查看本人审计日志。"""
    op.execute(
        sa.text(
            """
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id
            FROM roles AS r
            CROSS JOIN permissions AS p
            WHERE r.code = 'WAREHOUSE_STAFF'
              AND p.code = 'audit:read'
            ON CONFLICT (role_id, permission_id) DO NOTHING
            """
        )
    )


def downgrade() -> None:
    """撤销仓库工作人员的审计查看权限。"""
    op.execute(
        sa.text(
            """
            DELETE FROM role_permissions AS rp
            USING roles AS r, permissions AS p
            WHERE rp.role_id = r.id
              AND rp.permission_id = p.id
              AND r.code = 'WAREHOUSE_STAFF'
              AND p.code = 'audit:read'
            """
        )
    )
