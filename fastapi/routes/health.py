from fastapi import APIRouter

from models.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="Verifica se a API está ativa")
def health_check() -> HealthResponse:
    """Rota pública de *health check*.

    Não exige autenticação: serve para verificar rapidamente se a API está
    no ar e respondendo."""

    return HealthResponse(status="ok", service="customer-support-intent-api")
