from fastapi import APIRouter, Depends, HTTPException
from src.dependencies import get_current_admin, get_flight_service
from src.models.flight import FlightStatus
from src.schemas.flight import FlightCreate, FlightResponse
from src.services.flight import FlightService

router = APIRouter(prefix="/admin/flights", tags=["admin-flights"])


@router.post("/", response_model=FlightResponse)
def create_flight(data: FlightCreate, service: FlightService = Depends(get_flight_service), admin=Depends(get_current_admin)):
    return service.create_flight(data)


@router.patch("/{flight_id}/status", response_model=FlightResponse)
def update_flight_status(
    flight_id: int,
    status: str | None = None,
    service: FlightService = Depends(get_flight_service),
    admin=Depends(get_current_admin),
):
    if status is None:
        return service.update_status(flight_id, None)
    try:
        flight_status = FlightStatus(status)
    except ValueError as exc:
        allowed = ", ".join(item.value for item in FlightStatus)
        raise HTTPException(status_code=400, detail=f"Недопустимый статус: {status}. Допустимо: {allowed}") from exc
    return service.update_status(flight_id, flight_status)


@router.delete("/{flight_id}")
def delete_flight(
    flight_id: int,
    service: FlightService = Depends(get_flight_service),
    admin=Depends(get_current_admin),
):
    return service.delete_flight(flight_id)
