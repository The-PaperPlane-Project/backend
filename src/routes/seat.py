from fastapi import APIRouter, Depends
from src.dependencies import get_seat_service
from src.schemas.seat import SeatResponse
from src.services.seat import SeatService

router = APIRouter(prefix="/seats", tags=["seats"])


@router.get("/available/{airplane_id}", response_model=list[SeatResponse])
def available_seats(airplane_id: int, service: SeatService = Depends(get_seat_service)):
    return service.get_available_seats(airplane_id)
