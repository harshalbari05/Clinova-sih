from fastapi import APIRouter, status

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
