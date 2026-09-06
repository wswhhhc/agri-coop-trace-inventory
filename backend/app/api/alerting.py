from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api._pagination import build_pagination_meta
from app.core.auth.dependencies import CurrentAuthContext
from app.infrastructure.database import get_db_session
from app.models import Alert, AlertRule
from app.schemas.alerting import (
    AlertData,
    AlertListParams,
    AlertRuleData,
    AlertRuleUpdate,
    AlertStatusUpdate,
)
from app.schemas.common import ApiResponse, ListResponse
from app.services.alerting import AlertingService

router = APIRouter(tags=["alerting"])


def get_alerting_service(session: Annotated[AsyncSession, Depends(get_db_session)]) -> AlertingService:
    return AlertingService(session)


def _rule_data(rule: AlertRule) -> AlertRuleData:
    return AlertRuleData.model_validate(rule)


def _alert_data(alert: Alert) -> AlertData:
    return AlertData(
        id=alert.id,
        cooperative_id=alert.cooperative_id,
        rule_id=alert.rule_id,
        alert_type=alert.alert_type,
        severity=alert.severity,
        status=alert.status,
        warehouse_id=alert.warehouse_id,
        product_id=alert.product_id,
        batch_id=alert.batch_id,
        title=alert.title,
        message=alert.message,
        evidence=alert.evidence,
        detected_at=alert.detected_at,
        resolved_at=alert.resolved_at,
        assignee_id=alert.assignee_id,
        created_at=alert.created_at,
        updated_at=alert.updated_at,
        handling_logs=[
            {
                "id": log.id,
                "operatorId": log.operator_id,
                "fromStatus": log.from_status,
                "toStatus": log.to_status,
                "comment": log.comment,
                "createdAt": log.created_at,
            }
            for log in alert.handling_logs
        ],
    )


@router.get("/alert-rules", response_model=ListResponse[AlertRuleData])
async def list_alert_rules(
    context: CurrentAuthContext,
    service: Annotated[AlertingService, Depends(get_alerting_service)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 100,
) -> ListResponse[AlertRuleData]:
    rules, total = await service.list_rules(context, page, page_size)
    return ListResponse(data=[_rule_data(rule) for rule in rules], pagination=build_pagination_meta(total, page, page_size))


@router.patch("/alert-rules/{ruleId}", response_model=ApiResponse[AlertRuleData])
async def update_alert_rule(
    payload: AlertRuleUpdate,
    rule_id: Annotated[UUID, Path(alias="ruleId")],
    context: CurrentAuthContext,
    service: Annotated[AlertingService, Depends(get_alerting_service)],
) -> ApiResponse[AlertRuleData]:
    return ApiResponse(data=_rule_data(await service.update_rule(context, rule_id, payload)))


@router.get("/alerts", response_model=ListResponse[AlertData])
async def list_alerts(
    params: Annotated[AlertListParams, Query()],
    context: CurrentAuthContext,
    service: Annotated[AlertingService, Depends(get_alerting_service)],
) -> ListResponse[AlertData]:
    alerts, total = await service.list_alerts(context, params)
    return ListResponse(data=[_alert_data(alert) for alert in alerts], pagination=build_pagination_meta(total, params.page, params.page_size))


@router.get("/alerts/{alertId}", response_model=ApiResponse[AlertData])
async def get_alert(
    alert_id: Annotated[UUID, Path(alias="alertId")],
    context: CurrentAuthContext,
    service: Annotated[AlertingService, Depends(get_alerting_service)],
) -> ApiResponse[AlertData]:
    return ApiResponse(data=_alert_data(await service.get_alert(context, alert_id)))


@router.patch("/alerts/{alertId}", response_model=ApiResponse[AlertData])
async def update_alert(
    payload: AlertStatusUpdate,
    alert_id: Annotated[UUID, Path(alias="alertId")],
    context: CurrentAuthContext,
    service: Annotated[AlertingService, Depends(get_alerting_service)],
) -> ApiResponse[AlertData]:
    return ApiResponse(data=_alert_data(await service.update_alert(context, alert_id, payload)))


__all__ = ["get_alerting_service", "router"]
