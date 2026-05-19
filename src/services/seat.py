from fastapi import HTTPException
from src.models.airplane import Airplane
from src.models.seat import Seat
from src.repositories.seat import SeatRepository
from src.schemas.seat import SeatCreate, SeatResponse


class SeatService:
    def __init__(self, seat_repo: SeatRepository):
        self.seat_repo = seat_repo

    def create_seat(self, data: SeatCreate) -> SeatResponse:
        airplane = self.seat_repo.db.query(Airplane).filter(Airplane.id == data.airplane_id).first()
        if not airplane:
            raise HTTPException(status_code=404, detail="Airplane not found")
        seat_number = data.seat_number.strip().upper()
        if self.seat_repo.get_by_airplane_and_number(data.airplane_id, seat_number):
            raise HTTPException(status_code=400, detail="Seat already exists for this airplane")
        payload = data.model_dump(by_alias=False)
        payload["seat_number"] = seat_number
        seat = Seat(**payload)
        return SeatResponse.model_validate(self.seat_repo.create(seat))

    def get_available_seats(self, airplane_id: int) -> list[SeatResponse]:
        airplane = self.seat_repo.db.query(Airplane).filter(Airplane.id == airplane_id).first()
        if not airplane:
            raise HTTPException(status_code=404, detail="Airplane not found")
        seats = self.seat_repo.get_by_airplane(airplane_id)
        return [SeatResponse.model_validate(seat) for seat in seats]

    def get_seat(self, seat_id: int) -> SeatResponse:
        seat = self.seat_repo.get(seat_id)
        if not seat:
            raise HTTPException(status_code=404, detail="Seat not found")
        return SeatResponse.model_validate(seat)
