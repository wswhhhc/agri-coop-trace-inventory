"""补充质检项目单位和更正记录关联

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-09-05 20:30:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f6a7b8c9d0e1"
down_revision: str | None = "e5f6a7b8c9d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.add_column(
        "quality_inspections",
        sa.Column("original_inspection_id", UUID, nullable=True),
    )
    op.create_foreign_key(
        "fk_quality_inspections_original",
        "quality_inspections",
        "quality_inspections",
        ["original_inspection_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_quality_inspections_original",
        "quality_inspections",
        ["original_inspection_id"],
    )
    op.add_column(
        "quality_inspection_items",
        sa.Column("unit", sa.String(20), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("quality_inspection_items", "unit")
    op.drop_index(
        "ix_quality_inspections_original", table_name="quality_inspections"
    )
    op.drop_constraint(
        "fk_quality_inspections_original", "quality_inspections", type_="foreignkey"
    )
    op.drop_column("quality_inspections", "original_inspection_id")
