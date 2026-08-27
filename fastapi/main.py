"""Ponto de entrada da aplicação FastAPI.

Execução local:
    uvicorn main:app --reload

Documentação interativa (Swagger):
    http://127.0.0.1:8000/docs
"""
from fastapi import FastAPI

from routes import auth, health, predict

app = FastAPI(
    title="Customer Support Intent API",
    description=(
        "API base do sistema de atendimento ao cliente do Projeto de Bloco. "
        "Etapa 1: estrutura da API com autenticação JWT"
    ),
    version="0.1.0",
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(predict.router)
