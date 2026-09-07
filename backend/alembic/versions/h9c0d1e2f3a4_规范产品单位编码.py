"""规范历史产品单位编码。"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "h9c0d1e2f3a4"
down_revision: str | None = "g8b9c0d1e2f3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """将旧演示数据中的中文单位转换为 API 契约使用的编码。"""
    op.execute(
        sa.text(
            """
            UPDATE products
            SET unit = CASE TRIM(LOWER(unit))
                WHEN '千克' THEN 'KG'
                WHEN '公斤' THEN 'KG'
                WHEN 'kg' THEN 'KG'
                WHEN '吨' THEN 'TON'
                WHEN '箱' THEN 'BOX'
                WHEN '个' THEN 'PIECE'
                ELSE unit
            END
            WHERE TRIM(LOWER(unit)) IN ('千克', '公斤', 'kg', '吨', '箱', '个')
            """
        )
    )


def downgrade() -> None:
    """不将规范编码恢复为含义不明确的历史中文值。"""
