"""Modelo de resposta da rota de autenticação."""

from pydantic import BaseModel


class TokenResponse(BaseModel):
    """O que POST /auth/token devolve quando o login dá certo."""

    access_token: str
    token_type: str = "bearer"
