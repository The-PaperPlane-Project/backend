from fastapi import APIRouter, Depends
from src.dependencies import get_ticket_service
from src.schemas.ticket import TicketCreate, TicketResponse
from src.services.ticket import TicketService

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("/", response_model=TicketResponse)
def book_ticket(data: TicketCreate, service: TicketService = Depends(get_ticket_service)):
    return service.book_ticket(data)


@router.get("/user/{user_id}", response_model=list[TicketResponse])
def user_tickets(user_id: int, service: TicketService = Depends(get_ticket_service)):
    return service.get_tickets_for_user(user_id)


@router.delete("/{ticket_id}")
def cancel_ticket(ticket_id: str, service: TicketService = Depends(get_ticket_service)):
    return service.cancel_ticket(ticket_id)
