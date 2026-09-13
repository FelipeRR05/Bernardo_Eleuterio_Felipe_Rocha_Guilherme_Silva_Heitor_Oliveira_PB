"""Esquema OAuth2 (Bearer) e dependências de autenticação/autorização."""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlmodel import Session, select

from database import obter_sessao
from models.user import User
from security.jwt_handler import decodificar_token_de_acesso

# Tratamento de autenticação via OAuth2 com Bearer token.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token", auto_error=False)


CREDENCIAIS_INVALIDAS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Token ausente, inválido ou expirado",
    headers={"WWW-Authenticate": "Bearer"},
)


def obter_usuario_atual(
    token: str | None = Depends(oauth2_scheme),
    sessao: Session = Depends(obter_sessao),
) -> User:
    """Valida o JWT e devolve o usuário autenticado."""

    if not token:
        raise CREDENCIAIS_INVALIDAS

    try:
        payload = decodificar_token_de_acesso(token)
        user_id = int(payload["sub"])
    except (InvalidTokenError, ValueError, KeyError):
        raise CREDENCIAIS_INVALIDAS

    # Consulta do usuário logado
    usuario = sessao.exec(select(User).where(User.id == user_id)).first()

    if usuario is None or not usuario.ativo:
        raise CREDENCIAIS_INVALIDAS

    return usuario


def exigir_papel_de_admin(usuario: User = Depends(obter_usuario_atual)) -> User:
    """Dependência para rotas restritas a administradores."""

    if usuario.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta operação exige privilégios de administrador",
        )
    return usuario
