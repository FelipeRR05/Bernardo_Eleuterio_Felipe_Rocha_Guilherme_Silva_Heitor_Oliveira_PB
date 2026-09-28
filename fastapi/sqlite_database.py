"""Cria e popula o banco SQLite usado pela API.

    python sqlite_database.py
"""

import sqlite3
from pathlib import Path

from security.password import gerar_hash_de_senha

CAMINHO_DO_BANCO = Path(__file__).resolve().parent / "database.db"


CRIAR_TABELA_USER = """
CREATE TABLE user (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        VARCHAR(50)  NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL
)
"""

CRIAR_TABELA_PREDICTION = """
CREATE TABLE prediction (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    texto      VARCHAR(5000) NOT NULL,
    intencao   VARCHAR(50)   NOT NULL,
    criado_em  TIMESTAMP     NOT NULL,
    owner_id   INTEGER       NOT NULL,
    FOREIGN KEY (owner_id) REFERENCES user (id)
)
"""

CRIAR_INDICE_USERNAME = "CREATE UNIQUE INDEX ix_user_username ON user (username)"
CRIAR_INDICE_OWNER = "CREATE INDEX ix_prediction_owner_id ON prediction (owner_id)"


USUARIOS = [
    ("admin", "admin123"),
    ("analista", "analista123"),
]

# Predições divididas entre os dois usuários. A 1 e a 2 são do admin, a 3 é do
# analista - é essa separação que os testes de BOLA usam.
PREDICOES = [
    (
        "Meu produto parou de funcionar depois da última atualização.",
        "Technical issue",
        "admin",
    ),
    (
        "Fui cobrado duas vezes na fatura deste mês e queria entender o motivo.",
        "Billing inquiry",
        "admin",
    ),
    (
        "Gostaria de cancelar minha assinatura a partir do próximo ciclo.",
        "Cancellation request",
        "analista",
    ),
]


def criar_banco() -> None:
    """Apaga o banco anterior, recria o schema e insere os dados iniciais."""

    if CAMINHO_DO_BANCO.exists():
        CAMINHO_DO_BANCO.unlink()
        print(f"Banco anterior removido: {CAMINHO_DO_BANCO.name}")

    conexao = sqlite3.connect(CAMINHO_DO_BANCO)
    cursor = conexao.cursor()

    try:
        # O SQLite não valida chave estrangeira por padrão; precisa ligar.
        cursor.execute("PRAGMA foreign_keys = ON")

        cursor.execute(CRIAR_TABELA_USER)
        cursor.execute(CRIAR_TABELA_PREDICTION)
        cursor.execute(CRIAR_INDICE_USERNAME)
        cursor.execute(CRIAR_INDICE_OWNER)
        print("Tabelas 'user' e 'prediction' criadas.")

        ids_por_usuario: dict[str, int] = {}
        for username, senha in USUARIOS:
            cursor.execute(
                "INSERT INTO user (username, hashed_password) VALUES (?, ?)",
                (username, gerar_hash_de_senha(senha)),
            )
            ids_por_usuario[username] = cursor.lastrowid
            print(f"Usuário criado: {username} (id={cursor.lastrowid})")

        for texto, intencao, dono in PREDICOES:
            cursor.execute(
                """
                INSERT INTO prediction (texto, intencao, criado_em, owner_id)
                VALUES (?, ?, datetime('now'), ?)
                """,
                (texto, intencao, ids_por_usuario[dono]),
            )
            print(f"Predição {cursor.lastrowid} criada para '{dono}'")

        conexao.commit()

    finally:
        conexao.close()

    print(f"\nBanco pronto em: {CAMINHO_DO_BANCO}")


if __name__ == "__main__":
    criar_banco()
