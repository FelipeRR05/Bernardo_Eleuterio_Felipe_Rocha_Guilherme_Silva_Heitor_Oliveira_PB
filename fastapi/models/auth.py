from pydantic import BaseModel


class TokenResponse(BaseModel):
    """Corpo de resposta da rota de autenticação (POST /auth/token)."""

    access_token: str
    token_type: str = "bearer"
