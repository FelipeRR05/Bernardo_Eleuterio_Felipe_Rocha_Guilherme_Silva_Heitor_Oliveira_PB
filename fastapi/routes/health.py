"""Rota de health check."""

from fastapi import APIRouter

from models.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Verifica se a API está no ar",
    responses={200: {"description": "A API está ativa e respondendo."}},
)
def health_check() -> HealthResponse:
    """Rota pública, sem autenticação."""

    return HealthResponse(status="ok", service="customer-support-intent-api")
