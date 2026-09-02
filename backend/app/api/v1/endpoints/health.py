from typing import Any

from fastapi import APIRouter, status

from app.db.session import check_db_connectivity

router = APIRouter()


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Returns the operational status of the Clinova API backend.",
    response_model=dict[str, str],
)
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get(
    "/health/db",
    status_code=status.HTTP_200_OK,
    summary="Database Health Check",
    description="Returns the live database connectivity status.",
    response_model=dict[str, Any],
)
async def db_health_check() -> dict[str, Any]:
    connected = await check_db_connectivity()
    return {
        "status": "ok" if connected else "disconnected",
        "database": "connected" if connected else "disconnected",
    }
