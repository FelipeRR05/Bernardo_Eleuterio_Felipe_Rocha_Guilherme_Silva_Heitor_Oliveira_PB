from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Corpo de resposta da rota de health check."""

    status: str
    service: str
