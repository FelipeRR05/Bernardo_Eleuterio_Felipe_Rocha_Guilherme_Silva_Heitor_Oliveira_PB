"""Tabela de predictions e os modelos de entrada/saída dessa rota."""

from datetime import datetime, timezone

from pydantic import ConfigDict
from sqlmodel import Field, SQLModel


def _agora() -> datetime:
    return datetime.now(timezone.utc)


class Prediction(SQLModel, table=True):
    """Uma predição salva no banco, pertencente a um usuário."""

    id: int | None = Field(default=None, primary_key=True)
    texto: str = Field(max_length=5000)
    intencao: str = Field(max_length=50)
    criado_em: datetime = Field(default_factory=_agora)

    # Chave estrangeira para a tabela de usuários. É o dono do registro.
    owner_id: int = Field(foreign_key="user.id", index=True)


class PredictionRequest(SQLModel):
    """Corpo da requisição de POST /predict."""

    model_config = ConfigDict(extra="forbid")

    texto: str = Field(min_length=1, max_length=5000)


class PredictionResponse(SQLModel):
    """O que a API devolve quando uma predição é criada ou consultada."""

    id: int
    texto: str
    intencao: str
    criado_em: datetime
    owner_id: int
