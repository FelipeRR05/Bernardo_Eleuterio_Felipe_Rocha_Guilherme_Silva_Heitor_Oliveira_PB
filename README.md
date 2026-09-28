# Projeto de Bloco - Análise e Segurança de Agentes de IA

**Disciplina:** Projeto de Bloco: Análise e Segurança de Agentes de IA - Instituto Infnet
**Professor:** Tiago Cariolano de Souza Xavier
**Grupo:** Bernardo de Moraes Eleuterio, Felipe Roberto Rocha, Guilherme Valentim Ramalho da Silva e Heitor Cella Oliveira

---

## Objetivo do projeto

Construir um sistema de atendimento ao cliente apoiado por IA e, principalmente, **cuidar da
segurança da aplicação que serve esse sistema**. A ideia do bloco é que, mais para a frente, um
colega tente invadir esta API - então quanto mais sólida ela estiver agora, melhor.

Nesta etapa (TP2) entregamos duas coisas:

1. O **EDA completo** do dataset de chamados de suporte, com análise multivariada, identificação
   de outliers e testes de hipótese formais.
2. A **API FastAPI com os controles do OWASP Top 10 aplicados** e auditada com um scan passivo do
   OWASP ZAP.

**O principal achado do EDA:** o dataset é sintético e suas colunas foram geradas de forma
independente umas das outras. A correlação mais forte entre variáveis distintas é |r| ≈ 0,04, e
69,3% dos chamados começam com exatamente o mesmo texto, rotulado com as cinco intenções. Isso
significa que o classificador previsto para o TP3 não funcionaria acima do acaso com esses dados.
A discussão completa e as três alternativas que levantamos estão na seção 1.8 do notebook.

---

## Estrutura de pastas

```
.
├── README.md
├── data/
│   └── customer_support_tickets.csv     # dataset usado no projeto
├── eda/
│   └── EDA_Customer_Support_Tickets.ipynb   # EDA completo (etapas 1.1 a 1.8)
├── fastapi/
│   ├── main.py                  # ponto de entrada, middlewares e tratadores de erro
│   ├── config.py                # configurações (JWT, CORS, CSP, rate limit)
│   ├── database.py              # engine e sessão do SQLModel
│   ├── sqlite_database.py       # cria e popula o database.db (sqlite3)
│   ├── database.db              # banco SQLite já populado
│   ├── requirements.txt
│   ├── models/                  # modelos Pydantic e tabelas SQLModel
│   │   ├── auth.py
│   │   ├── health.py
│   │   ├── prediction.py        # tabela prediction + entrada/saída da rota
│   │   └── user.py              # tabela user
│   ├── routes/                  # endpoints
│   │   ├── auth.py              # POST /auth/token (com rate limiting)
│   │   ├── health.py            # GET /health
│   │   ├── predict.py           # POST /predict
│   │   └── predictions.py       # GET /predictions e /predictions/{id} (ownership)
│   └── security/                # autenticação e controles de segurança
│       ├── jwt_handler.py       # geração e validação do JWT
│       ├── middleware.py        # cabeçalhos de segurança HTTP
│       ├── oauth2.py            # OAuth2PasswordBearer e dependência de autenticação
│       ├── password.py          # hash bcrypt
│       └── rate_limit.py        # configuração do SlowAPI
├── tests/
│   ├── conftest.py              # banco em memória e fixtures
│   └── test_security.py         # testes de segurança
├── zap/
│   ├── relatorio_zap.html       # relatório exportado do OWASP ZAP
│   ├── relatorio_zap.json       # o mesmo relatório em JSON
│   └── scan_passivo_zap.md      # análise dos findings Medium e High
└── others/
    ├── dfd_api.png              # diagrama de fluxo de dados
    └── analise_cia.md           # tríade CIA aplicada a cada componente
```

---

## Instalação

Pré-requisito: Python 3.10 ou superior (`python3 --version`).

```bash
# 1. Clonar o repositório
git clone <URL-DO-REPOSITORIO>
cd <NOME-DO-REPOSITORIO>

# 2. Criar e ativar o ambiente virtual
python3 -m venv .venv
source .venv/bin/activate      # Linux / macOS
# .venv\Scripts\activate       # Windows

# 3. Instalar as dependências da API
cd fastapi
pip install -r requirements.txt

# 4. Se for abrir o notebook de EDA, instalar também as dependências da análise
pip install pandas numpy matplotlib seaborn scipy jupyter
```

As dependências estão separadas de propósito: quem só quer rodar ou testar a API não precisa
instalar pandas, seaborn e companhia.

---

## Criação e população do banco de dados

O projeto já inclui o fastapi/database.db pronto para uso. Caso seja necessário recriá-lo, dentro da pasta fastapi/, execute:

python sqlite_database.py

O script apaga o banco anterior, recria as tabelas user e prediction e insere os dados iniciais, incluindo os usuários admin e analista e três predições de exemplo.

````

### Usuários criados

O sistema possui dois usuários de teste para demonstrar o controle de acesso:

admin → possui as predições 1 e 2.
analista → possui a predição 3.

A existência de dois usuários permite testar o ownership, verificando que um usuário não consegue acessar as predições do outro.

---

## Execução da API

De dentro da pasta `fastapi/`:

```bash
uvicorn main:app --reload
````

A API sobe em <http://127.0.0.1:8000> e a documentação interativa fica em
<http://127.0.0.1:8000/docs>.

### Variáveis de ambiente (todas opcionais)

O projeto utiliza variáveis de ambiente para configurar aspectos importantes da aplicação:

JWT_SECRET_KEY - chave usada para assinar os tokens.
ACCESS_TOKEN_EXPIRE_MINUTES - define a validade do token, padrão de 30 minutos.
DATABASE_URL - configura a conexão com o banco de dados.
CORS_ALLOWED_ORIGINS - define quais origens podem acessar a API.
RATE_LIMIT_LOGIN - controla o limite de tentativas de login, padrão de 10 por minuto.
TRUST_PROXY_HEADERS - permite confiar em cabeçalhos de proxy somente quando houver um proxy reverso confiável.

---

## Execução dos testes

Os testes podem ser executados a partir da raiz do projeto com:

pytest tests/ -v

O resultado esperado é de 15 testes aprovados. Eles utilizam um banco SQLite em memória, sem alterar o database.db do projeto.

Os três testes principais verificam:

Acesso sem token sendo recusado;
Usuário tentando acessar a predição de outro usuário;
Envio de campo extra no corpo sendo rejeitado com 422.

---

## Rotas da API

A API possui 5 rotas principais:

GET /health - verifica se a API está funcionando.
POST /auth/token - realiza o login e gera o JWT, com limite de 10 tentativas por minuto.
POST /predict - recebe um texto, identifica a intenção e salva a predição.
GET /predictions/ - lista apenas as predições do usuário autenticado.
GET /predictions/{id} - consulta uma predição, desde que pertença ao usuário autenticado.

### Respostas possíveis de cada rota

A API documenta os principais códigos de resposta e controles de segurança:

/health → 200 se estiver funcionando.
/auth/token → 200, 401, 422 ou 429, conforme o resultado do login.
/predict → 200 para sucesso, 401 para autenticação inválida e 422 para dados inválidos.
/predictions → 200, 401, 404 ou 422, conforme acesso e validação.

O fluxo básico é: login → receber JWT → consultar/criar predições → testar bloqueios de acesso.

Usuários inexistentes e senhas erradas retornam o mesmo 401, enquanto recursos inexistentes e de outros usuários retornam 404, evitando vazamento de informações.

---

## Controles de segurança implementados

A API possui diversos controles de segurança, incluindo:

JWT + OAuth2 para autenticação.
bcrypt para proteger as senhas.
Validação Pydantic com extra='forbid'.
SQLModel para evitar consultas SQL inseguras.
Verificação de ownership para impedir acesso indevido a dados (BOLA).
Cabeçalhos de segurança como HSTS, CSP e X-Frame-Options.
CORS configurado com allowlist de origens permitidas.
Rate limiting no login para reduzir tentativas de força bruta.

Os controles estão organizados principalmente nas pastas security/, routes/, além de main.py, config.py e database.py.

### Cabeçalhos de segurança

A API adiciona automaticamente alguns cabeçalhos de segurança para evitar problemas como XSS, clickjacking, cache de dados sensíveis e downgrade para HTTP.

Entre eles estão Strict-Transport-Security, X-Frame-Options, Content-Security-Policy, Referrer-Policy e Cache-Control.

Eles podem ser verificados com:

curl -D - -o /dev/null http://127.0.0.1:8000/health

As páginas /docs e /redoc usam uma CSP um pouco mais permissiva porque o Swagger precisa de scripts para funcionar.

Além disso, o Uvicorn adiciona o Server: uvicorn. A remoção pelo middleware não funciona, pois o cabeçalho é inserido pelo próprio servidor. Para um ambiente mais seguro, pode-se usar --no-server-header.

---

## Rate limiting: o limite escolhido e por quê

Foi adotado um limite de 10 requisições por minuto por IP no POST /auth/token para reduzir:

Força bruta e password spraying;
Sobrecarga de CPU causada pelo bcrypt;
Impactos na disponibilidade do serviço.

Com o limite, 10.000 tentativas passam de cerca de 17 minutos para aproximadamente 17 horas, tornando o ataque mais lento e detectável.

Decisões de implementação:

X-Forwarded-For só é confiável quando TRUST_PROXY_HEADERS=true.
A resposta 429 é genérica para não revelar informações úteis ao atacante.
Teste: após 10 tentativas, a 11ª retorna HTTP 429.

Limitações: o contador é mantido em memória, não funcionando de forma centralizada em múltiplas réplicas. Além disso, o limite por IP não impede ataques distribuídos; um controle por conta poderia complementar a proteção.

---

## Auditoria com OWASP ZAP

Foi realizado um scan passivo com OWASP ZAP 2.16.1, usando 57 regras em sensibilidade máxima.

High: 0
Medium: 4
Low: 2
Informational: 22
Endpoints da API: nenhum alerta Medium ou High.
Os alertas Medium/Low ficaram restritos às páginas /docs e /redoc.

As análises e correções estão em zap/scan_passivo_zap.md, e o relatório completo em zap/relatorio_zap.html.

---

## EDA

O notebook eda/EDA_Customer_Support_Tickets.ipynb já está executado e contém gráficos e resultados das 8 etapas: compreensão, inspeção, qualidade, limpeza, análise univariada e multivariada, outliers/anomalias e conclusões. Pode ser executado novamente com Jupyter após instalar as dependências.

---

## Modelagem de ameaças

O DFD está em others/dfd_api.png, identificando 3 fronteiras de confiança: internet, servidor da API e zona autenticada. A análise da tríade CIA (Confidencialidade, Integridade e Disponibilidade) dos 8 componentes está em others/analise_cia.md.
