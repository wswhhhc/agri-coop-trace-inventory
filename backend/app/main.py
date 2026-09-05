from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import get_settings
from app.core.logging_config import configure_logging

settings = get_settings()
configure_logging(settings)

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    debug=settings.debug,
    docs_url="/docs" if settings.docs_enabled else None,
    redoc_url="/redoc" if settings.docs_enabled else None,
    openapi_url=f"{settings.api_v1_prefix}/openapi.json"
    if settings.docs_enabled
    else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
    expose_headers=settings.cors_exposed_headers,
)

if settings.trusted_host_list:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_host_list)


@app.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    return {"status": "ok", "environment": settings.app_env}
