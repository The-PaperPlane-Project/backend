from fastapi import APIRouter, Depends
from typing import List
from src.schemas.cabin_template import CabinTemplateCreate, CabinTemplateResponse
from src.schemas.seat import SeatResponse
from src.services.cabin_template import CabinTemplateService
from src.dependencies import get_cabin_template_service, get_current_admin

router = APIRouter(prefix="/admin/cabin-templates", tags=["admin-cabin-templates"])

@router.post("/", response_model=CabinTemplateResponse)
def create_template(data: CabinTemplateCreate,
                    service: CabinTemplateService = Depends(get_cabin_template_service),
                    admin = Depends(get_current_admin)):
    return service.create_template(data)

@router.post("/{template_id}/generate-seats/{airplane_id}", response_model=List[SeatResponse])
def generate_seats(template_id: int, airplane_id: int,
                   service: CabinTemplateService = Depends(get_cabin_template_service),
                   admin = Depends(get_current_admin)):
    return service.generate_seats(template_id, airplane_id)

@router.get("/{template_id}/visualize", response_model=dict)
def visualize(template_id: int, airplane_id: int = None,
              service: CabinTemplateService = Depends(get_cabin_template_service)):
    return service.visualize(template_id, airplane_id)