from app.api.export import router
from app.tasks.export_tasks import generate_export_task
from fastapi.routing import APIRoute


def test_export_router_matches_interface_contract() -> None:
    routes = {
        (route.path, method)
        for route in router.routes
        if isinstance(route, APIRoute)
        for method in route.methods
    }
    assert ("/export-tasks", "POST") in routes


def test_export_task_has_stable_name() -> None:
    assert generate_export_task.name == "app.tasks.export_tasks.generate_export_task"
