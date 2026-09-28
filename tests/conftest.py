import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

PASTA_DA_API = Path(__file__).resolve().parent.parent / "fastapi"
if str(PASTA_DA_API) not in sys.path:
    sys.path.insert(0, str(PASTA_DA_API))

from database import pegar_sessao  
from main import app  
from models.prediction import Prediction  
from models.user import User
from security.password import gerar_hash_de_senha  
from security.rate_limit import limiter  


SENHAS = {"admin": "admin123", "analista": "analista123"}


@pytest.fixture(name="sessao")
def fixture_sessao():
    

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as sessao:
        admin = User(
            username="admin", hashed_password=gerar_hash_de_senha(SENHAS["admin"])
        )
        analista = User(
            username="analista",
            hashed_password=gerar_hash_de_senha(SENHAS["analista"]),
        )
        sessao.add_all([admin, analista])
        sessao.commit()
        sessao.refresh(admin)
        sessao.refresh(analista)

        sessao.add_all(
            [
                Prediction(
                    texto="Predição que pertence ao admin.",
                    intencao="Technical issue",
                    owner_id=admin.id,
                ),
                Prediction(
                    texto="Predição que pertence ao analista.",
                    intencao="Technical issue",
                    owner_id=analista.id,
                ),
            ]
        )
        sessao.commit()

        yield sessao


@pytest.fixture(name="client")
def fixture_client(sessao: Session):
  

    app.dependency_overrides[pegar_sessao] = lambda: sessao
    limiter.enabled = False

    with TestClient(app) as cliente:
        yield cliente

    app.dependency_overrides.clear()
    limiter.enabled = True


def token_de(cliente: TestClient, usuario: str) -> dict[str, str]:
   

    resposta = cliente.post(
        "/auth/token", data={"username": usuario, "password": SENHAS[usuario]}
    )
    assert resposta.status_code == 200, resposta.text
    return {"Authorization": f"Bearer {resposta.json()['access_token']}"}
