"""Hash e verificação de senha com bcrypt. """

import bcrypt

LIMITE_DE_BYTES = 72


def gerar_hash_de_senha(senha: str) -> str:
   

    return bcrypt.hashpw(
        senha.encode("utf-8")[:LIMITE_DE_BYTES], bcrypt.gensalt()
    ).decode("utf-8")


def senha_confere(senha: str, hash_guardado: str) -> bool:
   

    try:
        return bcrypt.checkpw(
            senha.encode("utf-8")[:LIMITE_DE_BYTES], hash_guardado.encode("utf-8")
        )
    except ValueError:

        return False
