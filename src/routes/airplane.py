from fastapi import APIRouter, Depends
from src.dependencies import get_airplane_service
from src.schemas.airplane import AirplaneResponse
from src.services.airplane import AirplaneService

router = APIRouter(prefix="/airplanes", tags=["airplanes"])


@router.get("/", response_model=list[AirplaneResponse])
def list_airplanes(service: AirplaneService = Depends(get_airplane_service)):
    return service.get_all_airplanes()


@router.get("/{airplane_id}", response_model=AirplaneResponse)
def get_airplane(airplane_id: int, service: AirplaneService = Depends(get_airplane_service)):
    return service.get_airplane(airplane_id)
