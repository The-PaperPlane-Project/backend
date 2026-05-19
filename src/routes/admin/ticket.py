from fastapi import APIRouter, Depends
from src.dependencies import get_current_admin, get_ticket_service
from src.schemas.ticket import TicketResponse
from src.services.ticket import TicketService

router = APIRouter(prefix="/admin/tickets", tags=["admin-tickets"])


@router.get("/", response_model=list[TicketResponse])
def all_tickets(service: TicketService = Depends(get_ticket_service), admin=Depends(get_current_admin)):
    return service.get_all_tickets()
