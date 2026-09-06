from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.alerting import router as alerting_router
from app.api.auth import router as auth_router
from app.api.batches import router as batches_router
from app.api.cooperatives import router as cooperatives_router
from app.api.files import router as files_router
from app.api.inventory import router as inventory_router
from app.api.products import category_router, product_router
from app.api.quality_inspections import router as quality_inspections_router
from app.api.traceability import public_router as public_traceability_router
from app.api.traceability import router as traceability_router
from app.api.users import router as users_router
from app.api.warehouses import router as warehouses_router
from app.core.config import Settings, get_settings
from app.core.exceptions import (
    register_exception_handlers,
    request_id_middleware,
)
from app.core.logging_config import configure_logging
from app.infrastructure.database import (
    dispose_database_engine,
    initialize_database,
)
from app.infrastructure.redis import dispose_redis_client, initialize_redis
from app.schemas.common import ApiResponse

settings = get_settings()
configure_logging(settings)
initialize_database(settings)
initialize_redis(settings)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """管理应用级数据库连接池生命周期。"""
    try:
        yield
    finally:
        await dispose_database_engine()
        await dispose_redis_client()

def create_app(app_settings: Settings | None = None) -> FastAPI:
    """根据配置创建应用，便于生产启动和隔离测试复用同一套注册逻辑。"""
    app_settings = app_settings or settings
    application = FastAPI(
        title=app_settings.app_name,
        version="0.1.0",
        debug=app_settings.debug,
        lifespan=lifespan,
        docs_url="/docs" if app_settings.docs_enabled else None,
        redoc_url="/redoc" if app_settings.docs_enabled else None,
        openapi_url=f"{app_settings.api_v1_prefix}/openapi.json"
        if app_settings.docs_enabled
        else None,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_credentials=app_settings.cors_allow_credentials,
        allow_methods=app_settings.cors_methods,
        allow_headers=app_settings.cors_headers,
        expose_headers=app_settings.cors_exposed_headers,
    )
    if app_settings.trusted_host_list:
        application.add_middleware(
            TrustedHostMiddleware, allowed_hosts=app_settings.trusted_host_list
        )
    application.middleware("http")(request_id_middleware)
    register_exception_handlers(application)
    application.include_router(auth_router, prefix=app_settings.api_v1_prefix)
    application.include_router(cooperatives_router, prefix=app_settings.api_v1_prefix)
    application.include_router(warehouses_router, prefix=app_settings.api_v1_prefix)
    application.include_router(users_router, prefix=app_settings.api_v1_prefix)
    application.include_router(category_router, prefix=app_settings.api_v1_prefix)
    application.include_router(product_router, prefix=app_settings.api_v1_prefix)
    application.include_router(batches_router, prefix=app_settings.api_v1_prefix)
    application.include_router(inventory_router, prefix=app_settings.api_v1_prefix)
    application.include_router(alerting_router, prefix=app_settings.api_v1_prefix)
    application.include_router(files_router, prefix=app_settings.api_v1_prefix)
    application.include_router(
        quality_inspections_router, prefix=app_settings.api_v1_prefix
    )
    application.include_router(traceability_router, prefix=app_settings.api_v1_prefix)
    application.include_router(public_traceability_router, prefix=app_settings.api_v1_prefix)

    @application.get(
        "/health",
        response_model=ApiResponse[dict[str, str]],
        tags=["system"],
    )
    async def health_check() -> ApiResponse[dict[str, str]]:
        return ApiResponse(
            data={"status": "ok", "environment": app_settings.app_env}
        )

    return application


app = create_app()
