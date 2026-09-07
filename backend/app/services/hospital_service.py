"""Hospital service layer.

Responsibilities:
- Provide public read-only directory of active hospital facilities.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hospital import Hospital
from app.schemas.hospital import HospitalDirectoryResponse

__all__ = [
    "list_active_hospitals",
]


async def list_active_hospitals(db: AsyncSession) -> list[HospitalDirectoryResponse]:
    """Retrieve all available hospital facilities ordered alphabetically by name.

    Returns public, safe directory information (id, name, city, state)
    suitable for unauthenticated patient registration and facility selection.
    """
    stmt = select(Hospital).order_by(Hospital.name.asc())
    rows = (await db.execute(stmt)).scalars().all()
    return [HospitalDirectoryResponse.model_validate(h) for h in rows]
