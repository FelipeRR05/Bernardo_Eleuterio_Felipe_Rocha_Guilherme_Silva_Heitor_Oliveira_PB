"""Middleware de cabeçalhos de segurança HTTP."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from config import CSP_API, CSP_DOCUMENTACAO, EM_PRODUCAO, ROTAS_DE_DOCUMENTACAO


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Acrescenta cabeçalhos de segurança a todas as respostas da API."""

    async def dispatch(self, request: Request, call_next) -> Response:
        resposta: Response = await call_next(request)

        caminho = request.url.path

        documentacao_habilitada = not EM_PRODUCAO
        if documentacao_habilitada and caminho.startswith(ROTAS_DE_DOCUMENTACAO):
            resposta.headers["Content-Security-Policy"] = CSP_DOCUMENTACAO
        else:
            resposta.headers["Content-Security-Policy"] = CSP_API

        resposta.headers["Strict-Transport-Security"] = (
            "max-age=63072000; includeSubDomains; preload"
        )

        resposta.headers["X-Frame-Options"] = "DENY"
        resposta.headers["X-Content-Type-Options"] = "nosniff"

        resposta.headers["Referrer-Policy"] = "no-referrer"
        resposta.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), payment=(), usb=()"
        )

        resposta.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        resposta.headers["Pragma"] = "no-cache"

        resposta.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        resposta.headers["Cross-Origin-Opener-Policy"] = "same-origin"

        for cabecalho_a_remover in ("server", "x-powered-by"):
            if cabecalho_a_remover in resposta.headers:
                del resposta.headers[cabecalho_a_remover]

        return resposta
