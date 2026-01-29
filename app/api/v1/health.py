"""
Healthcheck da API.
"""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Healthcheck",
    description="Verifica se a API está respondendo. Útil para load balancers e monitoramento.",
)
async def health() -> dict:
    return {"status": "ok"}
