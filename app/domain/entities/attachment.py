"""
Entidade de domínio: Anexo.
Representa um arquivo (áudio, imagem ou vídeo) vinculado a uma manifestação.
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.enums import AttachmentType


@dataclass
class Attachment:
    """Anexo de uma manifestação."""

    id: UUID
    manifestation_id: UUID
    type: AttachmentType
    mime_type: str
    size_bytes: int
    file_path: str
    created_at: datetime

    def __post_init__(self) -> None:
        if isinstance(self.type, str):
            self.type = AttachmentType(self.type)
