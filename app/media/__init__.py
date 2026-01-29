"""
Módulo de processamento multimodal local.
OCR (imagem), transcrição (áudio), vídeo (áudio + frames + OCR).
"""

from app.media.dispatcher import extract_from_file
from app.media.image_ocr import extract_text_from_image
from app.media.audio_transcription import extract_text_from_audio
from app.media.video_processing import extract_text_from_video

__all__ = [
    "extract_from_file",
    "extract_text_from_image",
    "extract_text_from_audio",
    "extract_text_from_video",
]
