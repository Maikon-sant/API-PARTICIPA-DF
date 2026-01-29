"""
Enums do domínio.
Input_type (início por mídia), tipo de anexo e status.
"""

from enum import Enum


class InputType(str, Enum):
    """Tipo de entrada: texto, áudio, imagem, vídeo ou misto."""

    TEXT = "text"
    AUDIO = "audio"
    IMAGE = "image"
    VIDEO = "video"
    MIXED = "mixed"


# Compatibilidade: Channel = InputType
Channel = InputType


class AttachmentType(str, Enum):
    """Tipo do anexo (áudio, imagem ou vídeo)."""

    AUDIO = "audio"
    IMAGE = "image"
    VIDEO = "video"


class ManifestationStatus(str, Enum):
    """Status do fluxo da manifestação."""

    DRAFT = "draft"
    RECEIVED = "received"
    PROCESSING = "processing"
    COMPLETED = "completed"
