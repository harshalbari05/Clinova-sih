from typing import Dict
from fastapi import APIRouter, status

router = APIRouter()


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Returns the operational status of the Clinova API backend.",
    response_model=Dict[str, str],
)
async def health_check() -> Dict[str, str]:
    return {"status": "ok"}
