"""
Utilitários para processamento de mídia.
Execução em thread para não bloquear o event loop (OCR, Whisper, ffmpeg).
"""

import asyncio
import logging
import tempfile
from pathlib import Path
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def run_sync(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """
    Executa função síncrona (bloqueante) em thread separada.
    OCR, Whisper e ffmpeg são CPU-bound; não bloquear o event loop.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: func(*args, **kwargs))


def ensure_dir(path: Path) -> Path:
    """Cria diretório se não existir. Retorna o path."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def temp_dir(prefix: str = "media_") -> Path:
    """Cria diretório temporário. Chamador deve remover após uso."""
    return Path(tempfile.mkdtemp(prefix=prefix))


def resolve_path(path: str | Path) -> Path:
    """Garante path absoluto e resolvido (links, . etc.)."""
    p = Path(path) if isinstance(path, str) else path
    return p.resolve()


def safe_unlink(path: Path) -> None:
    """Remove arquivo se existir. Ignora erros."""
    try:
        if path.exists():
            path.unlink()
    except OSError as e:
        logger.warning("Erro ao remover %s: %s", path, e)
