from fastapi import APIRouter, Depends
from src.dependencies import get_flight_service
from src.schemas.flight import FlightResponse
from src.services.flight import FlightService

router = APIRouter(prefix="/flights", tags=["flights"])


@router.get("/", response_model=list[FlightResponse])
def list_flights(service: FlightService = Depends(get_flight_service)):
    return service.get_all_flights()


@router.get("/{flight_id}", response_model=FlightResponse)
def get_flight(flight_id: int, service: FlightService = Depends(get_flight_service)):
    return service.get_flight(flight_id)


@router.get("/{flight_id}/seats")
def flight_seats(flight_id: int, service: FlightService = Depends(get_flight_service)):
    return service.get_seats_with_availability(flight_id)
