"""
Use case: obter manifestação por protocolo.
Retorna detalhes e quantidade de anexos (apenas manifestações finalizadas).
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.db.models import ManifestationModel


async def get_manifestation_by_protocol(
    session: AsyncSession,
    protocol: str,
) -> dict | None:
    """
    Busca manifestação por protocolo (apenas finalizadas).
    Retorna dict com protocol, status, input_type, created_at, attachments_count,
    subject_label, summary ou None se não encontrada.
    """
    q = (
        select(ManifestationModel)
        .where(ManifestationModel.protocol == protocol)
        .options(selectinload(ManifestationModel.attachments))
    )
    r = await session.execute(q)
    m = r.scalar_one_or_none()
    if not m:
        return None
    return {
        "protocol": m.protocol,
        "status": m.status.value,
        "input_type": m.input_type.value,
        "created_at": m.created_at,
        "attachments_count": len(m.attachments),
        "subject_label": m.subject_label,
        "summary": m.summary,
        "extracted_text": m.extracted_text,
    }
