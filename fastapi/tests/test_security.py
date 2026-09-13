"""Testes de segurança da API.

Executar com:  pytest tests/ -v
"""

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from conftest import CREDENCIAIS, cabecalho_de_autorizacao
from models.ticket import Ticket


class TestAcessoSemToken:
    """Rotas protegidas devem recusar requisições não autenticadas."""

    def test_listar_tickets_sem_token_retorna_401(self, client: TestClient):
        resposta = client.get("/tickets/")
        assert resposta.status_code == 401

    def test_obter_ticket_por_id_sem_token_retorna_401(self, client: TestClient):
        resposta = client.get("/tickets/1")
        assert resposta.status_code == 401

    def test_criar_ticket_sem_token_retorna_401(self, client: TestClient):
        resposta = client.post(
            "/tickets/",
            json={"titulo": "Chamado sem autenticação", "descricao": "teste"},
        )
        assert resposta.status_code == 401

    def test_predict_sem_token_retorna_401(self, client: TestClient):
        resposta = client.post("/predict", json={"text": "Meu produto não liga."})
        assert resposta.status_code == 401

    def test_token_invalido_retorna_401(self, client: TestClient):
        resposta = client.get(
            "/tickets/",
            headers={"Authorization": "Bearer token-forjado-invalido"},
        )
        assert resposta.status_code == 401

    def test_token_assinado_com_outra_chave_retorna_401(self, client: TestClient):
        """Um JWT bem formado, mas assinado com outra chave, deve ser recusado."""
        import jwt

        token_forjado = jwt.encode(
            {"sub": "1", "username": "ana", "role": "admin", "exp": 9999999999},
            "chave-do-atacante",
            algorithm="HS256",
        )

        resposta = client.get(
            "/tickets/", headers={"Authorization": f"Bearer {token_forjado}"}
        )
        assert resposta.status_code == 401

    def test_resposta_401_nao_revela_motivo_especifico(self, client: TestClient):
        """A mensagem de erro não deve distinguir token ausente de expirado."""
        sem_token = client.get("/tickets/").json()
        token_ruim = client.get(
            "/tickets/", headers={"Authorization": "Bearer xyz"}
        ).json()

        assert sem_token["detail"] == token_ruim["detail"]


class TestBrokenObjectLevelAuthorization:
    """Um usuário autenticado não pode acessar o recurso de outro usuário."""

    def test_usuario_acessa_o_proprio_ticket(self, client: TestClient, sessao: Session):
        ticket_da_ana = sessao.exec(
            select(Ticket).where(Ticket.titulo == "Chamado da Ana")
        ).first()

        resposta = client.get(
            f"/tickets/{ticket_da_ana.id}",
            headers=cabecalho_de_autorizacao(client, "ana"),
        )

        assert resposta.status_code == 200
        assert resposta.json()["titulo"] == "Chamado da Ana"

    def test_usuario_NAO_acessa_ticket_de_outro_usuario(
        self, client: TestClient, sessao: Session
    ):
        """Bruno tenta ler o chamado da Ana pelo ID."""
        ticket_da_ana = sessao.exec(
            select(Ticket).where(Ticket.titulo == "Chamado da Ana")
        ).first()

        resposta = client.get(
            f"/tickets/{ticket_da_ana.id}",
            headers=cabecalho_de_autorizacao(client, "bruno"),
        )

        assert resposta.status_code == 404
        assert "Chamado da Ana" not in resposta.text

    def test_usuario_NAO_atualiza_ticket_de_outro_usuario(
        self, client: TestClient, sessao: Session
    ):
        ticket_da_ana = sessao.exec(
            select(Ticket).where(Ticket.titulo == "Chamado da Ana")
        ).first()
        id_do_ticket = ticket_da_ana.id

        resposta = client.put(
            f"/tickets/{id_do_ticket}",
            json={"titulo": "Título sequestrado pelo Bruno"},
            headers=cabecalho_de_autorizacao(client, "bruno"),
        )

        assert resposta.status_code == 404

        sessao.expire_all()
        ticket_apos = sessao.exec(
            select(Ticket).where(Ticket.id == id_do_ticket)
        ).first()
        assert ticket_apos.titulo == "Chamado da Ana"

    def test_usuario_NAO_remove_ticket_de_outro_usuario(
        self, client: TestClient, sessao: Session
    ):
        ticket_da_ana = sessao.exec(
            select(Ticket).where(Ticket.titulo == "Chamado da Ana")
        ).first()
        id_do_ticket = ticket_da_ana.id

        resposta = client.delete(
            f"/tickets/{id_do_ticket}",
            headers=cabecalho_de_autorizacao(client, "bruno"),
        )

        assert resposta.status_code == 404

        sessao.expire_all()
        assert sessao.exec(select(Ticket).where(Ticket.id == id_do_ticket)).first()

    def test_listagem_devolve_apenas_os_proprios_tickets(self, client: TestClient):
        resposta = client.get(
            "/tickets/", headers=cabecalho_de_autorizacao(client, "bruno")
        )

        assert resposta.status_code == 200
        titulos = [ticket["titulo"] for ticket in resposta.json()]
        assert "Chamado do Bruno" in titulos
        assert "Chamado da Ana" not in titulos

    def test_admin_acessa_qualquer_ticket(self, client: TestClient, sessao: Session):
        """O papel de admin é a única exceção prevista à regra de ownership."""
        ticket_da_ana = sessao.exec(
            select(Ticket).where(Ticket.titulo == "Chamado da Ana")
        ).first()

        resposta = client.get(
            f"/tickets/{ticket_da_ana.id}",
            headers=cabecalho_de_autorizacao(client, "admin"),
        )

        assert resposta.status_code == 200

    def test_ticket_inexistente_e_ticket_alheio_sao_indistinguiveis(
        self, client: TestClient, sessao: Session
    ):
        """Ambos devem responder 404 com o mesmo corpo."""
        ticket_da_ana = sessao.exec(
            select(Ticket).where(Ticket.titulo == "Chamado da Ana")
        ).first()
        cabecalho = cabecalho_de_autorizacao(client, "bruno")

        resposta_alheio = client.get(f"/tickets/{ticket_da_ana.id}", headers=cabecalho)
        resposta_inexistente = client.get("/tickets/999999", headers=cabecalho)

        assert resposta_alheio.status_code == resposta_inexistente.status_code == 404
        assert resposta_alheio.json() == resposta_inexistente.json()


class TestCamposExtrasProibidos:
    """``extra="forbid"`` deve rejeitar qualquer campo não declarado."""

    def test_campo_extra_em_predict_retorna_422(self, client: TestClient):
        resposta = client.post(
            "/predict",
            json={"text": "Meu produto não liga.", "campo_extra": "valor malicioso"},
            headers=cabecalho_de_autorizacao(client, "ana"),
        )
        assert resposta.status_code == 422

    def test_campo_extra_na_criacao_de_ticket_retorna_422(self, client: TestClient):
        resposta = client.post(
            "/tickets/",
            json={
                "titulo": "Chamado legítimo",
                "descricao": "Descrição do problema.",
                "campo_inesperado": "algum valor",
            },
            headers=cabecalho_de_autorizacao(client, "ana"),
        )
        assert resposta.status_code == 422

    def test_tentativa_de_mass_assignment_de_owner_id_retorna_422(
        self, client: TestClient
    ):
        """Ana tenta criar um chamado já atribuído ao Bruno."""
        resposta = client.post(
            "/tickets/",
            json={
                "titulo": "Chamado com dono forjado",
                "descricao": "Tentativa de mass assignment.",
                "owner_id": 2,
            },
            headers=cabecalho_de_autorizacao(client, "ana"),
        )
        assert resposta.status_code == 422

    def test_tentativa_de_escalar_privilegio_via_campo_role_retorna_422(
        self, client: TestClient
    ):
        resposta = client.post(
            "/tickets/",
            json={
                "titulo": "Chamado comum",
                "descricao": "Tentativa de escalar privilégio.",
                "role": "admin",
            },
            headers=cabecalho_de_autorizacao(client, "ana"),
        )
        assert resposta.status_code == 422

    def test_ticket_valido_sem_campos_extras_e_aceito(self, client: TestClient):
        """Controle negativo: a requisição correta deve continuar funcionando."""
        resposta = client.post(
            "/tickets/",
            json={"titulo": "Chamado válido", "descricao": "Descrição adequada."},
            headers=cabecalho_de_autorizacao(client, "ana"),
        )
        assert resposta.status_code == 201
        assert resposta.json()["titulo"] == "Chamado válido"

    def test_owner_id_do_ticket_criado_vem_do_token_e_nao_do_corpo(
        self, client: TestClient, sessao: Session
    ):
        from models.user import User

        ana = sessao.exec(select(User).where(User.username == "ana")).first()

        resposta = client.post(
            "/tickets/",
            json={"titulo": "Chamado da própria Ana", "descricao": "Texto."},
            headers=cabecalho_de_autorizacao(client, "ana"),
        )

        assert resposta.status_code == 201
        assert resposta.json()["owner_id"] == ana.id


class TestCabecalhosDeSeguranca:
    """Todos os cabeçalhos exigidos devem estar presentes."""

    def test_hsts_presente(self, client: TestClient):
        cabecalhos = client.get("/health").headers
        assert "max-age=" in cabecalhos["Strict-Transport-Security"]
        assert "includeSubDomains" in cabecalhos["Strict-Transport-Security"]

    def test_x_frame_options_deny(self, client: TestClient):
        assert client.get("/health").headers["X-Frame-Options"] == "DENY"

    def test_x_content_type_options_nosniff(self, client: TestClient):
        assert client.get("/health").headers["X-Content-Type-Options"] == "nosniff"

    def test_content_security_policy_restritiva_nas_rotas_de_api(
        self, client: TestClient
    ):
        csp = client.get("/health").headers["Content-Security-Policy"]
        assert "default-src 'none'" in csp
        assert "frame-ancestors 'none'" in csp

    def test_cabecalhos_presentes_tambem_em_respostas_de_erro(
        self, client: TestClient
    ):
        """Um erro também precisa carregar os cabeçalhos de segurança."""
        cabecalhos = client.get("/tickets/").headers
        assert cabecalhos["X-Frame-Options"] == "DENY"
        assert cabecalhos["X-Content-Type-Options"] == "nosniff"
        assert "Content-Security-Policy" in cabecalhos

    def test_servidor_nao_expoe_versao(self, client: TestClient):
        servidor = client.get("/health").headers.get("Server", "")
        assert "uvicorn" not in servidor.lower()

    def test_respostas_nao_sao_cacheadas(self, client: TestClient):
        assert "no-store" in client.get("/health").headers["Cache-Control"]


class TestCORS:
    """A allowlist deve aceitar apenas as origens explicitamente configuradas."""

    def test_origem_permitida_recebe_cabecalho_cors(self, client: TestClient):
        resposta = client.get(
            "/health", headers={"Origin": "http://localhost:3000"}
        )
        assert resposta.headers.get("access-control-allow-origin") == (
            "http://localhost:3000"
        )

    def test_origem_nao_autorizada_nao_recebe_cabecalho_cors(self, client: TestClient):
        resposta = client.get(
            "/health", headers={"Origin": "https://site-malicioso.example.com"}
        )
        assert "access-control-allow-origin" not in resposta.headers

    def test_nao_existe_curinga_na_allowlist(self, client: TestClient):
        resposta = client.get(
            "/health", headers={"Origin": "https://qualquer-site.example.com"}
        )
        assert resposta.headers.get("access-control-allow-origin") != "*"


class TestRateLimiting:
    """O endpoint de login deve bloquear tentativas repetidas de força bruta."""

    def test_forca_bruta_no_login_e_bloqueada_com_429(
        self, client_com_rate_limit: TestClient
    ):
        codigos_obtidos = []

        for _ in range(12):
            resposta = client_com_rate_limit.post(
                "/auth/token",
                data={"username": "ana", "password": "senha-errada"},
            )
            codigos_obtidos.append(resposta.status_code)

        assert 429 in codigos_obtidos, (
            f"O rate limiting não bloqueou a força bruta. Códigos: {codigos_obtidos}"
        )
        assert codigos_obtidos.index(429) <= 10

    def test_resposta_429_nao_revela_tentativas_restantes(
        self, client_com_rate_limit: TestClient
    ):
        resposta_bloqueada = None
        for _ in range(12):
            resposta = client_com_rate_limit.post(
                "/auth/token", data={"username": "ana", "password": "errada"}
            )
            if resposta.status_code == 429:
                resposta_bloqueada = resposta
                break

        assert resposta_bloqueada is not None
        corpo = resposta_bloqueada.json()["detail"].lower()
        assert "tente novamente" in corpo
        assert "5" not in corpo


class TestVazamentoDeDados:
    """Dados sensíveis nunca devem aparecer nas respostas da API."""

    def test_login_nao_devolve_hash_de_senha(self, client: TestClient):
        resposta = client.post(
            "/auth/token", data={"username": "ana", "password": CREDENCIAIS["ana"]}
        )
        corpo = resposta.text.lower()
        assert "hashed_password" not in corpo
        assert "$2b$" not in corpo

    def test_erro_de_validacao_nao_ecoa_a_senha_enviada(self, client: TestClient):
        """O corpo do 422 não pode conter o valor enviado pelo usuário."""
        senha_secreta = "MinhaSenhaSuperSecreta123"
        resposta = client.post(
            "/predict",
            json={"text": "", "password": senha_secreta},
            headers=cabecalho_de_autorizacao(client, "ana"),
        )

        assert resposta.status_code == 422
        assert senha_secreta not in resposta.text

    def test_credenciais_invalidas_nao_distinguem_usuario_inexistente(
        self, client: TestClient
    ):
        """Usuário inexistente e senha errada devem dar a mesma resposta."""
        inexistente = client.post(
            "/auth/token",
            data={"username": "usuario-que-nao-existe", "password": "x"},
        )
        senha_errada = client.post(
            "/auth/token", data={"username": "ana", "password": "senha-errada"}
        )

        assert inexistente.status_code == senha_errada.status_code == 401
        assert inexistente.json() == senha_errada.json()

    def test_erro_interno_nao_expoe_stack_trace(self, client: TestClient):
        """Um ID fora da faixa de int não deve produzir traceback."""
        resposta = client.get(
            "/tickets/abc", headers=cabecalho_de_autorizacao(client, "ana")
        )
        assert resposta.status_code == 422
        assert "Traceback" not in resposta.text
        assert "sqlalchemy" not in resposta.text.lower()
