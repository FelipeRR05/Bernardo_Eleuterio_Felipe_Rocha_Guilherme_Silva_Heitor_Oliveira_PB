from pydantic import BaseModel, ConfigDict, Field


class PredictRequest(BaseModel):
    """Entrada da rota POST /predict."""

    model_config = ConfigDict(extra="forbid")

    text: str = Field(
        min_length=1,
        max_length=5000,
        description="Texto do chamado/mensagem do cliente a ser classificado.",
        examples=["Meu produto parou de funcionar depois da última atualização."],
    )


class PredictResponse(BaseModel):
    """Resposta da rota POST /predict."""

    text: str
    intent: str
    message: str
