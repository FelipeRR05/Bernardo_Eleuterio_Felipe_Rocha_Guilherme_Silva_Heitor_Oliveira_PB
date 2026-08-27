"""Esquema OAuth2 (Bearer Token) e dependência de validação de token JWT."""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError

from security.jwt_handler import decode_access_token

"""Indica no Swagger a rota usada para obter o token, sem criar essa rota automaticamente.."""
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """Protege as rotas exigindo um JWT válido. Se o token estiver ausente, inválido ou expirado, retorna erro 401."""

    credenciais_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        username = decode_access_token(token)
    except InvalidTokenError:
        raise credenciais_invalidas

    return username
