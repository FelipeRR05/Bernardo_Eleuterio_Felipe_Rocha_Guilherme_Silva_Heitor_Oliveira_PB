"""Ponto de entrada da aplicação FastAPI.

Execução local:
    uvicorn main:app --reload

Documentação interativa (Swagger):
    http://127.0.0.1:8000/docs
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from config import (
    CORS_CABECALHOS_PERMITIDOS,
    CORS_METODOS_PERMITIDOS,
    CORS_ORIGENS_PERMITIDAS,
    EM_PRODUCAO,
)
from database import criar_tabelas, popular_dados_iniciais
from routes import auth, health, predict, tickets
from security.middleware import SecurityHeadersMiddleware
from security.rate_limit import limiter, tratar_limite_excedido


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    """Prepara o banco de dados na subida da aplicação."""
    criar_tabelas()
    popular_dados_iniciais()
    yield


app = FastAPI(
    title="Customer Support Intent API",
    description="API do sistema de atendimento ao cliente do Projeto de Bloco.",
    version="0.2.0",
    lifespan=ciclo_de_vida,
    docs_url=None if EM_PRODUCAO else "/docs",
    redoc_url=None if EM_PRODUCAO else "/redoc",
    openapi_url=None if EM_PRODUCAO else "/openapi.json",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, tratar_limite_excedido)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGENS_PERMITIDAS,
    allow_credentials=True,
    allow_methods=CORS_METODOS_PERMITIDOS,
    allow_headers=CORS_CABECALHOS_PERMITIDOS,
    max_age=600,
)


@app.exception_handler(RequestValidationError)
async def tratar_erro_de_validacao(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Normaliza os erros de validação do Pydantic para não vazar o input original."""
    erros_sanitizados = [
        {
            "campo": ".".join(str(parte) for parte in erro.get("loc", [])),
            "mensagem": erro.get("msg", ""),
            "tipo": erro.get("type", ""),
        }
        for erro in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": erros_sanitizados})


@app.exception_handler(Exception)
async def tratar_erro_inesperado(request: Request, exc: Exception) -> JSONResponse:
    """Evita que stack traces cheguem ao cliente em erros inesperados."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Erro interno do servidor"},
    )


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(predict.router)
app.include_router(tickets.router)
