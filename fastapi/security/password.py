"""Hashing e verificação de senhas com bcrypt."""

import bcrypt

# bcrypt trunca silenciosamente entradas acima de 72 bytes; validamos antes para
# que uma senha longa não seja aceita com apenas o seu prefixo verificado.
LIMITE_BYTES_BCRYPT = 72


def gerar_hash_de_senha(senha: str) -> str:
    """Gera o hash bcrypt de uma senha em texto puro."""

    senha_em_bytes = senha.encode("utf-8")[:LIMITE_BYTES_BCRYPT]
    return bcrypt.hashpw(senha_em_bytes, bcrypt.gensalt()).decode("utf-8")


def verificar_senha(senha: str, hash_armazenado: str) -> bool:
    """Compara uma senha em texto puro com o hash bcrypt armazenado.

    ``bcrypt.checkpw`` faz a comparação em tempo constante, evitando *timing
    attacks* que poderiam revelar quantos caracteres iniciais estão corretos.
    """

    try:
        return bcrypt.checkpw(
            senha.encode("utf-8")[:LIMITE_BYTES_BCRYPT],
            hash_armazenado.encode("utf-8"),
        )
    except ValueError:
        # Hash malformado no banco: tratamos como falha de autenticação.
        return False
