"""Conexão com o banco pela ótica da API. """

from collections.abc import Generator

from sqlmodel import Session, create_engine

from config import DATABASE_URL


engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)


def pegar_sessao() -> Generator[Session, None, None]:
    with Session(engine) as sessao:
        yield sessao
