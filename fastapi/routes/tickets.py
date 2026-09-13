"""Rotas de chamados (tickets)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from database import obter_sessao
from models.ticket import Ticket, TicketCreate, TicketPublic, TicketUpdate
from models.user import User
from security.oauth2 import obter_usuario_atual

router = APIRouter(prefix="/tickets", tags=["tickets"])


def _buscar_ticket_do_usuario(
    ticket_id: int,
    usuario: User,
    sessao: Session,
) -> Ticket:
    """Busca um chamado garantindo que o usuário tem direito de acessá-lo."""
    ticket = sessao.exec(select(Ticket).where(Ticket.id == ticket_id)).first()

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chamado não encontrado",
        )

    if usuario.role != "admin" and ticket.owner_id != usuario.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chamado não encontrado",
        )

    return ticket


@router.get(
    "/",
    response_model=list[TicketPublic],
    summary="Lista os chamados do usuário autenticado",
)
def listar_tickets(
    usuario: User = Depends(obter_usuario_atual),
    sessao: Session = Depends(obter_sessao),
) -> list[Ticket]:
    """Devolve apenas os chamados do próprio usuário."""
    if usuario.role == "admin":
        return list(sessao.exec(select(Ticket)).all())

    return list(
        sessao.exec(select(Ticket).where(Ticket.owner_id == usuario.id)).all()
    )


@router.post(
    "/",
    response_model=TicketPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um chamado para o usuário autenticado",
)
def criar_ticket(
    dados: TicketCreate,
    usuario: User = Depends(obter_usuario_atual),
    sessao: Session = Depends(obter_sessao),
) -> Ticket:
    """Cria um chamado."""
    ticket = Ticket(
        titulo=dados.titulo,
        descricao=dados.descricao,
        owner_id=usuario.id,
    )

    sessao.add(ticket)
    sessao.commit()
    sessao.refresh(ticket)

    return ticket


@router.get(
    "/{ticket_id}",
    response_model=TicketPublic,
    summary="Obtém um chamado por ID (com verificação de ownership)",
)
def obter_ticket(
    ticket_id: int,
    usuario: User = Depends(obter_usuario_atual),
    sessao: Session = Depends(obter_sessao),
) -> Ticket:
    """Devolve um chamado específico, se ele pertencer ao usuário autenticado."""
    return _buscar_ticket_do_usuario(ticket_id, usuario, sessao)


@router.put(
    "/{ticket_id}",
    response_model=TicketPublic,
    summary="Atualiza um chamado por ID (com verificação de ownership)",
)
def atualizar_ticket(
    ticket_id: int,
    dados: TicketUpdate,
    usuario: User = Depends(obter_usuario_atual),
    sessao: Session = Depends(obter_sessao),
) -> Ticket:
    """Atualiza um chamado do próprio usuário."""
    ticket = _buscar_ticket_do_usuario(ticket_id, usuario, sessao)

    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(ticket, campo, valor)

    sessao.add(ticket)
    sessao.commit()
    sessao.refresh(ticket)

    return ticket


@router.delete(
    "/{ticket_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove um chamado por ID (com verificação de ownership)",
)
def remover_ticket(
    ticket_id: int,
    usuario: User = Depends(obter_usuario_atual),
    sessao: Session = Depends(obter_sessao),
) -> None:
    """Remove um chamado do próprio usuário."""
    ticket = _buscar_ticket_do_usuario(ticket_id, usuario, sessao)

    sessao.delete(ticket)
    sessao.commit()
