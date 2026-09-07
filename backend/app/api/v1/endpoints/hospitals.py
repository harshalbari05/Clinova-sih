"""Hospital directory API endpoints.

Routes:
    GET /api/v1/hospitals — List public hospital directory.

Access:
    Public and read-only. No authentication required.
    Allows patients to select an active facility during registration and consultation creation.
"""

from fastapi import APIRouter, status

from app.api.deps import DatabaseDep
from app.schemas.hospital import HospitalDirectoryResponse
from app.services import hospital_service

router = APIRouter()


@router.get(
    "",
    response_model=list[HospitalDirectoryResponse],
    status_code=status.HTTP_200_OK,
    summary="List Hospital Directory",
    description=(
        "Returns a public directory of available hospital facilities ordered alphabetically by name. "
        "Exposes only public non-sensitive fields (id, name, city, state) for patient facility selection."
    ),
)
async def list_hospitals(
    db: DatabaseDep,
) -> list[HospitalDirectoryResponse]:
    """Retrieve public hospital directory."""
    return await hospital_service.list_active_hospitals(db)
