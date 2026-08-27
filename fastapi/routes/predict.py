from fastapi import APIRouter, Depends

from models.predict import PredictRequest, PredictResponse
from security.oauth2 import get_current_user

router = APIRouter(tags=["predict"])

INTENCAO_PRE_DETERMINADA = "Technical issue"

@router.post("/predict", response_model=PredictResponse, summary="Classifica a intenção de um texto (simulado)")
def predict(
    request: PredictRequest,
    current_user: str = Depends(get_current_user),
) -> PredictResponse:
    """Rota protegida por JWT que recebe um texto e retorna uma intenção pré-determinada."""

    return PredictResponse(
        text=request.text,
        intent=INTENCAO_PRE_DETERMINADA,
        message=(
            "Resposta simulada: o modelo de classificação de intenção ainda "
            "não foi implementado nesta etapa do projeto de bloco."
        ),
    )
