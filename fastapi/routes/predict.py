"""Rota de predição de intenção."""

from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from database import pegar_sessao
from models.prediction import Prediction, PredictionRequest, PredictionResponse
from models.user import User
from security.oauth2 import usuario_autenticado

router = APIRouter(tags=["predict"])

INTENCAO_SIMULADA = "Technical issue"


@router.post(
    "/predict",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Classifica a intenção de um texto (resposta simulada)",
    responses={
        200: {"description": "Predição gerada e salva como pertencente ao usuário."},
        401: {"description": "Token ausente, inválido ou expirado."},
        422: {
            "description": (
                "Corpo inválido: texto vazio, acima de 5000 caracteres, ou com "
                "algum campo extra que não faz parte do modelo (extra='forbid')."
            )
        },
    },
)
def prever(
    dados: PredictionRequest,
    usuario: User = Depends(usuario_autenticado),
    sessao: Session = Depends(pegar_sessao),
) -> Prediction:
    """Recebe um texto, devolve a intenção e guarda a predição."""

    predicao = Prediction(
        texto=dados.texto,
        intencao=INTENCAO_SIMULADA,
        owner_id=usuario.id,
    )

    sessao.add(predicao)
    sessao.commit()
    sessao.refresh(predicao)

    return predicao
