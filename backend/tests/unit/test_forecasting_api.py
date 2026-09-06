from app.api.forecasting import router
from app.tasks.forecasting_tasks import forecast_demand_task, train_model_task
from fastapi.routing import APIRoute


def test_forecasting_routes_match_interface_contract() -> None:
    routes = {(route.path, method) for route in router.routes if isinstance(route, APIRoute) for method in route.methods}
    assert ("/model-training-tasks", "POST") in routes
    assert ("/model-versions", "GET") in routes
    assert ("/model-versions/{modelVersionId}", "GET") in routes
    assert ("/model-activations", "POST") in routes
    assert ("/forecast-tasks", "POST") in routes
    assert ("/forecast-results", "GET") in routes
    assert ("/forecast-results/{forecastResultId}", "GET") in routes
    assert ("/tasks/{taskId}", "GET") in routes


def test_forecasting_tasks_have_stable_names() -> None:
    assert train_model_task.name == "app.tasks.forecasting_tasks.train_model_task"
    assert forecast_demand_task.name == "app.tasks.forecasting_tasks.forecast_demand_task"
