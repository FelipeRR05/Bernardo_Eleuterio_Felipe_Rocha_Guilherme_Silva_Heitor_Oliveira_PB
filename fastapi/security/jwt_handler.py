"""Criação e validação dos tokens JWT. """

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from jwt.exceptions import InvalidTokenError

from config import JWT_ALGORITHM, JWT_SECRET_KEY, MINUTOS_DE_VALIDADE_DO_TOKEN


def criar_token(user_id: int, username: str) -> str:

    agora = datetime.now(timezone.utc)

    conteudo: dict[str, Any] = {
        "sub": str(user_id),
        "username": username,
        "iat": agora,
        "exp": agora + timedelta(minutes=MINUTOS_DE_VALIDADE_DO_TOKEN),
    }

    return jwt.encode(conteudo, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def ler_token(token: str) -> dict[str, Any]:

    conteudo = jwt.decode(
        token,
        JWT_SECRET_KEY,
        algorithms=[JWT_ALGORITHM],
        options={"require": ["exp", "sub"]},
    )

    if not conteudo.get("sub"):
        raise InvalidTokenError("Token sem o campo 'sub'.")

    return conteudo
