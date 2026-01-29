"""
Schemas Pydantic para manifestações e anexos.
Request/response da API v1.
Fluxo modernizado: início por mídia, draft, submit, PATCH.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# --- Create (multipart) ---


class CreateManifestationResponse(BaseModel):
    """Resposta do POST /v1/manifestations.
    Draft: protocol=null, status=draft. Retorna id para PATCH/submit/attachments.
    """

    id: str = Field(..., description="ID da manifestação (UUID)")
    protocol: str | None = Field(None, description="Protocolo (null se draft)")
    status: str = Field(..., description="draft | received")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"id": "550e8400-e29b-41d4-a716-446655440000", "protocol": None, "status": "draft"},
                {"id": "550e8400-e29b-41d4-a716-446655440001", "protocol": "DF-2026-000001", "status": "received"},
            ]
        }
    }


# --- PATCH ---


class UpdateManifestationBody(BaseModel):
    """Corpo do PATCH /v1/manifestations/{id}. Todos opcionais."""

    original_text: str | None = None
    subject_id: str | None = None
    subject_label: str | None = None
    complementary_tags: list[str] | None = None
    summary: str | None = None
    location_lat: float | None = None
    location_lng: float | None = None
    location_description: str | None = None
    administrative_region: str | None = None
    anonymous: bool | None = None
    contact_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None


class UpdateManifestationResponse(BaseModel):
    """Resposta do PATCH /v1/manifestations/{id}."""

    id: str
    protocol: str | None
    status: str


# --- Submit ---


class SubmitManifestationResponse(BaseModel):
    """Resposta do POST /v1/manifestations/{id}/submit."""

    protocol: str = Field(..., description="Protocolo definitivo")
    status: str = Field(..., description="received")

    model_config = {"json_schema_extra": {"examples": [{"protocol": "DF-2026-000001", "status": "received"}]}}


# --- Get by protocol ---


class ManifestationDetailResponse(BaseModel):
    """Resposta do GET /v1/manifestations/{protocol}."""

    protocol: str
    status: str
    input_type: str
    created_at: datetime
    attachments_count: int
    subject_label: str | None = None
    summary: str | None = None
    extracted_text: str | None = Field(None, description="Texto extraído de imagens/áudios/vídeos (OCR, Whisper)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "protocol": "DF-2026-000001",
                    "status": "received",
                    "input_type": "mixed",
                    "created_at": "2026-01-24T12:00:00Z",
                    "attachments_count": 2,
                    "subject_label": "Sinalização de trânsito",
                    "summary": None,
                    "extracted_text": "Texto extraído do áudio...",
                }
            ]
        }
    }


# --- Attachments list ---


class AttachmentListItem(BaseModel):
    """Item da lista de anexos."""

    id: UUID
    type: str
    mime_type: str
    size_bytes: int
    created_at: datetime

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "type": "image",
                    "mime_type": "image/jpeg",
                    "size_bytes": 102400,
                    "created_at": "2026-01-24T12:00:00Z",
                }
            ]
        }
    }


class AttachmentsListResponse(BaseModel):
    """Resposta do GET /v1/manifestations/{protocol}/attachments."""

    protocol: str
    attachments: list[AttachmentListItem]


# --- Admin list ---


class ManifestationListItem(BaseModel):
    """Item da listagem admin."""

    id: UUID
    protocol: str | None
    input_type: str
    anonymous: bool
    status: str
    created_at: datetime
    attachments_count: int


class ManifestationsListResponse(BaseModel):
    """Resposta do GET /v1/admin/manifestations."""

    total: int
    page: int
    per_page: int
    items: list[ManifestationListItem]
