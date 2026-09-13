"""Configurações centrais da aplicação.

Todos os parâmetros sensíveis ou dependentes de ambiente são lidos de variáveis
de ambiente, com valores padrão seguros para desenvolvimento local.
"""

import os
import secrets


def _ler_lista_de_ambiente(nome_variavel: str, padrao: list[str]) -> list[str]:
    """Lê uma variável de ambiente no formato 'a,b,c' e devolve uma lista."""

    valor_bruto = os.getenv(nome_variavel)
    if not valor_bruto:
        return padrao
    return [item.strip() for item in valor_bruto.split(",") if item.strip()]


AMBIENTE = os.getenv("APP_ENV", "development")
EM_PRODUCAO = AMBIENTE == "production"

_CHAVE_PADRAO_DESENVOLVIMENTO = "chave-secreta-projeto-bloco-DEV-nao-usar-em-producao"

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") or (
    secrets.token_urlsafe(64) if EM_PRODUCAO else _CHAVE_PADRAO_DESENVOLVIMENTO
)

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./customer_support.db")

CORS_ORIGENS_PERMITIDAS = _ler_lista_de_ambiente(
    "CORS_ALLOWED_ORIGINS",
    [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
)

CORS_METODOS_PERMITIDOS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
CORS_CABECALHOS_PERMITIDOS = ["Authorization", "Content-Type"]

RATE_LIMIT_LOGIN = os.getenv("RATE_LIMIT_LOGIN", "5/minute")
RATE_LIMIT_PADRAO = os.getenv("RATE_LIMIT_DEFAULT", "100/minute")

CSP_API = (
    "default-src 'none'; "
    "frame-ancestors 'none'; "
    "base-uri 'none'; "
    "form-action 'none'"
)

CSP_DOCUMENTACAO = (
    "default-src 'none'; "
    "script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
    "style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
    "img-src 'self' https://fastapi.tiangolo.com data:; "
    "font-src 'self' https://cdn.jsdelivr.net; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self'"
)

ROTAS_DE_DOCUMENTACAO = ("/docs", "/redoc", "/openapi.json")
