"""
Validação de arquivos: MIME types permitidos e tamanho máximo.
Preparado para regras da ouvidoria governamental.
"""

from typing import Tuple

from app.core.config import get_settings
from app.domain.enums import AttachmentType


def get_allowed_mimes() -> Tuple[list[str], list[str], list[str]]:
    """Retorna (audio_mimes, image_mimes, video_mimes)."""
    s = get_settings()
    return (s.allowed_audio_mimes, s.allowed_image_mimes, s.allowed_video_mimes)


def max_file_size_bytes() -> int:
    """Tamanho máximo por arquivo em bytes."""
    return get_settings().max_file_size_bytes


def mime_to_attachment_type(mime: str) -> AttachmentType | None:
    """
    Mapeia MIME type para AttachmentType.
    Retorna None se não permitido.
    """
    mime = (mime or "").strip().lower()
    audio, image, video = get_allowed_mimes()
    if mime in audio:
        return AttachmentType.AUDIO
    if mime in image:
        return AttachmentType.IMAGE
    if mime in video:
        return AttachmentType.VIDEO
    return None


def extension_from_mime(mime: str) -> str:
    """Extrai extensão típica do MIME (para salvar arquivo)."""
    m = (mime or "").strip().lower()
    map_ = {
        "audio/mpeg": "mp3",
        "audio/mp3": "mp3",
        "audio/wav": "wav",
        "audio/x-wav": "wav",
        "audio/webm": "webm",
        "audio/ogg": "ogg",
        "image/jpeg": "jpg",
        "image/jpg": "jpg",
        "image/png": "png",
        "image/gif": "gif",
        "image/webp": "webp",
        "video/mp4": "mp4",
        "video/webm": "webm",
        "video/ogg": "ogv",
    }
    return map_.get(m, "bin")
