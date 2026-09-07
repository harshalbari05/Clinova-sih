import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_router
from app.core.config import settings

logger = logging.getLogger("clinova.api")


def create_application() -> FastAPI:
    """FastAPI application factory."""
    docs_url = "/docs" if settings.docs_enabled else None
    redoc_url = "/redoc" if settings.docs_enabled else None
    openapi_url = f"{settings.API_V1_STR}/openapi.json" if settings.docs_enabled else None

    application = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=openapi_url,
        docs_url=docs_url,
        redoc_url=redoc_url,
        description="Clinova Platform Central API Service",
        version="1.0.0",
        debug=settings.DEBUG,
    )

    # Set up CORS middleware from environment configuration
    if settings.BACKEND_CORS_ORIGINS:
        origins = [str(origin) for origin in settings.BACKEND_CORS_ORIGINS]
        allow_all = "*" in origins
        application.add_middleware(
            CORSMiddleware,
            allow_origins=["*"] if allow_all else origins,
            allow_credentials=not allow_all,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Global exception handler to mask internal traces in production
    @application.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        if isinstance(exc, StarletteHTTPException):
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
                headers=getattr(exc, "headers", None),
            )
        logger.error(
            f"Unhandled server exception on {request.method} {request.url.path}: {exc}",
            exc_info=True,
        )
        if settings.is_production and not settings.DEBUG:
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error. Please contact system administration."},
            )
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc)},
        )

    # Mount API v1 Router
    application.include_router(api_router, prefix=settings.API_V1_STR)

    @application.get("/", tags=["Root"], summary="Root service status")
    async def root():
        return {
            "name": settings.PROJECT_NAME,
            "environment": settings.ENVIRONMENT,
            "version": "1.0.0",
            "docs": "/docs" if settings.docs_enabled else None,
            "health": f"{settings.API_V1_STR}/health",
        }

    return application


app = create_application()
