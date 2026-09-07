from __future__ import annotations

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool

pytestmark = pytest.mark.postgres
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _alembic_config(database_url: str, connection: object) -> Config:
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(PROJECT_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url)
    config.attributes["connection"] = connection
    return config


async def _table_names(engine: AsyncEngine) -> set[str]:
    async with engine.connect() as connection:
        return await connection.run_sync(
            lambda sync_connection: set(inspect(sync_connection).get_table_names())
        )


@pytest.mark.asyncio
async def test_alembic_upgrade_head_then_downgrade_base(
    postgres_database_url: str,
    postgres_schema: str,
) -> None:
    engine = create_async_engine(
        postgres_database_url,
        poolclass=NullPool,
        connect_args={"server_settings": {"search_path": postgres_schema}},
    )
    try:
        async with engine.begin() as connection:
            await connection.run_sync(
                lambda sync_connection: command.upgrade(
                    _alembic_config(postgres_database_url, sync_connection), "head"
                )
            )

        tables = await _table_names(engine)
        assert "alembic_version" in tables
        assert {
            "cooperatives",
            "products",
            "batches",
            "audit_logs",
        }.issubset(tables)

        async with engine.connect() as connection:
            version = await connection.scalar(text("SELECT version_num FROM alembic_version"))
        assert version == "h9c0d1e2f3a4"

        async with engine.begin() as connection:
            await connection.run_sync(
                lambda sync_connection: command.downgrade(
                    _alembic_config(postgres_database_url, sync_connection), "base"
                )
            )

        remaining_tables = await _table_names(engine)
        assert "alembic_version" in remaining_tables
        assert not {
            "cooperatives",
            "products",
            "batches",
            "audit_logs",
        }.intersection(remaining_tables)
        async with engine.connect() as connection:
            assert await connection.scalar(text("SELECT version_num FROM alembic_version")) is None
    finally:
        await engine.dispose()
