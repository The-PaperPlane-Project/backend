from fastapi import APIRouter, Depends
from src.dependencies import get_current_user, get_ticket_service
from src.models.user import User
from src.schemas.ticket import TicketCreate, TicketResponse
from src.services.ticket import TicketService

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("/", response_model=TicketResponse)
def book_ticket(data: TicketCreate, service: TicketService = Depends(get_ticket_service)):
    return service.book_ticket(data)


@router.get("/user/{user_id}", response_model=list[TicketResponse])
def user_tickets(user_id: int, service: TicketService = Depends(get_ticket_service)):
    return service.get_tickets_for_user(user_id)


@router.post("/{ticket_id}/email")
def email_ticket(
    ticket_id: str,
    service: TicketService = Depends(get_ticket_service),
    current_user: User = Depends(get_current_user),
):
    return service.send_ticket_to_email(ticket_id, current_user)


@router.delete("/{ticket_id}")
def cancel_ticket(ticket_id: str, service: TicketService = Depends(get_ticket_service)):
    return service.cancel_ticket(ticket_id)
