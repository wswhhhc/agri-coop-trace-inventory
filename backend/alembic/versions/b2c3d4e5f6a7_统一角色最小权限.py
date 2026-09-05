"""统一角色最小权限

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-09-05 10:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """使角色权限与需求文档的查看/管理边界一致。"""
    op.execute(
        sa.text(
            """
            INSERT INTO permissions (code, name, module, description)
            VALUES (
                'model:read',
                '查看预测模型',
                'forecasting',
                '查看预测模型和预测结果'
            )
            ON CONFLICT (code) DO NOTHING
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
              AND r.code = 'SYSTEM_ADMIN'
              AND p.code IN (
                  'warehouse:manage',
                  'product:manage',
                  'batch:manage',
                  'model:manage'
              )
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
            WHERE r.code IN (
                'SYSTEM_ADMIN',
                'COOPERATIVE_ADMIN',
                'WAREHOUSE_STAFF'
            )
              AND p.code = 'model:read'
            ON CONFLICT (role_id, permission_id) DO NOTHING
            """
        )
    )


def downgrade() -> None:
    """恢复迁移前的角色权限关系。"""
    op.execute(
        sa.text(
            """
            DELETE FROM role_permissions AS rp
            USING permissions AS p
            WHERE rp.permission_id = p.id
              AND p.code = 'model:read'
            """
        )
    )
    op.execute(
        sa.text("DELETE FROM permissions WHERE code = 'model:read'")
    )
    op.execute(
        sa.text(
            """
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id
            FROM roles AS r
            CROSS JOIN permissions AS p
            WHERE r.code = 'SYSTEM_ADMIN'
              AND p.code IN (
                  'warehouse:manage',
                  'product:manage',
                  'batch:manage',
                  'model:manage'
              )
            ON CONFLICT (role_id, permission_id) DO NOTHING
            """
        )
    )
