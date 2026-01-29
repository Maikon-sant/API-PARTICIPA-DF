"""
Processamento de vídeo: extração de áudio e frames via ffmpeg,
transcrição (Whisper) e OCR nos frames. Tudo local.
"""

import logging
import os
from pathlib import Path

from app.core.config import FFMPEG_PATH
from app.media.audio_transcription import extract_text_from_audio
from app.media.image_ocr import extract_text_from_image
from app.media.utils import temp_dir, safe_unlink

logger = logging.getLogger(__name__)

# Configura o caminho do ffmpeg adicionando o diretório ao PATH
if FFMPEG_PATH:
    ffmpeg_dir = os.path.dirname(FFMPEG_PATH)
    if ffmpeg_dir and os.path.exists(ffmpeg_dir):
        current_path = os.environ.get("PATH", "")
        if ffmpeg_dir not in current_path:
            os.environ["PATH"] = ffmpeg_dir + os.pathsep + current_path


def _extract_audio_ffmpeg(video_path: str, out_wav: Path) -> bool:
    """Extrai áudio do vídeo para WAV. Retorna True se OK."""
    import os
    video_p = Path(video_path).resolve()
    if not video_p.exists():
        logger.error("ffmpeg extrair áudio: vídeo não encontrado %s (original: %s)", video_p, video_path)
        return False
    
    if not video_p.is_file():
        logger.error("ffmpeg extrair áudio: path não é arquivo %s", video_p)
        return False
    
    video_str = os.path.normpath(str(video_p.absolute()))
    if not os.path.exists(video_str):
        logger.error("ffmpeg extrair áudio: os.path.exists False para %s", video_str)
        return False
    
    try:
        with open(video_str, "rb") as test_file:
            test_file.read(1)
    except (OSError, PermissionError) as e:
        logger.error("ffmpeg extrair áudio: não consegue abrir vídeo %s: %s", video_str, e)
        return False
    
    try:
        import ffmpeg
        logger.info("ffmpeg: extraindo áudio de %s para %s", video_str, out_wav)
        (ffmpeg
         .input(video_str)
         .output(str(out_wav), acodec="pcm_s16le", ac=1, ar=16000)
         .overwrite_output()
         .run(capture_stderr=True, quiet=True))
        return True
    except FileNotFoundError as e:
        logger.error("ffmpeg extrair áudio: FileNotFoundError - vídeo desapareceu? %s: %s (path: %s, exists: %s, readable: %s)", 
                    video_str, e, video_str, os.path.exists(video_str), os.access(video_str, os.R_OK))
        return False
    except Exception as e:
        logger.warning("ffmpeg extrair áudio: %s (vídeo: %s)", e, video_str)
        return False


def _extract_frames_ffmpeg(video_path: str, out_dir: Path, max_frames: int = 10) -> list[Path]:
    """Extrai até max_frames imagens (1 a cada ~5s). Retorna lista de paths."""
    import os
    video_p = Path(video_path).resolve()
    if not video_p.exists():
        logger.error("ffmpeg extrair frames: vídeo não encontrado %s (original: %s)", video_p, video_path)
        return []
    
    if not video_p.is_file():
        logger.error("ffmpeg extrair frames: path não é arquivo %s", video_p)
        return []
    
    video_str = os.path.normpath(str(video_p.absolute()))
    if not os.path.exists(video_str):
        logger.error("ffmpeg extrair frames: os.path.exists False para %s", video_str)
        return []
    
    try:
        with open(video_str, "rb") as test_file:
            test_file.read(1)
    except (OSError, PermissionError) as e:
        logger.error("ffmpeg extrair frames: não consegue abrir vídeo %s: %s", video_str, e)
        return []
    
    try:
        import ffmpeg
        out_dir.mkdir(parents=True, exist_ok=True)
        pattern = str(out_dir / "frame_%04d.png")
        logger.info("ffmpeg: extraindo frames de %s para %s", video_str, pattern)
        (ffmpeg
         .input(video_str)
         .filter("fps", fps=0.2)
         .output(pattern, vframes=max_frames)
         .overwrite_output()
         .run(capture_stderr=True, quiet=True))
        frames = sorted(out_dir.glob("frame_*.png"))
        logger.info("ffmpeg: extraídos %d frames de %s", len(frames), video_str)
        return frames[:max_frames]
    except FileNotFoundError as e:
        logger.error("ffmpeg extrair frames: FileNotFoundError - vídeo desapareceu? %s: %s (path: %s, exists: %s, readable: %s)", 
                    video_str, e, video_str, os.path.exists(video_str), os.access(video_str, os.R_OK))
        return []
    except Exception as e:
        logger.warning("ffmpeg extrair frames: %s (vídeo: %s)", e, video_str)
        return []


def extract_text_from_video(path: str) -> str:
    """
    Extrai texto do vídeo: áudio (Whisper) + frames (OCR).
    Usa ffmpeg para extrair áudio e frames, depois processa localmente.

    Args:
        path: Caminho absoluto do arquivo de vídeo.

    Returns:
        Texto extraído (áudio + frames) ou string vazia em caso de falha. Nunca levanta exceção.
    """
    p = Path(path).resolve()
    if not p.exists():
        logger.warning("Vídeo: arquivo não encontrado %s", path)
        return ""

    tmp = temp_dir("video_")
    wav_path = tmp / "audio.wav"
    frames_dir = tmp / "frames"
    parts: list[str] = []

    try:
        if _extract_audio_ffmpeg(str(p), wav_path):
            if not wav_path.exists():
                logger.warning("Vídeo: áudio extraído não encontrado %s", wav_path)
            else:
                logger.info("Vídeo: áudio extraído %s (size: %d bytes)", wav_path, wav_path.stat().st_size)
                t = extract_text_from_audio(str(wav_path))
                if t:
                    parts.append("[Áudio]\n" + t)

        for fp in _extract_frames_ffmpeg(str(p), frames_dir, max_frames=10):
            try:
                t = extract_text_from_image(str(fp))
                if t:
                    parts.append("[Frame]\n" + t)
            except Exception as e:
                logger.warning("OCR frame %s: %s", fp, e)

        return "\n\n---\n\n".join(parts) if parts else ""
    except Exception as e:
        logger.warning("Processamento de vídeo falhou %s: %s", path, e)
        return ""
    finally:
        safe_unlink(wav_path)
        if frames_dir.exists():
            for f in frames_dir.glob("*.png"):
                safe_unlink(f)
        try:
            if frames_dir.exists():
                frames_dir.rmdir()
        except OSError:
            pass
        try:
            tmp.rmdir()
        except OSError:
            pass
