"""Testes básicos das 3 rotas exigidas na Etapa 1.

Executar com: pytest -v
"""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_login_com_credenciais_invalidas():
    response = client.post("/auth/token", data={"username": "admin", "password": "senha-errada"})
    assert response.status_code == 401


def test_login_com_credenciais_validas_retorna_token():
    response = client.post("/auth/token", data={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    corpo = response.json()
    assert "access_token" in corpo
    assert corpo["token_type"] == "bearer"


def test_predict_sem_token_retorna_401():
    response = client.post("/predict", json={"text": "Meu produto não liga."})
    assert response.status_code == 401


def test_predict_com_token_valido_retorna_200():
    login_response = client.post("/auth/token", data={"username": "admin", "password": "admin123"})
    token = login_response.json()["access_token"]

    response = client.post(
        "/predict",
        json={"text": "Meu produto não liga."},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    corpo = response.json()
    assert corpo["text"] == "Meu produto não liga."
    assert "intent" in corpo


def test_predict_com_token_invalido_retorna_401():
    response = client.post(
        "/predict",
        json={"text": "Meu produto não liga."},
        headers={"Authorization": "Bearer token-forjado-invalido"},
    )
    assert response.status_code == 401
