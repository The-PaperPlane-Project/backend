from fastapi import HTTPException
from src.models.airplane import Airplane
from src.models.flight import Flight, FlightStatus
from src.models.ticket import Ticket
from src.repositories.flight import FlightRepository
from src.repositories.seat import SeatRepository
from src.repositories.ticket import TicketRepository
from src.schemas.flight import FlightCreate, FlightResponse


class FlightService:
    def __init__(self, flight_repo: FlightRepository, seat_repo: SeatRepository, ticket_repo: TicketRepository):
        self.flight_repo = flight_repo
        self.seat_repo = seat_repo
        self.ticket_repo = ticket_repo

    def create_flight(self, data: FlightCreate) -> FlightResponse:
        airplane = self.flight_repo.db.query(Airplane).filter(Airplane.id == data.airplane_id).first()
        if not airplane:
            raise HTTPException(status_code=404, detail="Airplane not found")
        existing = self.flight_repo.get_by_number(data.flight_number.strip())
        if existing:
            raise HTTPException(status_code=400, detail="Flight with this number already exists")
        payload = data.model_dump(by_alias=False)
        payload["flight_number"] = payload["flight_number"].strip()
        if payload.get("status"):
            try:
                payload["status"] = FlightStatus(payload["status"]).value
            except ValueError as exc:
                allowed = ", ".join(item.value for item in FlightStatus)
                raise HTTPException(status_code=400, detail=f"Недопустимый статус: {payload['status']}. Допустимо: {allowed}") from exc
        flight = Flight(**payload)
        return FlightResponse.model_validate(self.flight_repo.create(flight))

    def get_flight(self, flight_id: int) -> FlightResponse:
        flight = self.flight_repo.get(flight_id)
        if not flight:
            raise HTTPException(status_code=404, detail="Flight not found")
        return FlightResponse.model_validate(flight)

    def get_all_flights(self) -> list[FlightResponse]:
        return [FlightResponse.model_validate(item) for item in self.flight_repo.get_all()]

    def update_status(self, flight_id: int, new_status: FlightStatus | None) -> FlightResponse:
        flight = self.flight_repo.get(flight_id)
        if not flight:
            raise HTTPException(status_code=404, detail="Flight not found")
        status_value = new_status.value if isinstance(new_status, FlightStatus) else None
        return FlightResponse.model_validate(self.flight_repo.update(flight.id, status=status_value))

    def get_seats_with_availability(self, flight_id: int) -> list[dict]:
        flight = self.flight_repo.get(flight_id)
        if not flight:
            raise HTTPException(status_code=404, detail="Flight not found")
        seats = self.seat_repo.get_by_airplane(flight.airplane_id)
        booked = self.ticket_repo.db.query(Ticket).filter(Ticket.flight_id == flight_id).all()
        booked_numbers = {ticket.seat_number for ticket in booked if ticket.seat_number}
        booked_ids = {ticket.seat_id for ticket in booked if ticket.seat_id}
        return [
            {
                "id": seat.id,
                "airplaneId": seat.airplane_id,
                "seatNumber": seat.seat_number,
                "cabinClassId": seat.cabin_class_id,
                "cabinClassType": seat.cabin_class_type or (seat.cabin_class.class_type if seat.cabin_class else None),
                "isBooked": seat.id in booked_ids or seat.seat_number in booked_numbers,
            }
            for seat in seats
        ]


    def delete_flight(self, flight_id: int) -> dict[str, str]:
        flight = self.flight_repo.get(flight_id)
        if not flight:
            raise HTTPException(status_code=404, detail="Flight not found")
        self.flight_repo.delete(flight_id)
        return {"status": "ok"}
