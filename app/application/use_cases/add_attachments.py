"""
Use case: adicionar anexos a manifestação existente.
Apenas draft. Salva em storage por manifestation_id.
Extrai texto de imagens/áudios/vídeos localmente; anexa a extracted_text.
"""

import logging
from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.enums import AttachmentType, ManifestationStatus
from app.infrastructure.db.models import AttachmentModel, ManifestationModel
from app.infrastructure.storage.local_storage import LocalStorage
from app.utils.file_validation import (
    extension_from_mime,
    max_file_size_bytes,
    mime_to_attachment_type,
)

logger = logging.getLogger(__name__)


@dataclass
class AddAttachmentsInput:
    """Entrada do use case."""

    files: list[tuple[bytes, str, str]]  # (content, mime_type, original_filename)


@dataclass
class AddAttachmentsOutput:
    """Saída do use case."""

    manifestation_id: str
    added_count: int


class AddAttachmentsError(Exception):
    """Manifestação não encontrada ou não pode receber anexos."""

    pass


class ValidationError(Exception):
    """Arquivo inválido."""

    pass


async def add_attachments(
    session: AsyncSession,
    storage: LocalStorage,
    manifestation_id: str,
    inp: AddAttachmentsInput,
) -> AddAttachmentsOutput:
    """
    Adiciona anexos a manifestação draft.
    Valida MIME e tamanho. Retorna id e quantidade adicionada.
    """
    q = (
        select(ManifestationModel)
        .where(ManifestationModel.id == manifestation_id)
        .options(selectinload(ManifestationModel.attachments))
    )
    r = await session.execute(q)
    m = r.scalar_one_or_none()
    if not m:
        raise AddAttachmentsError("Manifestação não encontrada.")
    if m.status != ManifestationStatus.DRAFT:
        raise AddAttachmentsError("Apenas manifestações em rascunho podem receber novos anexos.")

    max_size = max_file_size_bytes()
    validated: list[tuple[bytes, str, AttachmentType]] = []

    for content, mime, _ in inp.files:
        if not content:
            continue
        if len(content) > max_size:
            raise ValidationError(
                f"Arquivo excede o tamanho máximo de {max_size / (1024*1024):.0f} MB."
            )
        atype = mime_to_attachment_type(mime)
        if not atype:
            raise ValidationError(f"MIME type não permitido: {mime}.")
        validated.append((content, mime, atype))

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
        logger.warning("Extração de mídia ignorada (add_attachments): %s", e, exc_info=True)

    if parts:
        existing = (m.extracted_text or "").strip()
        new = "\n\n---\n\n".join(parts)
        m.extracted_text = f"{existing}\n\n---\n\n{new}".strip() if existing else new
        await session.flush()

    return AddAttachmentsOutput(manifestation_id=m.id, added_count=len(validated))
