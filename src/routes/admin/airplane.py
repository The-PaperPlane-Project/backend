from fastapi import APIRouter, Depends
from src.dependencies import get_airplane_service, get_current_admin
from src.schemas.airplane import AirplaneCreate, AirplaneResponse
from src.services.airplane import AirplaneService

router = APIRouter(prefix="/admin/airplanes", tags=["admin-airplanes"])


@router.post("/", response_model=AirplaneResponse)
def create_airplane(
    data: AirplaneCreate,
    service: AirplaneService = Depends(get_airplane_service),
    admin=Depends(get_current_admin),
):
    return service.create_airplane(data)


@router.put("/{airplane_id}", response_model=AirplaneResponse)
def update_airplane(
    airplane_id: int,
    data: AirplaneCreate,
    service: AirplaneService = Depends(get_airplane_service),
    admin=Depends(get_current_admin),
):
    return service.update_airplane(airplane_id, data)


@router.delete("/{airplane_id}")
def delete_airplane(
    airplane_id: int,
    service: AirplaneService = Depends(get_airplane_service),
    admin=Depends(get_current_admin),
):
    return service.delete_airplane(airplane_id)
