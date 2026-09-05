from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Uuid, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.models._common import utc_now


class Base(DeclarativeBase):
    """全项目唯一 ORM 声明基类和公共持久化字段来源。"""

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
        server_default=text("CURRENT_TIMESTAMP"),
    )


__all__ = ["Base"]
