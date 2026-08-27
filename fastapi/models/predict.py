from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    """A rota POST /predict valida os dados de entrada e simula a resposta de um futuro modelo de classificação de intenção."""

    text: str = Field(
        min_length=1,
        description="Texto do chamado/mensagem do cliente a ser classificado.",
        examples=["Meu produto parou de funcionar depois da última atualização."],
    )


class PredictResponse(BaseModel):

    text: str
    intent: str
    message: str
