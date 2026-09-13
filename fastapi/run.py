"""Inicializador da API com opções seguras para o uvicorn.

Uso:
    python run.py

Equivalente via linha de comando:
    uvicorn main:app --no-server-header --no-date-header
"""

import os

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("API_HOST", "127.0.0.1"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=os.getenv("API_RELOAD", "false").lower() == "true",
        server_header=False,
        date_header=False,
    )
