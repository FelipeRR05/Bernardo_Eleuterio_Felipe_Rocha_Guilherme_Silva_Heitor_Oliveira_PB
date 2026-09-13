"""Rate limiting com slowapi."""

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from config import RATE_LIMIT_PADRAO


def _identificar_cliente(request: Request) -> str:
    """Define a chave (IP de origem) usada para contabilizar as requisições."""

    import os

    if os.getenv("TRUST_PROXY_HEADERS", "false").lower() == "true":
        encaminhado = request.headers.get("X-Forwarded-For")
        if encaminhado:
            # Primeiro IP da lista
            return encaminhado.split(",")[0].strip()

    return get_remote_address(request)


limiter = Limiter(key_func=_identificar_cliente, default_limits=[RATE_LIMIT_PADRAO])


async def tratar_limite_excedido(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Resposta HTTP 429 padronizada quando o limite é ultrapassado."""

    return JSONResponse(
        status_code=429,
        content={
            "detail": (
                "Muitas requisições em um curto intervalo de tempo. "
                "Aguarde alguns instantes e tente novamente."
            )
        },
        headers={"Retry-After": "60"},
    )
