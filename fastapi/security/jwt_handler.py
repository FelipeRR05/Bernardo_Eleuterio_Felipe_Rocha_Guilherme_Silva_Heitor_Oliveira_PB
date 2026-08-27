"""Geração e validação de tokens JWT usando PyJWT, com assinatura HS256 e tempo de expiração."""

import os
from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import InvalidTokenError

"""Em produção, a SECRET_KEY deve vir de um gerenciador de segredos e nunca ser armazenada no código. Nesta etapa didática, é usado um valor padrão."""
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "chave-secreta-projeto-bloco-etapa1-trocar-em-producao")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(username: str) -> str:
    """Gera um token JWT assinado para o usuário informado."""

    expiracao = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": username,
        "exp": expiracao,
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str:
    """Valida o token JWT e retorna o usuário. Se estiver inválido, alterado ou expirado, gera um erro."""

    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username = payload.get("sub")

    if username is None:
        raise InvalidTokenError("Token não contém o campo 'sub'.")

    return username
