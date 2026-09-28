"""Rota de autenticação, com rate limiting contra força bruta."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from config import LIMITE_DO_LOGIN
from database import pegar_sessao
from models.auth import TokenResponse
from models.user import User
from security.jwt_handler import criar_token
from security.password import gerar_hash_de_senha, senha_confere
from security.rate_limit import limiter

router = APIRouter(prefix="/auth", tags=["auth"])


# Hash descartável, gerado uma vez quando o módulo carrega. Ele existe só para
# a defesa contra enumeração de usuários explicada em autenticar().
_HASH_DE_COMPARACAO = gerar_hash_de_senha("hash-que-nunca-vai-bater-com-nada")


def autenticar(sessao: Session, username: str, senha: str) -> User | None:
    """Confere usuário e senha. Devolve o usuário, ou None se não bater."""

    usuario = sessao.exec(select(User).where(User.username == username)).first()

    if usuario is None:
        senha_confere(senha, _HASH_DE_COMPARACAO)
        return None

    if not senha_confere(senha, usuario.hashed_password):
        return None

    return usuario


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Autentica o usuário e devolve um token JWT",
    responses={
        200: {"description": "Login aceito. Devolve access_token e token_type."},
        401: {
            "description": (
                "Usuário ou senha inválidos. A resposta é a mesma para usuário "
                "inexistente e senha errada, para não revelar quais usuários existem."
            )
        },
        422: {"description": "Formulário incompleto (faltou username ou password)."},
        429: {
            "description": (
                "Limite de 10 requisições por minuto excedido. "
                "Veja o cabeçalho Retry-After."
            )
        },
    },
)
@limiter.limit(LIMITE_DO_LOGIN)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    sessao: Session = Depends(pegar_sessao),
) -> TokenResponse:
    """Recebe usuário e senha e devolve o token JWT."""

    usuario = autenticar(sessao, form_data.username, form_data.password)

    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha inválidos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(
        access_token=criar_token(user_id=usuario.id, username=usuario.username),
        token_type="bearer",
    )
