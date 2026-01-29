"""
API Ouvidoria Participa DF - Hackathon.
FastAPI com versionamento /v1, CORS, Swagger e Redoc.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import admin, health, manifestations
from app.core.config import get_settings
from app.infrastructure.db.session import init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Cria pasta uploads e tabelas ao subir (use Alembic em produção)."""
    Path(settings.uploads_dir).mkdir(parents=True, exist_ok=True)
    await init_db()
    yield
    # shutdown, se necessário


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API para registro de manifestações na Ouvidoria do Hackathon Participa DF. "
    "Início por texto, áudio, imagem ou vídeo. Sem conta nem login. "
    "Fluxo: draft → PATCH/attachments → submit → protocolo. Anonimato sempre disponível.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API v1
app.include_router(health.router, prefix=settings.api_v1_prefix)
app.include_router(manifestations.router, prefix=settings.api_v1_prefix)
app.include_router(admin.router, prefix=settings.api_v1_prefix)


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "redoc": "/redoc",
        "v1": f"{settings.api_v1_prefix}/health",
    }
