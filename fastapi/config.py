"""Configurações da aplicação. """

import os
from pathlib import Path

PASTA_DA_API = Path(__file__).resolve().parent


JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    "chave-do-projeto-trocar-em-producao",
)
JWT_ALGORITHM = "HS256"
MINUTOS_DE_VALIDADE_DO_TOKEN = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))



CAMINHO_DO_BANCO = PASTA_DA_API / "database.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{CAMINHO_DO_BANCO}")


ORIGENS_PERMITIDAS = [
    origem.strip()
    for origem in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if origem.strip()
]

METODOS_PERMITIDOS = ["GET", "POST", "OPTIONS"]
CABECALHOS_PERMITIDOS = ["Authorization", "Content-Type"]



LIMITE_DO_LOGIN = os.getenv("RATE_LIMIT_LOGIN", "10/minute")


CSP_DA_API = (
    "default-src 'none'; "
    "frame-ancestors 'none'; "
    "base-uri 'none'; "
    "form-action 'none'"
)

CSP_DA_DOCUMENTACAO = (
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


ROTAS_DA_DOCUMENTACAO = ("/docs", "/redoc")
