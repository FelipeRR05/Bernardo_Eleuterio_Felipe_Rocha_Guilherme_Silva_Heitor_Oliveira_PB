"""Rate limiting com SlowAPI. """

import os

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address


def identificar_cliente(request: Request) -> str:
   

    if os.getenv("TRUST_PROXY_HEADERS", "false").lower() == "true":
        encaminhado = request.headers.get("X-Forwarded-For")
        if encaminhado:
            return encaminhado.split(",")[0].strip()

    return get_remote_address(request)


limiter = Limiter(key_func=identificar_cliente)


async def resposta_de_limite_excedido(
    request: Request, exc: RateLimitExceeded
) -> JSONResponse:
  

    return JSONResponse(
        status_code=429,
        content={
            "detail": (
                "Muitas tentativas em pouco tempo. "
                "Espere um momento e tente novamente."
            )
        },
        headers={"Retry-After": "60"},
    )
