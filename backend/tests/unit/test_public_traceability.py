from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.core.exceptions import AppException
from app.models import (
    InspectionConclusion,
    QualityInspection,
    QualityInspectionItem,
    TraceEvent,
    TraceEventType,
)
from app.services.traceability import PublicTraceabilityService, TraceabilityCache
from redis.exceptions import RedisError
from tests.factories import batch_factory

pytestmark = pytest.mark.postgres


class MemoryRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.get_count = 0
        self.set_count = 0
        self.delete_count = 0

    async def get(self, key: str) -> str | None:
        self.get_count += 1
        return self.values.get(key)

    async def set(self, key: str, value: str, *, ex: int) -> bool:
        self.set_count += 1
        self.values[key] = value
        return True

    async def delete(self, key: str) -> int:
        self.delete_count += 1
        return int(self.values.pop(key, None) is not None)


class BrokenRedis(MemoryRedis):
    async def get(self, key: str) -> str | None:
        raise RedisError("redis unavailable")

    async def set(self, key: str, value: str, *, ex: int) -> bool:
        raise RedisError("redis unavailable")


async def _create_trace_fixture(postgres_session):
    batch = batch_factory()
    postgres_session.add(batch)
    await postgres_session.flush()
    inspection = QualityInspection(
        cooperative_id=batch.cooperative_id,
        batch_id=batch.id,
        inspection_no="QC-PUBLIC-001",
        inspected_at=datetime(2026, 9, 5, 9, tzinfo=UTC),
        inspector_id=batch.created_by,
        conclusion=InspectionConclusion.PASSED,
        remarks="内部质检备注不得公开",
        items=[
            QualityInspectionItem(
                item_name="水分含量",
                result_value="13.2",
                unit="%",
                standard_value="≤14.0%",
                is_qualified=True,
                sort_order=0,
            )
        ],
    )
    postgres_session.add_all(
        [
            inspection,
            TraceEvent(
                cooperative_id=batch.cooperative_id,
                batch_id=batch.id,
                event_type=TraceEventType.PRODUCTION,
                title="生产批次建立",
                description="内部描述不应直接作为公开描述",
                event_time=datetime(2026, 9, 5, 8, tzinfo=UTC),
                public_data={},
                created_by=batch.created_by,
            ),
            TraceEvent(
                cooperative_id=batch.cooperative_id,
                batch_id=batch.id,
                event_type=TraceEventType.INSPECTION,
                title="质量检验完成",
                description="检验结论：PASSED；内部备注",
                event_time=datetime(2026, 9, 5, 9, tzinfo=UTC),
                public_data={"conclusion": "PASSED"},
                created_by=batch.created_by,
            ),
        ]
    )
    await postgres_session.commit()
    return batch


@pytest.mark.asyncio
async def test_public_trace_projects_safe_data_and_caches_result(postgres_session) -> None:
    batch = await _create_trace_fixture(postgres_session)
    redis = MemoryRedis()
    service = PublicTraceabilityService(
        postgres_session,
        TraceabilityCache(redis, key_prefix="test:", ttl_seconds=600),
    )

    result = await service.get_public(batch.trace_code)

    assert result.trace_code == batch.trace_code
    assert result.product.name == "测试农产品"
    assert result.product.category_name.startswith("分类-")
    assert result.batch.batch_no == batch.batch_no
    assert result.latest_inspection is not None
    assert result.latest_inspection.conclusion is InspectionConclusion.PASSED
    assert result.latest_inspection.items[0].name == "水分含量"
    assert result.timeline[0].event_type is TraceEventType.PRODUCTION
    assert result.timeline[1].description == "检验结论：PASSED"
    assert "remarks" not in result.latest_inspection.model_dump()
    assert "内部" not in result.timeline[0].description
    assert redis.set_count == 1

    cached = await service.get_public(batch.trace_code)
    assert cached == result
    assert redis.get_count == 2
    assert redis.set_count == 1

    await service.cache.invalidate(batch.trace_code)
    refreshed = await service.get_public(batch.trace_code)
    assert refreshed == result
    assert redis.delete_count == 1
    assert redis.set_count == 2


@pytest.mark.asyncio
async def test_public_trace_cache_failure_falls_back_to_database(postgres_session) -> None:
    batch = await _create_trace_fixture(postgres_session)
    service = PublicTraceabilityService(
        postgres_session,
        TraceabilityCache(BrokenRedis(), key_prefix="test:", ttl_seconds=600),
    )

    result = await service.get_public(batch.trace_code)

    assert result.trace_code == batch.trace_code


@pytest.mark.asyncio
async def test_public_trace_invalid_code_returns_not_found(postgres_session) -> None:
    service = PublicTraceabilityService(
        postgres_session,
        TraceabilityCache(MemoryRedis(), key_prefix="test:", ttl_seconds=600),
    )

    with pytest.raises(AppException) as error:
        await service.get_public("tr-does-not-exist")

    assert error.value.status_code == 404


def test_public_trace_cache_key_and_json_are_namespaced() -> None:
    redis = MemoryRedis()
    cache = TraceabilityCache(redis, key_prefix="agri:", ttl_seconds=60)

    assert cache.key("tr_abc") == "agri:trace:tr_abc"
