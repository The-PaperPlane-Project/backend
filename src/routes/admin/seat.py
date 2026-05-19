from fastapi import APIRouter, Depends
from src.dependencies import get_current_admin, get_seat_service
from src.schemas.seat import SeatCreate, SeatResponse
from src.services.seat import SeatService

router = APIRouter(prefix="/admin/seats", tags=["admin-seats"])


@router.post("/", response_model=SeatResponse)
def create_seat(data: SeatCreate, service: SeatService = Depends(get_seat_service), admin=Depends(get_current_admin)):
    return service.create_seat(data)
