# Projeto de Bloco — Análise e Segurança de Agentes de IA

**Disciplina:** Análise e Segurança de Agentes de IA — Instituto Infnet
**Professor:** Tiago Cariolano de Souza Xavier
**Grupo:** Bernardo de Moraes Eleuterio, Felipe Roberto Rocha, Guilherme Valentim Ramalho da Silva e Heitor Cella Oliveira

---

## Objetivo do projeto

Construir um sistema de atendimento ao cliente apoiado por inteligência artificial, com foco na
**segurança da aplicação** que serve o modelo.

| Etapa | Escopo | Estado |
|---|---|---|
| **TP1** | Escolha do dataset, EDA inicial, estrutura da API com JWT, DFD e tríade CIA | Concluída |
| **TP2** | EDA aprofundada (correlação, testes de hipótese), controles OWASP Top 10 e auditoria com OWASP ZAP | Concluída |

---

## O que foi entregue no TP2

### Análise exploratória aprofundada

- Heatmap de correlação (Pearson e Spearman) sobre sete variáveis numéricas
- Quatro scatter plots de pares relevantes para o negócio
- Teste de hipótese formal (**Mann-Whitney U**, com teste t de Welch como verificação) sobre a
  Hipótese 3 do TP1
- Verificação quantitativa do sinal preditivo do dataset (qui-quadrado + baseline TF-IDF)
- Relatório estruturado em [`eda/RELATORIO_EDA.md`](eda/RELATORIO_EDA.md)

**Principal conclusão:** o dataset é sintético, com colunas geradas independentemente entre si.
A maior correlação informativa entre as variáveis é |r| ≈ 0,04, e um baseline TF-IDF + Regressão
Logística atinge 18,9% de acurácia — **abaixo** do modelo trivial (20,7%). O detalhamento e as três
alternativas propostas para a Etapa 3 estão no relatório de EDA.

### Segurança da API

| Controle | OWASP | Onde |
|---|---|---|
| Verificação de ownership (BOLA) | A01 | `fastapi/routes/tickets.py` |
| Persistência com SQLModel, queries parametrizadas | A03 | `fastapi/database.py` |
| `extra="forbid"` em todos os modelos de entrada | A08 | `fastapi/models/` |
| Cabeçalhos de segurança (HSTS, CSP, X-Frame-Options, nosniff) | A05 | `fastapi/security/middleware.py` |
| CORS com allowlist explícita | A05 | `fastapi/config.py` |
| Rate limiting no `/auth/token` | A07 | `fastapi/security/rate_limit.py` |
| Senhas em bcrypt | A02 | `fastapi/security/password.py` |

Documentação completa: [`security/OWASP_CONTROLES.md`](security/OWASP_CONTROLES.md) e
[`security/RATE_LIMITING.md`](security/RATE_LIMITING.md).

### Auditoria OWASP ZAP

Scan passivo com ZAP 2.16.1, executado em duas etapas (antes e depois dos controles):

| Severidade | ANTES (TP1) | DEPOIS (TP2) |
|---|---|---|
| High | 0 | 0 |
| **Medium** | **30** | **0** |
| Low | 17 | 0 |
| Informational | 21 | 18 |

Relatórios exportados em [`security/zap/`](security/zap/) e análise de cada finding em
[`security/ZAP_FINDINGS.md`](security/ZAP_FINDINGS.md).

### Testes

48 testes automatizados, sendo 36 especificamente de segurança.

---

## Estrutura de pastas

```
.
├── README.md
├── data/
│   └── customer_support_tickets.csv
├── eda/
│   ├── EDA_Customer_Support_Tickets.ipynb   # notebook executado, com gráficos
│   └── RELATORIO_EDA.md                     # relatório estruturado (TP2)
├── fastapi/
│   ├── main.py                  # app, middlewares, CORS, tratadores de erro
│   ├── run.py                   # inicializador com opções seguras de servidor
│   ├── config.py                # configuração central (TP2)
│   ├── database.py              # engine SQLModel e dados iniciais (TP2)
│   ├── requirements.txt
│   ├── models/                  # schemas Pydantic e tabelas SQLModel
│   │   ├── auth.py
│   │   ├── health.py
│   │   ├── predict.py
│   │   ├── ticket.py            # (TP2)
│   │   └── user.py              # (TP2)
│   ├── routes/
│   │   ├── auth.py              # login com rate limiting
│   │   ├── health.py
│   │   ├── predict.py
│   │   └── tickets.py           # CRUD com verificação de ownership (TP2)
│   ├── security/
│   │   ├── jwt_handler.py
│   │   ├── middleware.py        # cabeçalhos de segurança (TP2)
│   │   ├── oauth2.py
│   │   ├── password.py          # (TP2)
│   │   ├── rate_limit.py        # (TP2)
│   │   └── users.py
│   └── tests/
│       ├── conftest.py          # fixtures e banco isolado (TP2)
│       ├── test_api.py          # testes funcionais
│       └── test_security.py     # testes de segurança (TP2)
├── security/
│   ├── OWASP_CONTROLES.md       # mapa de controles por item do OWASP Top 10
│   ├── RATE_LIMITING.md         # justificativa técnica do limite escolhido
│   ├── ZAP_FINDINGS.md          # análise dos findings do scan
│   └── zap/                     # relatórios exportados + script do scan
└── others/
    └── dfd_api.jpg              # DFD da API (TP1)
```

---

## Instalação

Pré-requisito: Python 3.10 ou superior.

```bash
git clone <URL-DO-REPOSITORIO>
cd <NOME-DO-REPOSITORIO>

python3 -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows

cd fastapi
pip install -r requirements.txt
```

---

## Execução

### Desenvolvimento

```bash
cd fastapi
python run.py
```

A API sobe em <http://127.0.0.1:8000> e a documentação interativa fica em
<http://127.0.0.1:8000/docs>.

> **Por que `run.py` e não `uvicorn main:app`?** O uvicorn adiciona o cabeçalho `Server: uvicorn` na
> camada de protocolo, depois que o middleware da aplicação já terminou — então ele não pode ser
> removido pelo código da API. O `run.py` sobe o servidor já com `server_header=False`. O
> equivalente por linha de comando é `uvicorn main:app --no-server-header --no-date-header`.

### Produção

```bash
cd fastapi
export APP_ENV=production
export JWT_SECRET_KEY="<chave-forte-vinda-de-um-gerenciador-de-segredos>"
export CORS_ALLOWED_ORIGINS="https://app.suaempresa.com"
python run.py
```

Em produção, `/docs`, `/redoc` e `/openapi.json` são **desabilitados** — eles exigiriam relaxar a
CSP com `unsafe-inline` e entregariam o mapa completo da API (ver `security/ZAP_FINDINGS.md`).

### Variáveis de ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `APP_ENV` | `development` | `production` ativa o modo endurecido |
| `JWT_SECRET_KEY` | chave de desenvolvimento | Chave de assinatura dos tokens |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Validade do token |
| `DATABASE_URL` | `sqlite:///./customer_support.db` | Conexão do banco |
| `CORS_ALLOWED_ORIGINS` | `localhost:3000,localhost:5173,...` | Allowlist de origens |
| `RATE_LIMIT_LOGIN` | `5/minute` | Limite do endpoint de login |
| `RATE_LIMIT_DEFAULT` | `100/minute` | Limite das demais rotas |
| `TRUST_PROXY_HEADERS` | `false` | Só ative atrás de um proxy reverso confiável |

---

## Usuários de exemplo

Criados automaticamente na primeira execução (`database.py`):

| Usuário | Senha | Papel |
|---|---|---|
| `admin` | `admin123` | admin — enxerga todos os chamados |
| `ana` | `ana12345` | user — dona dos chamados 1 e 2 |
| `bruno` | `bruno12345` | user — dono do chamado 3 |

Os dois usuários comuns existem para tornar verificável o controle de ownership: sem múltiplos
usuários reais, não há como testar o acesso ao recurso de outra pessoa.

> Credenciais de demonstração, adequadas apenas ao ambiente didático.

---

## Rotas

| Método | Rota | Autenticação | Descrição |
|---|---|---|---|
| GET | `/health` | — | Health check |
| POST | `/auth/token` | — | Login (rate limit: 5/min) |
| POST | `/predict` | JWT | Classificação de intenção (simulada) |
| GET | `/tickets/` | JWT | Lista **apenas** os chamados do usuário |
| POST | `/tickets/` | JWT | Cria chamado (dono vem do token) |
| GET | `/tickets/{id}` | JWT + ownership | Obtém chamado |
| PUT | `/tickets/{id}` | JWT + ownership | Atualiza chamado |
| DELETE | `/tickets/{id}` | JWT + ownership | Remove chamado |

### Exemplo de uso

```bash
# Login
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/auth/token \
  -d "username=ana&password=ana12345" | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

# Listar os próprios chamados
curl http://127.0.0.1:8000/tickets/ -H "Authorization: Bearer $TOKEN"

# Tentar acessar o chamado do Bruno (id 3) -> 404, não 403
curl -i http://127.0.0.1:8000/tickets/3 -H "Authorization: Bearer $TOKEN"

# Enviar campo extra no corpo -> 422
curl -i -X POST http://127.0.0.1:8000/tickets/ \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"titulo":"Teste","descricao":"Texto","owner_id":2}'
```

---

## Testes

```bash
cd fastapi
pytest tests/ -v
```

Resultado esperado: **48 testes aprovados**.

| Arquivo | Testes | Cobertura |
|---|---|---|
| `tests/test_api.py` | 12 | Rotas, validação e CRUD |
| `tests/test_security.py` | 36 | Acesso sem token, BOLA, campos extras, cabeçalhos, CORS, rate limiting, vazamento de dados |

Os três casos exigidos no enunciado do TP2:

| Caso | Classe de teste |
|---|---|
| (a) acesso sem token | `TestAcessoSemToken` |
| (b) acesso a recurso de outro usuário | `TestBrokenObjectLevelAuthorization` |
| (c) campo extra no corpo da requisição | `TestCamposExtrasProibidos` |

---

## Notebook de EDA

```bash
cd eda
jupyter notebook EDA_Customer_Support_Tickets.ipynb
```

O notebook já está executado, com todos os gráficos e resultados salvos. Ele localiza o CSV
automaticamente, funcionando tanto a partir da pasta `eda/` quanto da raiz do projeto.

Dependências da análise:

```bash
pip install pandas numpy matplotlib seaborn scipy scikit-learn jupyter
```

---

## Segurança — DFD e tríade CIA

O diagrama de fluxo de dados da API está em [`others/dfd_api.jpg`](others/dfd_api.jpg), produzido no
TP1 junto com a análise da tríade CIA.
