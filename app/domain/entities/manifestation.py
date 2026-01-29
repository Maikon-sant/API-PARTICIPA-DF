"""
Entidade de domínio: Manifestação.
Representa uma manifestação registrada na ouvidoria (texto, áudio, imagem, vídeo).
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.domain.enums import Channel, ManifestationStatus


@dataclass
class Manifestation:
    """Manifestação na ouvidoria."""

    id: UUID
    protocol: str
    channel: Channel
    text: Optional[str]
    anonymous: bool
    status: ManifestationStatus
    created_at: datetime

    def __post_init__(self) -> None:
        if isinstance(self.channel, str):
            self.channel = Channel(self.channel)
        if isinstance(self.status, str):
            self.status = ManifestationStatus(self.status)
