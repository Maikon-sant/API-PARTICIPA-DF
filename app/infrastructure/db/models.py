"""
Modelos ORM (SQLAlchemy) para Manifestation e Attachment.
Mapeiam as entidades de domínio para o banco MySQL.
Compatível com MySQL: UUID como String(36), Enum nativo, JSON para complementary_tags.
"""

import uuid
from datetime import datetime
from typing import List

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Enum as SQLEnum,
)
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import AttachmentType, InputType, ManifestationStatus
from app.infrastructure.db.base import Base


def _gen_uuid_str() -> str:
    """Gera UUID como string (36 chars) para armazenamento em MySQL."""
    return str(uuid.uuid4())


class ManifestationModel(Base):
    """Modelo ORM: manifestação.
    Fluxo: início (texto/áudio/imagem/vídeo) → assunto → local → identificação → anexos → protocolo.
    """

    __tablename__ = "manifestations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_gen_uuid_str)
    protocol: Mapped[str | None] = mapped_column(String(32), unique=True, index=True, nullable=True)
    input_type: Mapped[InputType] = mapped_column(
        SQLEnum(
            InputType,
            name="input_type_enum",
            create_constraint=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )
    original_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    subject_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    subject_label: Mapped[str | None] = mapped_column(String(256), nullable=True)
    complementary_tags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    location_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_description: Mapped[str | None] = mapped_column(String(512), nullable=True)
    administrative_region: Mapped[str | None] = mapped_column(String(128), nullable=True)
    anonymous: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    contact_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(256), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[ManifestationStatus] = mapped_column(
        SQLEnum(
            ManifestationStatus,
            name="status_enum",
            create_constraint=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        default=ManifestationStatus.DRAFT,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    attachments: Mapped[List["AttachmentModel"]] = relationship(
        "AttachmentModel",
        back_populates="manifestation",
        cascade="all, delete-orphan",
    )


class AttachmentModel(Base):
    """Modelo ORM: anexo."""

    __tablename__ = "attachments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_gen_uuid_str)
    manifestation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("manifestations.id", ondelete="CASCADE"),
        nullable=False,
    )
    type: Mapped[AttachmentType] = mapped_column(
        SQLEnum(
            AttachmentType,
            name="attachment_type_enum",
            create_constraint=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    manifestation: Mapped["ManifestationModel"] = relationship(
        "ManifestationModel",
        back_populates="attachments",
    )
