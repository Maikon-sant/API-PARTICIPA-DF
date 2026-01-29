"""
Rotas públicas de manifestações.
Fluxo modernizado: POST (draft), PATCH, POST attachments, POST submit, GET por protocolo.
"""

import json
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.application.use_cases.add_attachments import (
    AddAttachmentsError,
    AddAttachmentsInput,
    ValidationError as AddValidationError,
    add_attachments,
)
from app.application.use_cases.create_manifestation import (
    CreateManifestationInput,
    ValidationError as CreateValidationError,
    create_manifestation,
)
from app.application.use_cases.get_manifestation import get_manifestation_by_protocol
from app.application.use_cases.submit_manifestation import (
    SubmitError,
    submit_manifestation,
)
from app.application.use_cases.update_manifestation import (
    UpdateError,
    UpdateManifestationInput,
    update_manifestation,
)
from app.infrastructure.db.models import AttachmentModel, ManifestationModel
from app.infrastructure.db.session import get_db
from app.infrastructure.storage.local_storage import LocalStorage
from app.schemas.manifestation import (
    AttachmentsListResponse,
    AttachmentListItem,
    CreateManifestationResponse,
    ManifestationDetailResponse,
    SubmitManifestationResponse,
    UpdateManifestationBody,
    UpdateManifestationResponse,
)


router = APIRouter(prefix="/manifestations", tags=["manifestations"])


def _storage() -> LocalStorage:
    return LocalStorage()


def _opt_str(s: str | None) -> str | None:
    """Retorna None para None, '' ou só espaços. Evita 500 por campo vazio."""
    if s is None:
        return None
    t = s.strip() if isinstance(s, str) else ""
    return t if t else None


def _parse_tags(s: str | None) -> list[str] | None:
    """Parse complementary_tags JSON string."""
    s = _opt_str(s)
    if not s:
        return None
    try:
        v = json.loads(s)
        return v if isinstance(v, list) else [str(v)]
    except json.JSONDecodeError:
        return None


def _opt_float(x: float | None) -> float | None:
    """Retorna None para None. Evita 500 por campo vazio no multipart."""
    if x is None:
        return None
    if isinstance(x, float) and (x != x):  # NaN
        return None
    return x


# --- POST create (draft) ---


@router.post(
    "",
    response_model=CreateManifestationResponse,
    status_code=201,
    summary="Criar manifestação (draft)",
    description="Aceita text ou original_text; um arquivo opcional (imagem, áudio ou vídeo); ou ambos. Pelo menos um obrigatório. 400 se faltar ambos. Swagger: Choose File.",
)
async def create(
    db: AsyncSession = Depends(get_db),
    text: str | None = Form(default=None),
    original_text: str | None = Form(default=None),
    anonymous: bool = Form(default=False),
    file: UploadFile = File(default=None, description="Imagem, áudio ou vídeo"),
    subject_id: str | None = Form(default=None),
    subject_label: str | None = Form(default=None),
    summary: str | None = Form(default=None),
    administrative_region: str | None = Form(default=None),
    complementary_tags: str | None = Form(default=None),
    location_lat: float | None = Form(default=None),
    location_lng: float | None = Form(default=None),
    location_description: str | None = Form(default=None),
    contact_name: str | None = Form(default=None),
    contact_email: str | None = Form(default=None),
    contact_phone: str | None = Form(default=None),
) -> CreateManifestationResponse:
    if text is None and original_text is not None:
        text = original_text

    validated_files: list[tuple[bytes, str, str]] = []
    if file is not None:
        fn = getattr(file, "filename", None)
        stripped_fn = (fn.strip() if isinstance(fn, str) else "") or ""
        if stripped_fn:
            try:
                content = await file.read()
                mime = getattr(file, "content_type", None) or "application/octet-stream"
                validated_files.append((content, mime, stripped_fn))
            except Exception:
                pass

    text_normalized = _opt_str(text)
    tags = _parse_tags(complementary_tags)

    try:
        out = await create_manifestation(
            db,
            _storage(),
            CreateManifestationInput(
                original_text=text_normalized,
                files=validated_files,
                subject_id=_opt_str(subject_id),
                subject_label=_opt_str(subject_label),
                complementary_tags=tags,
                summary=_opt_str(summary),
                location_lat=_opt_float(location_lat),
                location_lng=_opt_float(location_lng),
                location_description=_opt_str(location_description),
                administrative_region=_opt_str(administrative_region),
                anonymous=anonymous,
                contact_name=_opt_str(contact_name),
                contact_email=_opt_str(contact_email),
                contact_phone=_opt_str(contact_phone),
            ),
        )
    except CreateValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return CreateManifestationResponse(id=out.id, protocol=out.protocol, status=out.status)


# --- PATCH update ---


@router.patch(
    "/{manifestation_id}",
    response_model=UpdateManifestationResponse,
    summary="Atualizar manifestação (draft)",
    description="Atualiza qualquer etapa. Apenas rascunhos. Use id retornado no POST.",
)
async def update(
    manifestation_id: str,
    body: UpdateManifestationBody,
    db: AsyncSession = Depends(get_db),
) -> UpdateManifestationResponse:
    inp = UpdateManifestationInput(
        original_text=body.original_text,
        subject_id=body.subject_id,
        subject_label=body.subject_label,
        complementary_tags=body.complementary_tags,
        summary=body.summary,
        location_lat=body.location_lat,
        location_lng=body.location_lng,
        location_description=body.location_description,
        administrative_region=body.administrative_region,
        anonymous=body.anonymous,
        contact_name=body.contact_name,
        contact_email=body.contact_email,
        contact_phone=body.contact_phone,
    )
    try:
        out = await update_manifestation(db, manifestation_id, inp)
    except UpdateError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return UpdateManifestationResponse(id=out.id, protocol=out.protocol, status=out.status)


# --- POST attachments ---


@router.post(
    "/{manifestation_id}/attachments",
    summary="Adicionar anexos (draft)",
    description="Upload de arquivos para manifestação em rascunho.",
)
async def add_attachments_route(
    manifestation_id: str,
    db: AsyncSession = Depends(get_db),
    files: list[UploadFile] = File(..., description="Arquivos: áudio, imagem ou vídeo"),
) -> dict:
    validated: list[tuple[bytes, str, str]] = []
    for uf in files:
        if not uf.filename or uf.filename == "":
            continue
        content = await uf.read()
        mime = uf.content_type or "application/octet-stream"
        validated.append((content, mime, uf.filename))
    if not validated:
        raise HTTPException(status_code=400, detail="Nenhum arquivo válido enviado.")
    inp = AddAttachmentsInput(files=validated)
    try:
        out = await add_attachments(db, _storage(), manifestation_id, inp)
    except AddAttachmentsError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except AddValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"manifestation_id": out.manifestation_id, "added_count": out.added_count}


# --- POST submit ---


@router.post(
    "/{manifestation_id}/submit",
    response_model=SubmitManifestationResponse,
    summary="Finalizar manifestação",
    description="Gera protocolo definitivo. Status → received. Acompanhamento apenas por protocolo.",
)
async def submit(
    manifestation_id: str,
    db: AsyncSession = Depends(get_db),
) -> SubmitManifestationResponse:
    try:
        out = await submit_manifestation(db, manifestation_id)
    except SubmitError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return SubmitManifestationResponse(protocol=out.protocol, status=out.status)


# --- GET (mais específicas primeiro) ---


@router.get(
    "/{protocol}/attachments/{attachment_id}",
    summary="Download do anexo",
    description="Download do arquivo. Nunca expõe caminhos internos.",
)
async def download_attachment(
    protocol: str,
    attachment_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Response:
    q = (
        select(AttachmentModel)
        .join(ManifestationModel, AttachmentModel.manifestation_id == ManifestationModel.id)
        .where(
            AttachmentModel.id == str(attachment_id),
            ManifestationModel.protocol == protocol,
        )
    )
    r = await db.execute(q)
    a = r.scalar_one_or_none()
    if not a:
        raise HTTPException(status_code=404, detail="Anexo não encontrado.")
    storage = LocalStorage()
    if not storage.exists(a.file_path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado no storage.")
    body = storage.read_bytes(a.file_path)
    return Response(
        content=body,
        media_type=a.mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{attachment_id}.{a.file_path.split(".")[-1]}"',
        },
    )


@router.get(
    "/{protocol}/attachments",
    response_model=AttachmentsListResponse,
    summary="Listar anexos",
    description="Lista anexos da manifestação (por protocolo).",
)
async def list_attachments(
    protocol: str,
    db: AsyncSession = Depends(get_db),
) -> AttachmentsListResponse:
    q = (
        select(ManifestationModel)
        .where(ManifestationModel.protocol == protocol)
        .options(selectinload(ManifestationModel.attachments))
    )
    r = await db.execute(q)
    m = r.scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail="Manifestação não encontrada.")
    items = [
        AttachmentListItem(
            id=a.id,
            type=a.type.value,
            mime_type=a.mime_type,
            size_bytes=a.size_bytes,
            created_at=a.created_at,
        )
        for a in m.attachments
    ]
    return AttachmentsListResponse(protocol=protocol, attachments=items)


@router.get(
    "/{protocol}",
    response_model=ManifestationDetailResponse,
    summary="Consultar por protocolo",
    description="Retorna status e dados públicos. Apenas manifestações finalizadas.",
)
async def get_by_protocol(
    protocol: str,
    db: AsyncSession = Depends(get_db),
) -> ManifestationDetailResponse:
    data = await get_manifestation_by_protocol(db, protocol)
    if not data:
        raise HTTPException(status_code=404, detail="Manifestação não encontrada.")
    return ManifestationDetailResponse(**data)
