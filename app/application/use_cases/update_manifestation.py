"""
Use case: atualizar manifestação (PATCH).
Atualiza qualquer etapa do fluxo. Apenas draft pode ser alterado.
"""

from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import ManifestationStatus
from app.infrastructure.db.models import ManifestationModel


@dataclass
class UpdateManifestationInput:
    """Entrada do use case. Apenas campos enviados."""

    original_text: str | None = None
    subject_id: str | None = None
    subject_label: str | None = None
    complementary_tags: list[str] | None = None
    summary: str | None = None
    location_lat: float | None = None
    location_lng: float | None = None
    location_description: str | None = None
    administrative_region: str | None = None
    anonymous: bool | None = None
    contact_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None


@dataclass
class UpdateManifestationOutput:
    """Saída do use case."""

    id: str
    protocol: str | None
    status: str


class UpdateError(Exception):
    """Manifestação não encontrada ou não pode ser alterada."""

    pass


async def update_manifestation(
    session: AsyncSession,
    manifestation_id: str,
    inp: UpdateManifestationInput,
) -> UpdateManifestationOutput:
    """
    Atualiza manifestação por id.
    Apenas draft pode ser alterado. Retorna id, protocol, status.
    """
    q = select(ManifestationModel).where(ManifestationModel.id == manifestation_id)
    r = await session.execute(q)
    m = r.scalar_one_or_none()
    if not m:
        raise UpdateError("Manifestação não encontrada.")
    if m.status != ManifestationStatus.DRAFT:
        raise UpdateError("Apenas manifestações em rascunho podem ser alteradas.")

    updates: dict[str, Any] = {}
    if inp.original_text is not None:
        updates["original_text"] = inp.original_text.strip() or None
    if inp.subject_id is not None:
        updates["subject_id"] = inp.subject_id or None
    if inp.subject_label is not None:
        updates["subject_label"] = inp.subject_label or None
    if inp.complementary_tags is not None:
        updates["complementary_tags"] = inp.complementary_tags
    if inp.summary is not None:
        updates["summary"] = inp.summary.strip() or None
    if inp.location_lat is not None:
        updates["location_lat"] = inp.location_lat
    if inp.location_lng is not None:
        updates["location_lng"] = inp.location_lng
    if inp.location_description is not None:
        updates["location_description"] = inp.location_description.strip() or None
    if inp.administrative_region is not None:
        updates["administrative_region"] = inp.administrative_region.strip() or None
    if inp.anonymous is not None:
        updates["anonymous"] = inp.anonymous
    if inp.contact_name is not None:
        updates["contact_name"] = inp.contact_name.strip() or None
    if inp.contact_email is not None:
        updates["contact_email"] = inp.contact_email.strip() or None
    if inp.contact_phone is not None:
        updates["contact_phone"] = inp.contact_phone.strip() or None

    for k, v in updates.items():
        setattr(m, k, v)

    await session.flush()
    return UpdateManifestationOutput(
        id=m.id,
        protocol=m.protocol,
        status=m.status.value,
    )
