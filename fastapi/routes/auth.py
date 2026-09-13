"""Rota de autenticação."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from config import RATE_LIMIT_LOGIN
from database import obter_sessao
from models.auth import TokenResponse
from security.jwt_handler import criar_token_de_acesso
from security.rate_limit import limiter
from security.users import autenticar_usuario

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Autentica o usuário e retorna um token JWT",
)
@limiter.limit(RATE_LIMIT_LOGIN)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    sessao: Session = Depends(obter_sessao),
) -> TokenResponse:
    """Autentica o usuário e devolve um token JWT de acesso."""
    usuario = autenticar_usuario(sessao, form_data.username, form_data.password)

    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha inválidos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = criar_token_de_acesso(
        user_id=usuario.id,
        username=usuario.username,
        role=usuario.role,
    )

    return TokenResponse(access_token=token, token_type="bearer")
