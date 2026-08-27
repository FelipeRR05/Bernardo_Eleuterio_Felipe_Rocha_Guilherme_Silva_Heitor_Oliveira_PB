"""Cadastro do usuário administrador da API.

Conforme pedido no enunciado da Etapa 1, o login e a senha do usuário
admin (o único com acesso à API) são definidos diretamente no código-fonte
("in-code"), sem cadastro dinâmico de novos usuários.

A senha não é guardada em texto puro: é armazenada como um hash bcrypt e
comparada com `passlib`, então mesmo quem tiver acesso a este arquivo não
vê a senha original diretamente.

Usuário: admin
Senha:   admin123
"""

import bcrypt

ADMIN_USERNAME = "admin"

# Hash bcrypt da senha "admin123", gerado uma única vez na inicialização.
# (equivalente a bcrypt.hashpw(b"admin123", bcrypt.gensalt()))
ADMIN_PASSWORD_HASH = bcrypt.hashpw(b"admin123", bcrypt.gensalt())


def authenticate_user(username: str, password: str) -> bool:
    """Valida usuário e senha contra o único usuário admin cadastrado."""

    if username != ADMIN_USERNAME:
        return False
    return bcrypt.checkpw(password.encode("utf-8"), ADMIN_PASSWORD_HASH)
