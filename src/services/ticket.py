from datetime import datetime
from fastapi import HTTPException
from src.models.passenger import Passenger
from src.models.ticket import Ticket
from src.models.user import User
from src.repositories.flight import FlightRepository
from src.repositories.seat import SeatRepository
from src.repositories.ticket import TicketRepository
from src.services.email import BookingEmailService
from src.schemas.ticket import TicketCreate, TicketResponse


class TicketService:
    def __init__(
        self,
        ticket_repo: TicketRepository,
        seat_repo: SeatRepository,
        flight_repo: FlightRepository,
        email_service: BookingEmailService | None = None,
    ):
        self.ticket_repo = ticket_repo
        self.seat_repo = seat_repo
        self.flight_repo = flight_repo
        self.email_service = email_service or BookingEmailService()

    def book_ticket(self, data: TicketCreate) -> TicketResponse:
        flight = self.flight_repo.get(data.flight_id)
        if not flight:
            raise HTTPException(status_code=404, detail="Flight not found")

        if data.user_id is not None:
            user = self.ticket_repo.db.query(User).filter(User.id == data.user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

        passenger = None
        if data.passenger_id:
            passenger = self.ticket_repo.db.query(Passenger).filter(Passenger.id == data.passenger_id).first()
            if not passenger:
                raise HTTPException(status_code=404, detail="Passenger not found")
            if data.user_id is not None and passenger.user_id is not None and passenger.user_id != data.user_id:
                raise HTTPException(status_code=400, detail="Passenger does not belong to the selected user")
            if self.ticket_repo.get_by_flight_passenger(data.flight_id, data.passenger_id):
                raise HTTPException(status_code=400, detail="Passenger already has a ticket for this flight")
        else:
            raise HTTPException(status_code=400, detail="Passenger is required for booking")

        seat = None
        seat_number = data.seat_number.strip().upper() if data.seat_number else None
        if data.seat_id is not None:
            seat = self.seat_repo.get(data.seat_id)
            if not seat:
                raise HTTPException(status_code=404, detail="Seat not found")
            if seat.airplane_id != flight.airplane_id:
                raise HTTPException(status_code=400, detail="Seat does not belong to the flight airplane")
            seat_number = seat.seat_number
        elif seat_number:
            seat = self.seat_repo.get_by_airplane_and_number(flight.airplane_id, seat_number)
            if not seat:
                raise HTTPException(status_code=404, detail="Seat not found for this flight")
        else:
            raise HTTPException(status_code=400, detail="Seat is required for booking")

        if self.ticket_repo.get_by_flight_seat(data.flight_id, seat_number=seat_number):
            raise HTTPException(status_code=400, detail="Seat already booked for this flight")

        ticket_id = data.id or f"{data.flight_id}-{data.passenger_id}-{seat_number}"
        if self.ticket_repo.get(ticket_id):
            raise HTTPException(status_code=400, detail="Ticket with this id already exists")

        ticket = Ticket(
            id=ticket_id,
            user_id=data.user_id,
            passenger_id=data.passenger_id,
            flight_id=data.flight_id,
            seat_id=seat.id,
            seat_number=seat_number,
            cabin_class=data.cabin_class or seat.cabin_class_type,
            price=data.price,
            created_at=data.created_at or datetime.utcnow().isoformat(),
            is_used=data.is_used,
        )
        created_ticket = self.ticket_repo.create(ticket)
        self.email_service.send_booking_confirmation(created_ticket)
        return TicketResponse.model_validate(created_ticket)

    def cancel_ticket(self, ticket_id: str) -> dict[str, str]:
        ticket = self.ticket_repo.get(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        if ticket.is_used:
            raise HTTPException(status_code=400, detail="Ticket already used")

        flight = ticket.flight or self.flight_repo.get(ticket.flight_id)
        if not flight:
            raise HTTPException(status_code=404, detail="Flight not found")
        if flight.status is not None:
            raise HTTPException(status_code=400, detail="Ticket cancellation unavailable for current flight status")

        self.ticket_repo.delete(ticket_id)
        return {"status": "ok"}

    def send_ticket_to_email(self, ticket_id: str, current_user: User) -> dict[str, str]:
        ticket = self.ticket_repo.get(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        if ticket.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Ticket does not belong to current user")
        if not current_user.email:
            raise HTTPException(status_code=400, detail="User email is not specified")

        self.email_service.send_ticket_pdf(ticket, current_user.email)
        return {"status": "ok"}

    def get_tickets_for_user(self, user_id: int) -> list[TicketResponse]:
        return [TicketResponse.model_validate(t) for t in self.ticket_repo.get_by_user(user_id)]

    def get_all_tickets(self) -> list[TicketResponse]:
        return [TicketResponse.model_validate(t) for t in self.ticket_repo.get_all()]
