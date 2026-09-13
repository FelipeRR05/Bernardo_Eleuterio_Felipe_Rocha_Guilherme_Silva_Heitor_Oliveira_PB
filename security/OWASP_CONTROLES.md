# Controles de Segurança OWASP Top 10 - Customer Support Intent API

Documento de referência dos controles implementados na Etapa 2 (TP2), com o ponto exato do código
onde cada um vive e o teste automatizado que o verifica.

---

## Mapa de controles

| OWASP Top 10 (2021) | Controle implementado | Arquivo | Teste |
|---|---|---|---|
| **A01** - Broken Access Control | Verificação de *ownership* (BOLA) nas rotas por ID | `routes/tickets.py` | `TestBrokenObjectLevelAuthorization` |
| **A01** | Filtragem por dono na consulta ao banco (listagem) | `routes/tickets.py` | `test_listagem_devolve_apenas_os_proprios_tickets` |
| **A01** | Papel de admin isolado em dependência dedicada | `security/oauth2.py` | `test_admin_acessa_qualquer_ticket` |
| **A02** - Cryptographic Failures | Senhas em hash bcrypt com salt por senha | `security/password.py` | `test_login_nao_devolve_hash_de_senha` |
| **A02** | Hash de senha nunca serializado em resposta | `models/user.py` (`UserPublic`) | idem |
| **A03** - Injection | Acesso a dados exclusivamente via ORM parametrizado | `database.py`, `routes/tickets.py` | suíte inteira |
| **A05** - Security Misconfiguration | Cabeçalhos de segurança HTTP | `security/middleware.py` | `TestCabecalhosDeSeguranca` |
| **A05** | CORS com allowlist explícita | `main.py`, `config.py` | `TestCORS` |
| **A05** | Documentação interativa desabilitada em produção | `main.py` | verificado no scan ZAP |
| **A05** | Stack traces e detalhes internos suprimidos | `main.py` | `test_erro_interno_nao_expoe_stack_trace` |
| **A05** | Cabeçalho `Server` removido | `security/middleware.py`, `run.py` | `test_servidor_nao_expoe_versao` |
| **A07** - Authentication Failures | Rate limiting no `/auth/token` | `routes/auth.py`, `security/rate_limit.py` | `TestRateLimiting` |
| **A07** | Mensagem de erro genérica no login | `routes/auth.py`, `security/users.py` | `test_credenciais_invalidas_nao_distinguem_usuario_inexistente` |
| **A07** | Defesa contra enumeração por tempo de resposta | `security/users.py` | - |
| **A07** | JWT com algoritmo fixo e expiração obrigatória | `security/jwt_handler.py` | `test_token_assinado_com_outra_chave_retorna_401` |
| **A08** - Data Integrity Failures | `extra="forbid"` em todos os modelos de entrada | `models/*.py` | `TestCamposExtrasProibidos` |
| **A08** | `owner_id` derivado do token, nunca do corpo | `routes/tickets.py` | `test_owner_id_do_ticket_criado_vem_do_token_e_nao_do_corpo` |
| **A09** - Logging Failures | Erros de validação sanitizados antes de virar log | `main.py` | `test_erro_de_validacao_nao_ecoa_a_senha_enviada` |

---

## A01 - Broken Access Control (BOLA)

### O problema

BOLA (*Broken Object Level Authorization*) é o item **nº 1 do OWASP API Security Top 10**. A falha
aparece quando a API confirma que o usuário está **autenticado**, mas esquece de verificar se ele
está **autorizado naquele objeto específico**. O ataque é trivial: o usuário logado troca o ID na
URL e lê o recurso de outra pessoa.

### A implementação

Toda rota que acessa um chamado por ID passa por `_buscar_ticket_do_usuario()`
(`routes/tickets.py`), que confere `ticket.owner_id == usuario.id` antes de devolver qualquer dado.

### Decisão de projeto: responder 404 em vez de 403

Quando o chamado existe mas pertence a outra pessoa, a API responde **404 Not Found** - não 403
Forbidden.

Um 403 significaria, na prática, *"este recurso existe, mas não é seu"*. Essa confirmação permite ao
atacante iterar sobre os IDs e **mapear a base inteira**, descobrindo quantos chamados existem e
quais IDs estão ocupados, mesmo sem conseguir lê-los. Com 404, "não existe" e "não é seu" são
respostas idênticas, e o atacante não extrai informação alguma.

O teste `test_ticket_inexistente_e_ticket_alheio_sao_indistinguiveis` garante que as duas respostas
permanecem byte a byte iguais.

### Listagem: filtro na consulta, não em memória

`GET /tickets/` aplica `where(Ticket.owner_id == usuario.id)` **na consulta SQL**. Filtrar depois,
em Python, criaria a chance de um chamado alheio ser carregado e acidentalmente serializado numa
futura alteração do código.

---

## A03 - Injection

Não existe **nenhuma** query SQL construída por concatenação de strings no projeto. Todo acesso a
dados usa o ORM do SQLModel:

```python
# Correto: o valor vira um parâmetro vinculado (prepared statement)
usuario = sessao.exec(select(User).where(User.username == username)).first()

# Nunca feito neste projeto:
# sessao.execute(f"SELECT * FROM user WHERE username = '{username}'")
```

Com o ORM, um `username` como `admin' OR '1'='1` é tratado como **texto literal** procurado na
coluna, não como fragmento de SQL a ser executado.

---

## A05 - Security Misconfiguration

### Cabeçalhos de segurança (`security/middleware.py`)

| Cabeçalho | Valor | Ataque mitigado |
|---|---|---|
| `Strict-Transport-Security` | `max-age=63072000; includeSubDomains; preload` | Downgrade para HTTP / SSL stripping |
| `X-Frame-Options` | `DENY` | Clickjacking |
| `X-Content-Type-Options` | `nosniff` | MIME sniffing (JSON reinterpretado como HTML/JS) |
| `Content-Security-Policy` | `default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'` | XSS, injeção de recursos externos |
| `Referrer-Policy` | `no-referrer` | Vazamento de URLs (com IDs) para terceiros |
| `Permissions-Policy` | `geolocation=(), microphone=(), camera=(), payment=(), usb=()` | Abuso de APIs sensíveis do navegador |
| `Cache-Control` | `no-store, no-cache, must-revalidate` | Resposta autenticada retida em cache compartilhado |
| `Cross-Origin-Resource-Policy` | `same-origin` | Leitura cross-origin (classe Spectre) |
| `Cross-Origin-Opener-Policy` | `same-origin` | Manipulação entre janelas |

O `max-age` de 2 anos (63.072.000 s) é o mínimo exigido para inclusão na *preload list* dos
navegadores.

### CSP: por que `default-src 'none'` é possível aqui

A aplicação é uma API que devolve **exclusivamente JSON** - não carrega scripts, estilos, imagens
nem fontes. Isso permite a política mais restritiva que existe, algo geralmente inviável em
aplicações web tradicionais.

### O trade-off da documentação interativa

O Swagger UI (`/docs`) é uma página HTML que carrega JavaScript de uma CDN externa e **exige
`'unsafe-inline'`** para inicializar. Isso enfraquece a CSP - e foi exatamente o que o OWASP ZAP
apontou no primeiro scan de verificação (alertas *Medium* `CSP: script-src unsafe-inline` e
`CSP: style-src unsafe-inline`).

**Solução adotada:** a documentação interativa é mantida em desenvolvimento, por produtividade, e
**desabilitada em produção** (`APP_ENV=production`), junto com `/openapi.json`. Em produção não
existe página HTML alguma, a CSP estrita vale para todas as rotas e o mapa completo da API deixa de
ser público. Ver `main.py` (`docs_url=None if EM_PRODUCAO else "/docs"`) e a lógica correspondente
no middleware.

### Cabeçalho `Server`

O uvicorn anuncia `Server: uvicorn` na camada de protocolo HTTP, **depois** que o middleware já
montou a resposta - por isso não é possível removê-lo de dentro do middleware. A remoção acontece na
configuração do servidor, em `run.py` (`server_header=False`), e o middleware garante que nenhum
outro componente o reintroduza.

### CORS com allowlist explícita (`config.py`)

```python
CORS_ORIGENS_PERMITIDAS = ["http://localhost:3000", "http://localhost:5173", ...]
```

**Nunca `["*"]`.** Com `allow_credentials=True`, um curinga permitiria que qualquer site lesse
respostas autenticadas da API a partir do navegador de um usuário logado. As origens são
configuráveis por variável de ambiente (`CORS_ALLOWED_ORIGINS`), para que produção não herde as
origens de desenvolvimento.

---

## A07 - Identification and Authentication Failures

### Rate limiting

Detalhado em [`RATE_LIMITING.md`](RATE_LIMITING.md).

### Mensagens de erro que não vazam informação

Login com **usuário inexistente** e login com **senha errada** produzem exatamente a mesma resposta
(401, mesmo corpo JSON). Se diferissem, um atacante testaria uma lista de nomes e descobriria quais
existem - reduzindo o ataque de força bruta a apenas os usuários válidos.

### Defesa contra enumeração por tempo de resposta

Confirmar um usuário inexistente é naturalmente mais rápido do que verificar uma senha (bcrypt é
deliberadamente lento). Essa diferença de tempo é mensurável e revela quais usuários existem. Por
isso, `security/users.py` executa uma verificação bcrypt contra um **hash fictício** quando o
usuário não é encontrado, igualando os tempos.

### JWT

| Controle | Implementação |
|---|---|
| Algoritmo fixado na decodificação | `algorithms=["HS256"]` - bloqueia *algorithm confusion* (`alg: none`, troca para RS256) |
| Expiração obrigatória | `options={"require": ["exp", "sub"]}` |
| Identificador único por token | `jti` (UUID), habilita revogação via denylist no futuro |
| `sub` com o **id**, não o nome | Autorização não depende de campo que o usuário possa alterar |
| Chave secreta fora do código | `JWT_SECRET_KEY` por variável de ambiente; em produção sem a variável, gera chave aleatória em memória em vez de usar um padrão publicado |

---

## A08 - Software and Data Integrity Failures

### `extra="forbid"` em todos os modelos de entrada

```python
class TicketCreate(SQLModel):
    model_config = ConfigDict(extra="forbid")
    titulo: str
    descricao: str
```

Sem essa configuração, o Pydantic **descarta silenciosamente** campos desconhecidos. Com ela, a API
responde **HTTP 422**.

Dois ganhos concretos:

1. **Bloqueia *mass assignment***: uma tentativa de enviar `{"titulo": "x", "owner_id": 2}` ou
   `{"titulo": "x", "role": "admin"}` é rejeitada. Mesmo que uma futura alteração passe a repassar o
   dicionário completo ao modelo de banco, o ataque não chega lá.
2. **Torna a tentativa visível**: o 422 aparece nos logs. O descarte silencioso não deixa rastro,
   e um atacante pode sondar campos indefinidamente sem ser notado.

### `owner_id` sempre derivado do token

O schema `TicketCreate` **não declara** `owner_id`. O dono é lido do JWT no servidor:

```python
ticket = Ticket(titulo=dados.titulo, descricao=dados.descricao, owner_id=usuario.id)
```

---

## A09 - Security Logging and Monitoring Failures

O tratador de `RequestValidationError` em `main.py` remove o campo `input` da resposta padrão do
FastAPI. Esse campo devolve ao cliente **o valor exato que ele enviou** - numa falha de validação no
endpoint de login, isso significaria ecoar a senha digitada de volta na resposta, onde ela seria
capturada por logs de proxy e ferramentas de monitoramento.

O teste `test_erro_de_validacao_nao_ecoa_a_senha_enviada` verifica esse comportamento.

---

## Pendências conhecidas

Itens fora do escopo do TP2, registrados para as próximas etapas:

| Item | Risco atual | Encaminhamento |
|---|---|---|
| Rate limiting em memória | Não compartilhado entre réplicas | Backend Redis (`slowapi` já suporta) |
| Sem revogação de token | Token roubado vale até expirar (30 min) | Denylist de `jti` em Redis |
| Sem refresh token | Sessões longas exigem novo login | Fluxo de refresh com rotação |
| SQLite | Inadequado para concorrência em produção | PostgreSQL |
| Sem auditoria estruturada | Difícil investigar incidentes | Log estruturado de eventos de autenticação e negação de acesso |
| HTTPS não terminado na aplicação | HSTS só tem efeito sob TLS | TLS no proxy reverso à frente |
