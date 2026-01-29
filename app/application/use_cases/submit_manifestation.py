"""
Use case: finalizar manifestação (submit).
Gera protocolo definitivo e altera status para received.
"""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.domain.enums import ManifestationStatus
from app.infrastructure.db.models import ManifestationModel


@dataclass
class SubmitManifestationOutput:
    """Saída do use case."""

    protocol: str
    status: str


class SubmitError(Exception):
    """Manifestação não encontrada ou não pode ser finalizada."""

    pass


async def _next_protocol(session: AsyncSession) -> str:
    """Gera próximo protocolo único no formato DF-2026-000001.
    Considera apenas manifestações já finalizadas (protocol IS NOT NULL).
    """
    cfg = get_settings()
    prefix = f"{cfg.protocol_prefix}-{cfg.protocol_year}-"
    q = (
        select(ManifestationModel.protocol)
        .where(
            ManifestationModel.protocol.isnot(None),
            ManifestationModel.protocol.startswith(prefix),
        )
        .order_by(ManifestationModel.protocol.desc())
        .limit(1)
    )
    r = await session.execute(q)
    last = r.scalar_one_or_none()
    if not last:
        n = 1
    else:
        try:
            n = int(last[len(prefix) :]) + 1
        except ValueError:
            n = 1
    return f"{prefix}{n:06d}"


async def submit_manifestation(
    session: AsyncSession,
    manifestation_id: str,
) -> SubmitManifestationOutput:
    """
    Finaliza manifestação draft.
    Gera protocolo definitivo, define status=received.
    Acompanhamento será apenas por protocolo.
    """
    q = select(ManifestationModel).where(ManifestationModel.id == manifestation_id)
    r = await session.execute(q)
    m = r.scalar_one_or_none()
    if not m:
        raise SubmitError("Manifestação não encontrada.")
    if m.status != ManifestationStatus.DRAFT:
        raise SubmitError("Apenas manifestações em rascunho podem ser finalizadas.")

    protocol = await _next_protocol(session)
    m.protocol = protocol
    m.status = ManifestationStatus.RECEIVED
    await session.flush()

    return SubmitManifestationOutput(protocol=protocol, status=ManifestationStatus.RECEIVED.value)
