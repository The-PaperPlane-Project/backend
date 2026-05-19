from fastapi import HTTPException
from src.models.airplane import Airplane
from src.models.seat import Seat
from src.models.ticket import Ticket
from src.repositories.airplane import AirplaneRepository
from src.schemas.airplane import AirplaneCreate, AirplaneResponse


class AirplaneService:
    def __init__(self, airplane_repo: AirplaneRepository):
        self.airplane_repo = airplane_repo

    def _seat_number(self, row_index: int, col_index: int) -> str:
        return f"{row_index + 1}{chr(65 + col_index)}"

    def _sync_seats_from_matrix(self, airplane: Airplane) -> None:
        """Store the cabin scheme in SQL seats table.

        The frontend draws the cabin from airplane.cabin_matrix, while backend
        booking validation uses Seat rows. Therefore both representations must
        be updated together.
        """
        db = self.airplane_repo.db
        db.query(Seat).filter(Seat.airplane_id == airplane.id).delete()
        matrix = airplane.cabin_matrix or []
        seen: set[str] = set()
        for row_index, row in enumerate(matrix):
            if not isinstance(row, list):
                continue
            for col_index, cell in enumerate(row):
                cell_type = cell.get("type", "economy") if isinstance(cell, dict) else "economy"
                if cell_type in {"empty", "toilet"}:
                    continue
                seat_number = self._seat_number(row_index, col_index)
                if seat_number in seen:
                    raise HTTPException(status_code=400, detail=f"Duplicate seat {seat_number} for airplane")
                seen.add(seat_number)
                db.add(Seat(
                    airplane_id=airplane.id,
                    seat_number=seat_number,
                    cabin_class_type=cell_type,
                ))
        db.commit()
        db.refresh(airplane)

    def _validate_duplicate_registration(self, registration_number: str | None, excluded_id: int | None = None) -> None:
        if not registration_number:
            return
        query = self.airplane_repo.db.query(Airplane).filter(Airplane.registration_number == registration_number)
        if excluded_id is not None:
            query = query.filter(Airplane.id != excluded_id)
        if query.first():
            raise HTTPException(status_code=400, detail="Airplane with this registration number already exists")

    def _validate_duplicate_name_model(self, name: str, model: str, excluded_id: int | None = None) -> None:
        query = self.airplane_repo.db.query(Airplane)
        if excluded_id is not None:
            query = query.filter(Airplane.id != excluded_id)
        existing = query.all()
        name_key = name.strip().lower()
        model_key = model.strip().lower()
        if any(item.name.strip().lower() == name_key for item in existing):
            raise HTTPException(status_code=400, detail="Airplane with this name already exists")
        if any(item.model.strip().lower() == model_key for item in existing):
            raise HTTPException(status_code=400, detail="Airplane with this model already exists")

    def create_airplane(self, data: AirplaneCreate) -> AirplaneResponse:
        payload = data.model_dump(by_alias=False)
        self._validate_duplicate_registration(payload.get("registration_number"))
        self._validate_duplicate_name_model(payload["name"], payload["model"])
        airplane = Airplane(**payload)
        airplane = self.airplane_repo.create(airplane)
        self._sync_seats_from_matrix(airplane)
        return AirplaneResponse.model_validate(airplane)

    def update_airplane(self, airplane_id: int, data: AirplaneCreate) -> AirplaneResponse:
        airplane = self.airplane_repo.get(airplane_id)
        if not airplane:
            raise HTTPException(status_code=404, detail="Airplane not found")
        has_booked_tickets = (
            self.airplane_repo.db.query(Ticket)
            .join(Seat, Ticket.seat_id == Seat.id)
            .filter(Seat.airplane_id == airplane_id)
            .first()
        )
        if has_booked_tickets:
            raise HTTPException(status_code=400, detail="Cannot edit airplane cabin after tickets were booked")

        payload = data.model_dump(by_alias=False)
        self._validate_duplicate_registration(payload.get("registration_number"), excluded_id=airplane_id)
        self._validate_duplicate_name_model(payload["name"], payload["model"], excluded_id=airplane_id)
        for key, value in payload.items():
            setattr(airplane, key, value)
        self.airplane_repo.db.commit()
        self.airplane_repo.db.refresh(airplane)
        self._sync_seats_from_matrix(airplane)
        return AirplaneResponse.model_validate(airplane)

    def delete_airplane(self, airplane_id: int) -> dict[str, str]:
        airplane = self.airplane_repo.get(airplane_id)
        if not airplane:
            raise HTTPException(status_code=404, detail="Airplane not found")
        if airplane.flights:
            raise HTTPException(status_code=400, detail="Airplane is used in flights")
        self.airplane_repo.delete(airplane_id)
        return {"status": "ok"}

    def get_airplane(self, airplane_id: int) -> AirplaneResponse:
        airplane = self.airplane_repo.get(airplane_id)
        if not airplane:
            raise HTTPException(status_code=404, detail="Airplane not found")
        return AirplaneResponse.model_validate(airplane)

    def get_all_airplanes(self) -> list[AirplaneResponse]:
        return [AirplaneResponse.model_validate(item) for item in self.airplane_repo.get_all()]
