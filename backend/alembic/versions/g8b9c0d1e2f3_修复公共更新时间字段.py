"""修复旧数据库缺失的公共更新时间字段。"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "g8b9c0d1e2f3"
down_revision: str | None = "f7a8b9c0d1e2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """为旧版权限和审计表补齐 ORM 所需的 updated_at 字段。"""
    for table_name in ("permissions", "audit_logs"):
        op.execute(
            sa.text(
                f"""
                ALTER TABLE {table_name}
                ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE
                NOT NULL DEFAULT CURRENT_TIMESTAMP
                """
            )
        )


def downgrade() -> None:
    """回滚本次兼容性修复。"""
    for table_name in ("permissions", "audit_logs"):
        op.execute(sa.text(f"ALTER TABLE {table_name} DROP COLUMN IF EXISTS updated_at"))
