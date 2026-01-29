"""
Use case: criar manifestação (draft).
Início por texto, áudio, imagem ou vídeo. Status draft, sem protocolo.
Extrai texto de imagens/áudios/vídeos localmente (OCR, Whisper); persiste em extracted_text.
"""

import logging
from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import AttachmentType, InputType, ManifestationStatus
from app.infrastructure.db.models import AttachmentModel, ManifestationModel
from app.infrastructure.storage.local_storage import LocalStorage
from app.utils.file_validation import (
    extension_from_mime,
    max_file_size_bytes,
    mime_to_attachment_type,
)

logger = logging.getLogger(__name__)


@dataclass
class CreateManifestationInput:
    """Entrada do use case."""

    original_text: str | None
    files: list[tuple[bytes, str, str]]  # (content, mime_type, original_filename)
    subject_id: str | None
    subject_label: str | None
    complementary_tags: list[str] | None
    summary: str | None
    location_lat: float | None
    location_lng: float | None
    location_description: str | None
    administrative_region: str | None
    anonymous: bool
    contact_name: str | None
    contact_email: str | None
    contact_phone: str | None


@dataclass
class CreateManifestationOutput:
    """Saída do use case."""

    id: str
    protocol: str | None
    status: str


class ValidationError(Exception):
    """Erro de validação (arquivo inválido, etc.)."""

    pass


def _detect_input_type(has_text: bool, types: set[AttachmentType]) -> InputType:
    """Detecta input_type a partir de texto e tipos de anexo."""
    has_audio = AttachmentType.AUDIO in types
    has_image = AttachmentType.IMAGE in types
    has_video = AttachmentType.VIDEO in types
    file_count = sum([has_audio, has_image, has_video])
    if file_count > 1 or (has_text and file_count >= 1):
        return InputType.MIXED
    if has_audio:
        return InputType.AUDIO
    if has_image:
        return InputType.IMAGE
    if has_video:
        return InputType.VIDEO
    if has_text:
        return InputType.TEXT
    return InputType.TEXT  # fallback


async def create_manifestation(
    session: AsyncSession,
    storage: LocalStorage,
    inp: CreateManifestationInput,
) -> CreateManifestationOutput:
    """
    Cria manifestação como draft.
    - Exige pelo menos texto ou um arquivo.
    - Valida MIME e tamanho dos arquivos.
    - Detecta input_type automaticamente.
    - Sem protocolo até submit.
    """
    has_text = bool(inp.original_text and inp.original_text.strip())
    if not has_text and not inp.files:
        raise ValidationError(
            "Informe o conteúdo da manifestação: texto e/ou pelo menos um arquivo (áudio, imagem ou vídeo)."
        )

    max_size = max_file_size_bytes()
    validated: list[tuple[bytes, str, AttachmentType]] = []

    for content, mime, _ in inp.files:
        if len(content) > max_size:
            raise ValidationError(
                f"Arquivo excede o tamanho máximo de {max_size / (1024*1024):.0f} MB."
            )
        atype = mime_to_attachment_type(mime)
        if not atype:
            raise ValidationError(f"MIME type não permitido: {mime}.")
        validated.append((content, mime, atype))

    types = {t for (_, _, t) in validated}
    input_type = _detect_input_type(has_text, types)

    m = ManifestationModel(
        protocol=None,
        input_type=input_type,
        original_text=inp.original_text.strip() if has_text else None,
        subject_id=inp.subject_id,
        subject_label=inp.subject_label,
        complementary_tags=inp.complementary_tags if inp.complementary_tags else None,
        summary=inp.summary,
        location_lat=inp.location_lat,
        location_lng=inp.location_lng,
        location_description=inp.location_description,
        administrative_region=inp.administrative_region,
        anonymous=inp.anonymous,
        contact_name=inp.contact_name,
        contact_email=inp.contact_email,
        contact_phone=inp.contact_phone,
        status=ManifestationStatus.DRAFT,
    )
    session.add(m)
    await session.flush()

    saved: list[tuple[str, str, AttachmentType]] = []  # (rel_path, abs_path, atype)
    for content, mime, atype in validated:
        att_id = str(uuid4())
        ext = extension_from_mime(mime)
        rel_path = storage.save(m.id, att_id, content, ext)
        abs_path = storage.full_path(rel_path).resolve()
        
        from pathlib import Path
        abs_path_obj = Path(abs_path)
        if not abs_path_obj.exists():
            logger.error("Arquivo não existe após salvar: %s (rel: %s, size: %d bytes, base: %s)", abs_path, rel_path, len(content), storage._base)
            continue
        
        if not abs_path_obj.is_file():
            logger.error("Path não é arquivo após salvar: %s (rel: %s)", abs_path, rel_path)
            continue
        
        file_size = abs_path_obj.stat().st_size
        if file_size != len(content):
            logger.error("Tamanho incorreto após salvar: %s (esperado: %d, obtido: %d)", abs_path, len(content), file_size)
            continue
        
        abs_path_str = str(abs_path_obj.absolute())
        logger.info("Arquivo salvo e verificado: %s (size: %d bytes, tipo: %s)", abs_path_str, file_size, atype.value)
        saved.append((rel_path, abs_path_str, atype))
        a = AttachmentModel(
            id=att_id,
            manifestation_id=m.id,
            type=atype,
            mime_type=mime,
            size_bytes=len(content),
            file_path=rel_path,
        )
        session.add(a)

    await session.flush()

    parts: list[str] = []
    try:
        from app.media.dispatcher import extract_from_file
        from pathlib import Path

        for rel_path, abs_path_str, atype in saved:
            abs_path = Path(abs_path_str)
            if not abs_path.exists():
                logger.error("Arquivo não encontrado para extração: %s (rel: %s, abs_path_str: %s)", abs_path, rel_path, abs_path_str)
                continue
            
            if not abs_path.is_file():
                logger.error("Path não é arquivo para extração: %s (rel: %s)", abs_path, rel_path)
                continue
            
            file_size = abs_path.stat().st_size
            if file_size == 0:
                logger.warning("Arquivo vazio para extração: %s (rel: %s)", abs_path, rel_path)
                continue
            
            logger.info("Iniciando extração: %s (tipo: %s, size: %d bytes)", abs_path_str, atype.value, file_size)
            res = await extract_from_file(atype, abs_path_str)
            if res.get("raw_text", "").strip():
                parts.append(res["raw_text"].strip())
    except Exception as e:
        logger.warning("Extração de mídia ignorada (create): %s", e, exc_info=True)

    if parts:
        m.extracted_text = "\n\n---\n\n".join(parts)
        await session.flush()

    return CreateManifestationOutput(id=m.id, protocol=None, status=ManifestationStatus.DRAFT.value)
