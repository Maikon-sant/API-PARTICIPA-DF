"""
Configuração central da aplicação.
Carrega variáveis de ambiente e define constantes para a API Ouvidoria Participa DF.
"""

from functools import lru_cache
from pathlib import Path
import os
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_FFMPEG_PATH = (
    os.getenv("FFMPEG_PATH")
    or r"C:\ffmpeg\bin\ffmpeg.exe"
    or r"C:\ffmpeg\bin\ffmpeg.exe"
)

FFMPEG_PATH = DEFAULT_FFMPEG_PATH


class Settings(BaseSettings):
    """Configurações da API carregadas via variáveis de ambiente."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    app_name: str = "API Ouvidoria Participa DF"
    app_version: str = "1.0.0"
    debug: bool = False

    # API
    api_v1_prefix: str = "/v1"

    # Database (MySQL)
    database_url: str = "mysql+aiomysql://root:""@localhost:3306/participa_df?charset=utf8mb4"
    database_url_sync: str = "mysql+pymysql://root:""@localhost:3306/participa_df?charset=utf8mb4"

    # Storage local
    uploads_dir: Path = Path("uploads")
    max_file_size_bytes: int = 50 * 1024 * 1024  # 50 MB por arquivo
    allowed_audio_mimes: List[str] = [
        "audio/mpeg",
        "audio/mp3",
        "audio/wav",
        "audio/x-wav",
        "audio/webm",
        "audio/ogg",
    ]
    allowed_image_mimes: List[str] = [
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/gif",
        "image/webp",
    ]
    allowed_video_mimes: List[str] = [
        "video/mp4",
        "video/webm",
        "video/ogg",
    ]

    # Protocolo
    protocol_prefix: str = "DF"
    protocol_year: int = 2026


@lru_cache
def get_settings() -> Settings:
    """Retorna instância cacheada das configurações."""
    return Settings()
