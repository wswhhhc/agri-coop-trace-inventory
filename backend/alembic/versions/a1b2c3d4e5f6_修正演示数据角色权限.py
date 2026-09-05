"""修正演示数据角色权限

Revision ID: a1b2c3d4e5f6
Revises: e4f3c0ebc976
Create Date: 2026-09-04 10:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "e4f3c0ebc976"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """将旧版演示数据修正为当前最小权限边界。"""
    op.execute(
        sa.text(
            """
            DELETE FROM role_permissions AS rp
            USING roles AS r, permissions AS p
            WHERE rp.role_id = r.id
              AND rp.permission_id = p.id
              AND r.code = 'SYSTEM_ADMIN'
              AND p.code IN ('inventory:write', 'alert:handle')
            """
        )
    )
    op.execute(
        sa.text(
            """
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id
            FROM roles AS r
            CROSS JOIN permissions AS p
            WHERE r.code = 'WAREHOUSE_STAFF'
              AND p.code = 'alert:handle'
            ON CONFLICT (role_id, permission_id) DO NOTHING
            """
        )
    )


def downgrade() -> None:
    """恢复旧版演示数据的权限关系。"""
    op.execute(
        sa.text(
            """
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id
            FROM roles AS r
            CROSS JOIN permissions AS p
            WHERE r.code = 'SYSTEM_ADMIN'
              AND p.code IN ('inventory:write', 'alert:handle')
            ON CONFLICT (role_id, permission_id) DO NOTHING
            """
        )
    )
    op.execute(
        sa.text(
            """
            DELETE FROM role_permissions AS rp
            USING roles AS r, permissions AS p
            WHERE rp.role_id = r.id
              AND rp.permission_id = p.id
              AND r.code = 'WAREHOUSE_STAFF'
              AND p.code = 'alert:handle'
            """
        )
    )
