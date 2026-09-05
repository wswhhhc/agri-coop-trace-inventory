from __future__ import annotations

import pytest

from app import main


@pytest.mark.asyncio
async def test_application_lifespan_disposes_database_resources(monkeypatch) -> None:
    state = {"disposed": False}

    async def fake_dispose_database_engine() -> None:
        state["disposed"] = True

    monkeypatch.setattr(main, "dispose_database_engine", fake_dispose_database_engine)

    async with main.lifespan(main.app):
        assert state["disposed"] is False

    assert state["disposed"] is True
