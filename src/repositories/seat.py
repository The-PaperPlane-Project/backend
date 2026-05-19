from typing import List
from sqlalchemy.orm import Session, joinedload
from src.models.seat import Seat
from src.models.ticket import Ticket
from src.repositories.base import BaseRepository


class SeatRepository(BaseRepository[Seat]):
    def __init__(self, db: Session):
        super().__init__(Seat, db)

    def bulk_create(self, seats: List[Seat]) -> List[Seat]:
        self.db.add_all(seats)
        self.db.commit()
        return seats

    def get_by_airplane(self, airplane_id: int) -> List[Seat]:
        return (
            self.db.query(Seat)
            .options(joinedload(Seat.cabin_class))
            .filter(Seat.airplane_id == airplane_id)
            .order_by(Seat.seat_number)
            .all()
        )

    def get_available_for_flight(self, airplane_id: int, flight_id: int) -> List[Seat]:
        booked_seat_ids = (
            self.db.query(Ticket.seat_id)
            .filter(Ticket.flight_id == flight_id, Ticket.seat_id.is_not(None))
            .subquery()
        )
        return (
            self.db.query(Seat)
            .filter(Seat.airplane_id == airplane_id, ~Seat.id.in_(booked_seat_ids))
            .order_by(Seat.seat_number)
            .all()
        )

    def get_by_airplane_and_number(self, airplane_id: int, seat_number: str) -> Seat | None:
        return self.db.query(Seat).filter(
            Seat.airplane_id == airplane_id,
            Seat.seat_number == seat_number,
        ).first()
