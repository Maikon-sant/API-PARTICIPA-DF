"""
Use case: listar manifestações (admin).
Paginação simples. Inclui drafts (protocol null) e finalizadas.
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.db.models import ManifestationModel


async def list_manifestations(
    session: AsyncSession,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[dict], int]:
    """
    Lista manifestações com paginação.
    Retorna (lista de itens, total).
    Cada item: id, protocol, input_type, anonymous, status, created_at, attachments_count.
    """
    count_q = select(func.count()).select_from(ManifestationModel)
    total_r = await session.execute(count_q)
    total = total_r.scalar() or 0

    offset = max(0, (page - 1) * per_page)
    per_page = max(1, min(per_page, 100))

    q = (
        select(ManifestationModel)
        .options(selectinload(ManifestationModel.attachments))
        .order_by(ManifestationModel.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    r = await session.execute(q)
    rows = r.scalars().all()

    items = [
        {
            "id": m.id,
            "protocol": m.protocol,
            "input_type": m.input_type.value,
            "anonymous": m.anonymous,
            "status": m.status.value,
            "created_at": m.created_at,
            "attachments_count": len(m.attachments),
        }
        for m in rows
    ]
    return items, total
