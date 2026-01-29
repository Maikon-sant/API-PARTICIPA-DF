"""
Transcrição de áudio. Extração local com openai-whisper e torch.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_whisper_model = None


def _get_model():
    """Lazy load do modelo Whisper (base)."""
    global _whisper_model
    if _whisper_model is None:
        import whisper
        _whisper_model = whisper.load_model("base")
    return _whisper_model


def extract_text_from_audio(path: str) -> str:
    """
    Extrai texto do áudio via transcrição (Whisper).

    Args:
        path: Caminho absoluto do arquivo de áudio.

    Returns:
        Texto transcrito ou string vazia em caso de falha. Nunca levanta exceção.
    """
    p = Path(path)
    if not p.is_absolute():
        p = p.resolve()
    
    if not p.exists():
        logger.error("Transcrição: arquivo não encontrado (path recebido: %s, resolved: %s, exists: %s)", path, p, p.exists())
        return ""
    
    if not p.is_file():
        logger.error("Transcrição: path não é arquivo %s (is_file: %s, is_dir: %s)", p, p.is_file(), p.is_dir())
        return ""

    try:
        file_size = p.stat().st_size
        if file_size == 0:
            logger.warning("Transcrição: arquivo vazio %s", p)
            return ""
        
        import os
        path_str = os.path.normpath(str(p.absolute()))
        logger.info("Transcrição: processando %s (size: %d bytes, path_str: %s)", p, file_size, path_str)
        
        if not os.path.exists(path_str):
            logger.error("Transcrição: os.path.exists retorna False para %s", path_str)
            return ""
        
        if not os.path.isfile(path_str):
            logger.error("Transcrição: os.path.isfile retorna False para %s", path_str)
            return ""
        
        try:
            with open(path_str, "rb") as test_file:
                test_file.read(1)
        except (OSError, PermissionError) as e:
            logger.error("Transcrição: não consegue abrir arquivo %s: %s", path_str, e)
            return ""
        
        actual_size = os.path.getsize(path_str)
        if actual_size != file_size:
            logger.warning("Transcrição: tamanho mudou (antes: %d, agora: %d) para %s", file_size, actual_size, path_str)
        
        if actual_size == 0:
            logger.error("Transcrição: arquivo tem tamanho 0 via os.path.getsize para %s", path_str)
            return ""
        
        model = _get_model()
        logger.info("Transcrição: chamando Whisper.transcribe com path: %s (size: %d bytes)", path_str, actual_size)
        
        try:
            out = model.transcribe(path_str, language=None, fp16=False)
        except FileNotFoundError as fnf:
            logger.error("Transcrição: FileNotFoundError no Whisper.transcribe - arquivo desapareceu? %s: %s", path_str, fnf)
            logger.error("Transcrição: diagnóstico - exists: %s, isfile: %s, readable: %s, path_len: %d", 
                        os.path.exists(path_str), os.path.isfile(path_str), os.access(path_str, os.R_OK), len(path_str))
            import stat
            try:
                file_stat = os.stat(path_str)
                logger.error("Transcrição: stat - mode: %s, size: %d", stat.filemode(file_stat.st_mode), file_stat.st_size)
            except Exception as stat_e:
                logger.error("Transcrição: erro ao fazer stat: %s", stat_e)
            
            try:
                with open(path_str, "rb") as test:
                    test.read(1)
                logger.error("Transcrição: arquivo pode ser aberto diretamente, mas Whisper falha")
            except Exception as open_e:
                logger.error("Transcrição: também não consegue abrir diretamente: %s", open_e)
            return ""
        text = (out.get("text") or "").strip()
        logger.info("Transcrição: concluída %s (texto: %d chars)", p, len(text))
        return text
    except FileNotFoundError as e:
        logger.error("Transcrição: FileNotFoundError durante processamento %s: %s (path_str usado: %s)", p, e, path_str if 'path_str' in locals() else path)
        return ""
    except OSError as e:
        logger.error("Transcrição: OSError durante processamento %s: %s (errno: %s)", p, e, getattr(e, 'errno', None))
        return ""
    except Exception as e:
        logger.error("Transcrição Whisper falhou para %s: %s", path, e, exc_info=True)
        return ""
