"""
Rotas admin (demonstração, sem autenticação).
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.list_manifestations import list_manifestations
from app.infrastructure.db.session import get_db
from app.schemas.manifestation import ManifestationListItem, ManifestationsListResponse

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get(
    "/manifestations",
    response_model=ManifestationsListResponse,
    summary="Listar manifestações (admin)",
    description="Lista manifestações com paginação. Apenas para demonstração.",
)
async def admin_list_manifestations(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Página"),
    per_page: int = Query(20, ge=1, le=100, description="Itens por página"),
) -> ManifestationsListResponse:
    items, total = await list_manifestations(db, page=page, per_page=per_page)
    return ManifestationsListResponse(
        total=total,
        page=page,
        per_page=per_page,
        items=[ManifestationListItem(**x) for x in items],
    )
