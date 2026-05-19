from typing import Optional
from sqlalchemy.orm import Session
from src.models.ticket import Ticket
from src.repositories.base import BaseRepository


class TicketRepository(BaseRepository[Ticket]):
    def __init__(self, db: Session):
        super().__init__(Ticket, db)

    def get_by_flight_seat(self, flight_id: int, seat_number: str | None = None, seat_id: int | None = None) -> Optional[Ticket]:
        query = self.db.query(Ticket).filter(Ticket.flight_id == flight_id)
        if seat_id is not None:
            query = query.filter(Ticket.seat_id == seat_id)
        if seat_number is not None:
            query = query.filter(Ticket.seat_number == seat_number)
        return query.first()

    def get_by_flight_passenger(self, flight_id: int, passenger_id: str) -> Optional[Ticket]:
        return self.db.query(Ticket).filter(
            Ticket.flight_id == flight_id,
            Ticket.passenger_id == passenger_id,
        ).first()

    def get_by_user(self, user_id: int) -> list[Ticket]:
        return self.db.query(Ticket).filter(Ticket.user_id == user_id).all()
