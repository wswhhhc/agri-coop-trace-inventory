"""修复旧数据库缺失的角色更新时间字段。"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f7a8b9c0d1e2"
down_revision: str | None = "f6a7b8c9d0e1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """为旧版 roles 表补齐 ORM 所需的 updated_at 字段。"""
    op.execute(
        sa.text(
            """
            ALTER TABLE roles
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE
            NOT NULL DEFAULT CURRENT_TIMESTAMP
            """
        )
    )


def downgrade() -> None:
    """回滚本次兼容性修复。"""
    op.execute(sa.text("ALTER TABLE roles DROP COLUMN IF EXISTS updated_at"))
