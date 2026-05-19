from fastapi import APIRouter, Depends
from src.dependencies import get_user_details_service
from src.schemas.user_details import UserDetailsCreate, UserDetailsResponse
from src.services.user_details import UserDetailsService

router = APIRouter(prefix="/user-details", tags=["user-details"])


@router.post("/", response_model=UserDetailsResponse)
def create_details(data: UserDetailsCreate, service: UserDetailsService = Depends(get_user_details_service)):
    return service.create_details(data)


@router.get("/{user_id}", response_model=UserDetailsResponse)
def get_details(user_id: int, service: UserDetailsService = Depends(get_user_details_service)):
    return service.get_by_user(user_id)
