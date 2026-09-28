"""Esquema OAuth2PasswordBearer e a dependência que identifica quem está chamando. """

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlmodel import Session, select

from database import pegar_sessao
from models.user import User
from security.jwt_handler import ler_token


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token", auto_error=False)


TOKEN_INVALIDO = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Token ausente, inválido ou expirado",
    headers={"WWW-Authenticate": "Bearer"},
)


def usuario_autenticado(
    token: str | None = Depends(oauth2_scheme),
    sessao: Session = Depends(pegar_sessao),
) -> User:

    if not token:
        raise TOKEN_INVALIDO

    try:
        conteudo = ler_token(token)
        user_id = int(conteudo["sub"])
    except (InvalidTokenError, KeyError, ValueError):
        raise TOKEN_INVALIDO

    usuario = sessao.exec(select(User).where(User.id == user_id)).first()

    if usuario is None:
        raise TOKEN_INVALIDO

    return usuario
