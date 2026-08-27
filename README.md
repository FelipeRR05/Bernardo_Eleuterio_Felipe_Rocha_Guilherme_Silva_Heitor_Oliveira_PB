# Projeto de Bloco - Análise e Segurança de Agentes de IA - Etapa 1

**Disciplina:** Análise e Segurança de Agentes de IA - Instituto Infnet

**Professor:** Tiago Cariolano de Souza Xavier

**Grupo:** Bernardo de Moraes Eleuterio, Felipe Roberto Rocha, Guilherme Valentim Ramalho da Silva e Heitor Cella Oliveira

## Objetivo do projeto

Este repositório contém a **Etapa 1 (TP1)** do Projeto de Bloco, cujo objetivo final (ao longo do bloco) é construir um sistema de atendimento ao cliente alimentado por inteligência artificial. Nesta primeira etapa, o trabalho consiste em:

1. Escolher e documentar o dataset que servirá de base para o projeto - o [Customer Support Ticket Dataset](https://www.kaggle.com/datasets/suraj520/customer-support-ticket-dataset), que contém o texto de chamados de suporte (Ticket Description) e a intenção/categoria de cada chamado (Ticket Type).
2. Realizar a Análise Exploratória de Dados (EDA) inicial desse dataset (compreensão do problema, inspeção, verificação de qualidade, limpeza e análise univariada), levantando hipóteses sobre as intenções dos usuários.
3. Configurar a estrutura base de uma API FastAPI, modular e com autenticação JWT funcional, que servirá de esqueleto para o sistema de atendimento (o modelo de Machine Learning propriamente dito será integrado em etapas futuras).
4. Modelar a segurança da API com um Diagrama de Fluxo de Dados (DFD) e uma análise da tríade CIA (Confidencialidade, Integridade, Disponibilidade).

## Estrutura de pastas

```
.
├── README.md
├── data/
│   └── customer_support_tickets.csv
├── eda/
│   └── EDA_Customer_Support_Tickets.ipynb
├── fastapi/
│   ├── main.py
│   ├── requirements.txt
│   ├── routes/
│   │   ├── health.py
│   │   ├── auth.py
│   │   └── predict.py
│   ├── models/
│   │   ├── health.py
│   │   ├── auth.py
│   │   └── predict.py
│   ├── security/
│   │   ├── users.py
│   │   ├── jwt_handler.py
│   │   └── oauth2.py
│   └── tests/
│       └── test_api.py
└── others/
    └── dfd_api.png
```

## Instruções de instalação

Pré-requisitos: Python 3.10+ instalado (python3 --version).

1. Clone o repositório:

   git clone <URL-DO-REPOSITORIO>
   cd <NOME-DO-REPOSITORIO>

2. Crie e ative um ambiente virtual:

   python3 -m venv .venv
   source .venv/bin/activate  
   .venv\Scripts\activate

3. Instale as dependências da API:

   cd fastapi
   pip install -r requirements.txt

## Instruções de execução

### Rodando a API

Dentro da pasta fastapi/, com as dependências já instaladas:

uvicorn main:app --reload

A API sobe por padrão em http://127.0.0.1:8000. A documentação interativa (Swagger) fica disponível em:

http://127.0.0.1:8000/docs

### Testando as rotas manualmente

1. Health check (rota pública):

   curl http://127.0.0.1:8000/health

2. Login (usuário admin definido em security/users.py: usuário admin, senha admin123):

   curl -X POST http://127.0.0.1:8000/auth/token \
    -d "username=admin&password=admin123"

   A resposta traz o access_token (JWT) a ser usado nas rotas protegidas.

3. Predição de intenção (rota protegida - requer o token obtido acima):

   curl -X POST http://127.0.0.1:8000/predict \
    -H "Authorization: Bearer <TOKEN_OBTIDO_NO_PASSO_ANTERIOR>" \
    -H "Content-Type: application/json" \
    -d '{"text": "Meu produto parou de funcionar."}'

   Sem o header Authorization (ou com um token inválido/expirado), a rota responde 401 Unauthorized.

### Rodando os testes automatizados

Dentro da pasta fastapi/:

pip install -r requirements.txt
pytest -v

Os testes cobrem as 3 rotas exigidas, incluindo o comportamento de autenticação (401 sem token / com token inválido e 200 com token válido).

### Abrindo o notebook de EDA

O notebook eda/EDA_Customer_Support_Tickets.ipynb já foi executado e possui os gráficos e resultados da análise. Para abrir ou executar novamente, basta instalar as dependências e iniciar o Jupyter.

O notebook utiliza o dataset localizado em ../data/customer_support_tickets.csv, então é importante executá-lo a partir da pasta eda/, mantendo a estrutura original do projeto.

## Escopo desta entrega

Nesta primeira etapa, o projeto conta com a documentação e a análise inicial do dataset, além da estrutura básica da API FastAPI com autenticação JWT. As partes de Machine Learning, agente de IA e os controles OWASP/pentest serão desenvolvidas nas próximas etapas.

Para testar a API, entre na pasta fastapi/, instale as dependências com pip install -r requirements.txt e execute pytest -v. Os testes verificam as 3 rotas exigidas e também confirmam o funcionamento da autenticação, considerando casos com token ausente, inválido e válido.

### Abrindo o notebook de EDA

O notebook de EDA já foi executado, com gráficos e resultados. Para abrir ou executar novamente, basta instalar as dependências e rodar o Jupyter/Colab.

## Segurança - DFD e CIA

O diagrama de fluxo de dados e a análise da tríade CIA aplicada aos componentes da API estão em others/dfd_api.png e others/CIA_analysis.md.

## Escopo desta entrega

A Etapa 1 inclui a EDA do dataset e a estrutura básica da API FastAPI com JWT. O modelo de ML, agente de IA e testes OWASP ficam para etapas futuras.
