"""Autenticação de usuários contra o banco de dados."""

from sqlmodel import Session, select

from models.user import User
from security.password import gerar_hash_de_senha, verificar_senha

# Hash descartável usado apenas para igualar o tempo de resposta quando o
# usuário não existe (ver ``autenticar_usuario``).
_HASH_FICTICIO = gerar_hash_de_senha("hash-ficticio-para-tempo-constante")


def autenticar_usuario(sessao: Session, username: str, senha: str) -> User | None:
    """Valida as credenciais e devolve o usuário, ou ``None`` se inválidas."""

    # Query do usuário
    usuario = sessao.exec(select(User).where(User.username == username)).first()

    if usuario is None:
        verificar_senha(senha, _HASH_FICTICIO)
        return None

    if not usuario.ativo:
        verificar_senha(senha, _HASH_FICTICIO)
        return None

    if not verificar_senha(senha, usuario.hashed_password):
        return None

    return usuario
