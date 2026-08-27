from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from models.auth import TokenResponse
from security.jwt_handler import create_access_token
from security.users import authenticate_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=TokenResponse, summary="Autentica o usuário e retorna um token JWT")
def login(form_data: OAuth2PasswordRequestForm = Depends()) -> TokenResponse:
    """Autentica o usuário admin e retorna um token JWT de acesso."""

    if not authenticate_user(form_data.username, form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha inválidos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(form_data.username)

    return TokenResponse(access_token=access_token, token_type="bearer")
