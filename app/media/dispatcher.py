"""
Dispatcher: roteia por tipo de mídia (imagem, áudio, vídeo) e chama o extrator correto.
Usa image_ocr, audio_transcription e video_processing. Nunca levanta exceção.
"""

import logging
from pathlib import Path

from app.domain.enums import AttachmentType
from app.media.audio_transcription import extract_text_from_audio
from app.media.image_ocr import extract_text_from_image
from app.media.utils import run_sync
from app.media.video_processing import extract_text_from_video

logger = logging.getLogger(__name__)


def _extract_sync(attachment_type: AttachmentType, path: str) -> str:
    """Extração síncrona. Roda em thread."""
    p = Path(path).resolve()
    if not p.exists():
        logger.warning("Dispatcher: arquivo não existe para extração: %s (tipo: %s, original: %s)", p, attachment_type.value, path)
        return ""
    
    if not p.is_file():
        logger.warning("Dispatcher: path não é arquivo: %s (tipo: %s)", p, attachment_type.value)
        return ""
    
    file_size = p.stat().st_size
    if file_size == 0:
        logger.warning("Dispatcher: arquivo vazio: %s (tipo: %s)", p, attachment_type.value)
        return ""
    
    logger.info("Dispatcher: extraindo %s (tipo: %s, size: %d bytes)", p, attachment_type.value, file_size)
    import os
    path_str = os.path.normpath(str(p.absolute()))
    
    if not os.path.exists(path_str):
        logger.error("Dispatcher: os.path.exists False imediatamente antes de extrair %s", path_str)
        return ""
    
    if not os.path.isfile(path_str):
        logger.error("Dispatcher: os.path.isfile False imediatamente antes de extrair %s", path_str)
        return ""
    
    try:
        with open(path_str, "rb") as test_file:
            test_file.read(1)
    except (OSError, PermissionError) as e:
        logger.error("Dispatcher: não consegue abrir arquivo %s: %s", path_str, e)
        return ""
    
    try:
        if attachment_type == AttachmentType.IMAGE:
            return extract_text_from_image(path_str)
        if attachment_type == AttachmentType.AUDIO:
            return extract_text_from_audio(path_str)
        if attachment_type == AttachmentType.VIDEO:
            return extract_text_from_video(path_str)
        return ""
    except FileNotFoundError as e:
        logger.error("Dispatcher: FileNotFoundError durante extração %s: %s (path usado: %s)", p, e, path_str)
        return ""
    except Exception as e:
        logger.error("Dispatcher: erro durante extração %s: %s", p, e, exc_info=True)
        return ""


async def extract_from_file(
    attachment_type: AttachmentType,
    file_path: str,
) -> dict:
    """
    Extrai texto do arquivo conforme o tipo de mídia.
    Executa em thread (OCR/Whisper/ffmpeg são bloqueantes).

    Retorna {"raw_text", "language", "confidence", "metadata"}.
    Em falha, raw_text vazio. Nunca levanta exceção.
    """
    try:
        raw = await run_sync(_extract_sync, attachment_type, file_path)
        return {
            "raw_text": raw or "",
            "language": "",
            "confidence": 0.0,
            "metadata": {},
        }
    except Exception as e:
        logger.warning("Extração falhou para %s (%s): %s", file_path, attachment_type.value, e)
        return {"raw_text": "", "language": "", "confidence": 0.0, "metadata": {"error": str(e)}}
