"""需求预测 Celery 入口；实际训练/预测流水线在 forecasting service 中执行。"""

from celery import Task  # type: ignore[import-untyped]

from app.tasks.celery_app import celery_app


@celery_app.task(
    bind=True,
    name="app.tasks.forecasting_tasks.train_model_task",
    acks_late=True,
    track_started=True,
)
def train_model_task(self: Task, task_record_id: str) -> dict[str, str]:
    # F4 将接入真实数据库流水线；保留稳定任务名供 API 和 worker 注册使用。
    return {"taskRecordId": task_record_id, "status": "PENDING"}


@celery_app.task(
    bind=True,
    name="app.tasks.forecasting_tasks.forecast_demand_task",
    acks_late=True,
    track_started=True,
)
def forecast_demand_task(self: Task, task_record_id: str) -> dict[str, str]:
    return {"taskRecordId": task_record_id, "status": "PENDING"}


__all__ = ["forecast_demand_task", "train_model_task"]
