"""Configuração compartilhada e isolamento do banco para testes."""

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

# ---------------------------------------------------------------------------
# 1. Garante que os módulos da API sejam importáveis
# ---------------------------------------------------------------------------
DIRETORIO_DA_API = Path(__file__).resolve().parent.parent
if str(DIRETORIO_DA_API) not in sys.path:
    sys.path.insert(0, str(DIRETORIO_DA_API))

# Variáveis de ambiente devem ser configuradas antes da aplicação
os.environ.setdefault("JWT_SECRET_KEY", "chave-de-teste-isolada-do-ambiente-real")

from database import obter_sessao  # noqa: E402
from main import app  # noqa: E402
from models.ticket import Ticket  # noqa: E402
from models.user import User  # noqa: E402
from security.password import gerar_hash_de_senha  # noqa: E402
from security.rate_limit import limiter  # noqa: E402

CREDENCIAIS = {
    "ana": "ana12345",
    "bruno": "bruno12345",
    "admin": "admin123",
}


@pytest.fixture(name="sessao")
def fixture_sessao():
    """Banco SQLite em memória, recriado a cada teste."""

    engine_de_teste = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine_de_teste)

    with Session(engine_de_teste) as sessao:
        ana = User(
            username="ana",
            hashed_password=gerar_hash_de_senha(CREDENCIAIS["ana"]),
            role="user",
        )
        bruno = User(
            username="bruno",
            hashed_password=gerar_hash_de_senha(CREDENCIAIS["bruno"]),
            role="user",
        )
        admin = User(
            username="admin",
            hashed_password=gerar_hash_de_senha(CREDENCIAIS["admin"]),
            role="admin",
        )
        sessao.add_all([ana, bruno, admin])
        sessao.commit()
        for usuario in (ana, bruno, admin):
            sessao.refresh(usuario)

        sessao.add_all(
            [
                Ticket(
                    titulo="Chamado da Ana",
                    descricao="Produto não liga após a atualização.",
                    owner_id=ana.id,
                ),
                Ticket(
                    titulo="Chamado do Bruno",
                    descricao="Quero cancelar a assinatura.",
                    owner_id=bruno.id,
                ),
            ]
        )
        sessao.commit()

        yield sessao

    SQLModel.metadata.drop_all(engine_de_teste)


@pytest.fixture(name="client")
def fixture_client(sessao: Session):
    """Cliente HTTP de teste."""

    def substituir_sessao():
        return sessao

    app.dependency_overrides[obter_sessao] = substituir_sessao
    limiter.enabled = False

    with TestClient(app) as cliente:
        yield cliente

    app.dependency_overrides.clear()
    limiter.enabled = True


@pytest.fixture(name="client_com_rate_limit")
def fixture_client_com_rate_limit(sessao: Session):
    """Cliente de teste com rate limiting ativo."""

    def substituir_sessao():
        return sessao

    app.dependency_overrides[obter_sessao] = substituir_sessao
    limiter.enabled = True
    limiter.reset()

    with TestClient(app) as cliente:
        yield cliente

    app.dependency_overrides.clear()
    limiter.reset()


def autenticar(cliente: TestClient, usuario: str) -> str:
    """Faz login e devolve o token JWT do usuário informado."""

    resposta = cliente.post(
        "/auth/token",
        data={"username": usuario, "password": CREDENCIAIS[usuario]},
    )
    assert resposta.status_code == 200, resposta.text
    return resposta.json()["access_token"]


def cabecalho_de_autorizacao(cliente: TestClient, usuario: str) -> dict[str, str]:
    """Monta o header Authorization pronto para uso nos testes."""

    return {"Authorization": f"Bearer {autenticar(cliente, usuario)}"}
