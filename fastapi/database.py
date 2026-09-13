"""Camada de acesso a dados com SQLModel."""

from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine, select

from config import DATABASE_URL

# Argumentos para SQLite
_argumentos_de_conexao = (
    {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

engine = create_engine(DATABASE_URL, echo=False, connect_args=_argumentos_de_conexao)


def criar_tabelas() -> None:
    """Cria as tabelas do banco a partir dos modelos SQLModel registrados."""

    # Imports locais para evitar dependência circular
    from models.ticket import Ticket  # noqa: F401
    from models.user import User  # noqa: F401

    SQLModel.metadata.create_all(engine)


def obter_sessao() -> Generator[Session, None, None]:
    """Dependência do FastAPI que fornece uma sessão de banco por requisição."""

    with Session(engine) as sessao:
        yield sessao


def popular_dados_iniciais() -> None:
    """Cria os usuários e chamados de exemplo, se o banco estiver vazio."""

    from models.ticket import Ticket
    from models.user import User
    from security.password import gerar_hash_de_senha

    with Session(engine) as sessao:
        if sessao.exec(select(User)).first() is not None:
            return  # Banco já populado: nada a fazer.

        admin = User(
            username="admin",
            hashed_password=gerar_hash_de_senha("admin123"),
            role="admin",
        )
        ana = User(
            username="ana",
            hashed_password=gerar_hash_de_senha("ana12345"),
            role="user",
        )
        bruno = User(
            username="bruno",
            hashed_password=gerar_hash_de_senha("bruno12345"),
            role="user",
        )

        sessao.add_all([admin, ana, bruno])
        sessao.commit()
        for usuario in (admin, ana, bruno):
            sessao.refresh(usuario)

        sessao.add_all(
            [
                Ticket(
                    titulo="Produto não liga após a última atualização",
                    descricao=(
                        "Depois da atualização de firmware o aparelho não liga mais. "
                        "Já tentei reiniciar segurando o botão por 30 segundos."
                    ),
                    intencao_prevista="Technical issue",
                    owner_id=ana.id,
                ),
                Ticket(
                    titulo="Cobrança duplicada na fatura de março",
                    descricao=(
                        "Fui cobrado duas vezes pelo mesmo pedido na fatura de março "
                        "e gostaria do estorno de uma das cobranças."
                    ),
                    intencao_prevista="Billing inquiry",
                    owner_id=ana.id,
                ),
                Ticket(
                    titulo="Solicitação de cancelamento da assinatura",
                    descricao=(
                        "Gostaria de cancelar a assinatura anual a partir do próximo "
                        "ciclo de faturamento."
                    ),
                    intencao_prevista="Cancellation request",
                    owner_id=bruno.id,
                ),
            ]
        )
        sessao.commit()
