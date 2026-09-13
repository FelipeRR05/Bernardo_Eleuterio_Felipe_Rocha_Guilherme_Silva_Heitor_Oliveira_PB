from fastapi import APIRouter, Depends

from models.predict import PredictRequest, PredictResponse
from models.user import User
from security.oauth2 import obter_usuario_atual

router = APIRouter(tags=["predict"])

INTENCAO_PRE_DETERMINADA = "Technical issue"


@router.post(
    "/predict",
    response_model=PredictResponse,
    summary="Classifica a intenção de um texto (simulado)",
)
def predict(
    request: PredictRequest,
    usuario: User = Depends(obter_usuario_atual),
) -> PredictResponse:
    """Rota protegida por JWT que recebe um texto e devolve uma intenção simulada."""

    return PredictResponse(
        text=request.text,
        intent=INTENCAO_PRE_DETERMINADA,
        message=(
            "Resposta simulada: o modelo de classificação de intenção ainda não "
            "foi implementado. Ver a seção 'Próximos passos' do relatório de EDA."
        ),
    )
