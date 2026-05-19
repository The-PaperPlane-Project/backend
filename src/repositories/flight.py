from sqlalchemy.orm import Session
from src.models.flight import Flight
from src.repositories.base import BaseRepository


class FlightRepository(BaseRepository[Flight]):
    def __init__(self, db: Session):
        super().__init__(Flight, db)

    def get_by_number(self, flight_number: str) -> Flight | None:
        return self.db.query(Flight).filter(Flight.flight_number == flight_number).first()
