"""Modelo de resposta do health check."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """O que GET /health devolve."""

    status: str
    service: str
