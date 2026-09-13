"""Testes funcionais das rotas da API."""

from fastapi.testclient import TestClient

from conftest import CREDENCIAIS, cabecalho_de_autorizacao


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------
def test_health_check(client: TestClient):
    resposta = client.get("/health")
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# /auth/token
# ---------------------------------------------------------------------------
def test_login_com_credenciais_invalidas(client: TestClient):
    resposta = client.post(
        "/auth/token", data={"username": "ana", "password": "senha-errada"}
    )
    assert resposta.status_code == 401


def test_login_com_credenciais_validas_retorna_token(client: TestClient):
    resposta = client.post(
        "/auth/token", data={"username": "ana", "password": CREDENCIAIS["ana"]}
    )
    assert resposta.status_code == 200

    corpo = resposta.json()
    assert "access_token" in corpo
    assert corpo["token_type"] == "bearer"


def test_login_do_admin_funciona(client: TestClient):
    resposta = client.post(
        "/auth/token", data={"username": "admin", "password": CREDENCIAIS["admin"]}
    )
    assert resposta.status_code == 200


# ---------------------------------------------------------------------------
# /predict
# ---------------------------------------------------------------------------
def test_predict_sem_token_retorna_401(client: TestClient):
    resposta = client.post("/predict", json={"text": "Meu produto não liga."})
    assert resposta.status_code == 401


def test_predict_com_token_valido_retorna_200(client: TestClient):
    resposta = client.post(
        "/predict",
        json={"text": "Meu produto não liga."},
        headers=cabecalho_de_autorizacao(client, "ana"),
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["text"] == "Meu produto não liga."
    assert "intent" in corpo


def test_predict_com_token_invalido_retorna_401(client: TestClient):
    resposta = client.post(
        "/predict",
        json={"text": "Meu produto não liga."},
        headers={"Authorization": "Bearer token-forjado-invalido"},
    )
    assert resposta.status_code == 401


def test_predict_com_texto_vazio_retorna_422(client: TestClient):
    resposta = client.post(
        "/predict",
        json={"text": ""},
        headers=cabecalho_de_autorizacao(client, "ana"),
    )
    assert resposta.status_code == 422


# ---------------------------------------------------------------------------
# /tickets
# ---------------------------------------------------------------------------
def test_criar_e_listar_ticket(client: TestClient):
    cabecalho = cabecalho_de_autorizacao(client, "ana")

    criacao = client.post(
        "/tickets/",
        json={"titulo": "Impressora não conecta", "descricao": "Não aparece na rede."},
        headers=cabecalho,
    )
    assert criacao.status_code == 201
    id_criado = criacao.json()["id"]

    listagem = client.get("/tickets/", headers=cabecalho)
    assert listagem.status_code == 200
    assert id_criado in [ticket["id"] for ticket in listagem.json()]


def test_atualizar_o_proprio_ticket(client: TestClient):
    cabecalho = cabecalho_de_autorizacao(client, "ana")

    criacao = client.post(
        "/tickets/",
        json={"titulo": "Título original", "descricao": "Descrição original."},
        headers=cabecalho,
    )
    id_criado = criacao.json()["id"]

    atualizacao = client.put(
        f"/tickets/{id_criado}",
        json={"titulo": "Título atualizado"},
        headers=cabecalho,
    )

    assert atualizacao.status_code == 200
    assert atualizacao.json()["titulo"] == "Título atualizado"
    # O campo não enviado deve permanecer intacto.
    assert atualizacao.json()["descricao"] == "Descrição original."


def test_remover_o_proprio_ticket(client: TestClient):
    cabecalho = cabecalho_de_autorizacao(client, "ana")

    criacao = client.post(
        "/tickets/",
        json={"titulo": "Chamado a remover", "descricao": "Texto."},
        headers=cabecalho,
    )
    id_criado = criacao.json()["id"]

    remocao = client.delete(f"/tickets/{id_criado}", headers=cabecalho)
    assert remocao.status_code == 204

    assert client.get(f"/tickets/{id_criado}", headers=cabecalho).status_code == 404


def test_titulo_curto_demais_retorna_422(client: TestClient):
    resposta = client.post(
        "/tickets/",
        json={"titulo": "ab", "descricao": "Descrição válida."},
        headers=cabecalho_de_autorizacao(client, "ana"),
    )
    assert resposta.status_code == 422
