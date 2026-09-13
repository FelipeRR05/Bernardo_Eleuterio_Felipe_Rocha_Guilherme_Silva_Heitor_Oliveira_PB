"""Geração e validação de tokens JWT (PyJWT, assinatura HS256)."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from jwt.exceptions import InvalidTokenError

from config import ACCESS_TOKEN_EXPIRE_MINUTES, JWT_ALGORITHM, JWT_SECRET_KEY


def criar_token_de_acesso(user_id: int, username: str, role: str) -> str:
    """Gera um token JWT assinado para o usuário informado."""

    momento_atual = datetime.now(timezone.utc)
    expiracao = momento_atual + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "iat": momento_atual,
        "exp": expiracao,
        "jti": str(uuid.uuid4()),
    }

    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decodificar_token_de_acesso(token: str) -> dict[str, Any]:
    """Valida a assinatura e a expiração do token e devolve o payload.

    Levanta ``InvalidTokenError`` se o token for inválido, adulterado ou
    expirado.
    """

    payload = jwt.decode(
        token,
        JWT_SECRET_KEY,
        algorithms=[JWT_ALGORITHM],  # lista fixa: nunca confiar no header do token
        options={"require": ["exp", "sub"]},
    )

    if not payload.get("sub"):
        raise InvalidTokenError("Token não contém o campo 'sub'.")

    return payload
