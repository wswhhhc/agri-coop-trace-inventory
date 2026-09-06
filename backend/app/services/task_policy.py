from __future__ import annotations

from app.core.auth.authorization import permission_denied
from app.core.auth.context import AuthContext
from app.models import TaskRecord


def require_task_read(context: AuthContext, task: TaskRecord) -> None:
    """按任务所属领域保留既有读取权限边界。"""
    if task.task_type in {"MODEL_TRAINING", "DEMAND_FORECAST"}:
        permission = "model:read"
    elif task.task_type == "ALERT_SCAN":
        permission = "alert:read"
    elif task.task_type == "EXPORT_REPORT":
        report_type = str(task.request_payload.get("reportType", ""))
        if report_type == "INVENTORY_DETAIL":
            permission = "inventory:read"
        elif report_type == "ALERT_DETAIL":
            permission = "alert:read"
        else:
            raise permission_denied()
    else:
        raise permission_denied()
    if not context.has_permission(permission):
        raise permission_denied()


__all__ = ["require_task_read"]
