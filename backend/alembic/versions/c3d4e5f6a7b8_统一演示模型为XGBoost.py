"""统一演示模型为 XGBoost

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-09-05 10:15:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c3d4e5f6a7b8"
down_revision: str | None = "b2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """将旧版合成演示数据中的随机森林模型统一为 XGBoost。"""
    op.execute(
        sa.text(
            """
            UPDATE model_versions
            SET model_type = 'XGBOOST',
                version = regexp_replace(
                    version,
                    '^random_forest-synthetic-',
                    'xgboost-synthetic-'
                )
            WHERE data_type = 'SYNTHETIC'
              AND model_type = 'RANDOM_FOREST'
              AND version LIKE 'random_forest-synthetic-%'
            """
        )
    )


def downgrade() -> None:
    """恢复旧版合成演示数据中的随机森林模型标识。"""
    op.execute(
        sa.text(
            """
            UPDATE model_versions
            SET model_type = 'RANDOM_FOREST',
                version = regexp_replace(
                    version,
                    '^xgboost-synthetic-',
                    'random_forest-synthetic-'
                )
            WHERE data_type = 'SYNTHETIC'
              AND model_type = 'XGBOOST'
              AND version LIKE 'xgboost-synthetic-%'
              AND CAST(substring(version FROM '[0-9]+$') AS INTEGER) % 2 = 0
            """
        )
    )
