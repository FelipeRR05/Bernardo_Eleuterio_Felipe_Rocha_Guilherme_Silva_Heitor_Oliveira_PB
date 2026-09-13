"""Modelo de chamado (ticket) e seus schemas de entrada/saída."""

from datetime import datetime, timezone

from pydantic import ConfigDict
from sqlmodel import Field, SQLModel


def _agora_utc() -> datetime:
    return datetime.now(timezone.utc)


class Ticket(SQLModel, table=True):
    """Chamado de suporte, persistido no banco."""

    id: int | None = Field(default=None, primary_key=True)
    titulo: str = Field(max_length=150)
    descricao: str = Field(max_length=5000)
    intencao_prevista: str | None = Field(default=None, max_length=50)
    criado_em: datetime = Field(default_factory=_agora_utc)
    owner_id: int = Field(foreign_key="user.id", index=True)


class TicketCreate(SQLModel):
    """Entrada para criação de chamado."""

    model_config = ConfigDict(extra="forbid")

    titulo: str = Field(min_length=3, max_length=150)
    descricao: str = Field(min_length=1, max_length=5000)


class TicketUpdate(SQLModel):
    """Entrada para atualização de chamado (todos os campos opcionais)."""

    model_config = ConfigDict(extra="forbid")

    titulo: str | None = Field(default=None, min_length=3, max_length=150)
    descricao: str | None = Field(default=None, min_length=1, max_length=5000)


class TicketPublic(SQLModel):
    """Representação pública de um chamado devolvida pela API."""

    id: int
    titulo: str
    descricao: str
    intencao_prevista: str | None
    criado_em: datetime
    owner_id: int
