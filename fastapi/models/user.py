"""Modelo de usuário (tabela SQLModel) e schemas de entrada/saída."""

from pydantic import ConfigDict
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """Usuário da API, persistido no banco."""

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, max_length=50)
    hashed_password: str = Field(max_length=255)
    role: str = Field(default="user", max_length=20)
    ativo: bool = Field(default=True)


class UserPublic(SQLModel):
    """Representação pública de um usuário (sem hash de senha)."""

    id: int
    username: str
    role: str


class UserCreate(SQLModel):
    """Entrada para criação de usuário."""

    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)
