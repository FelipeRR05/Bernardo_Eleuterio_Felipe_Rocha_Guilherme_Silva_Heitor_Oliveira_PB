"""Ponto de entrada da API.

Para rodar, de dentro da pasta fastapi/:

    uvicorn main:app --reload

A documentação interativa fica em http://127.0.0.1:8000/docs

Antes do primeiro uso é preciso criar o banco:

    python sqlite_database.py
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from config import (
    CABECALHOS_PERMITIDOS,
    METODOS_PERMITIDOS,
    ORIGENS_PERMITIDAS,
)
from routes import auth, health, predict, predictions
from security.middleware import CabecalhosDeSeguranca
from security.rate_limit import limiter, resposta_de_limite_excedido

app = FastAPI(
    title="Customer Support Intent API",
    description=(
        "API do sistema de atendimento ao cliente do Projeto de Bloco. "
        "Etapa 2: controles do OWASP Top 10 aplicados e auditados com OWASP ZAP."
    ),
    version="2.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, resposta_de_limite_excedido)
app.add_middleware(SlowAPIMiddleware)


app.add_middleware(CabecalhosDeSeguranca)


app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGENS_PERMITIDAS,
    allow_credentials=True,
    allow_methods=METODOS_PERMITIDOS,
    allow_headers=CABECALHOS_PERMITIDOS,
)

@app.exception_handler(RequestValidationError)
async def erro_de_validacao(
    request: Request, exc: RequestValidationError
) -> JSONResponse:

    erros = [
        {
            "campo": ".".join(str(parte) for parte in erro.get("loc", [])),
            "mensagem": erro.get("msg", ""),
            "tipo": erro.get("type", ""),
        }
        for erro in exc.errors()
    ]

    return JSONResponse(status_code=422, content={"detail": erros})


@app.exception_handler(Exception)
async def erro_inesperado(request: Request, exc: Exception) -> JSONResponse:

    return JSONResponse(
        status_code=500, content={"detail": "Erro interno do servidor"}
    )


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(predict.router)
app.include_router(predictions.router)
