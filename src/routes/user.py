from fastapi import APIRouter, Depends
from src.dependencies import get_user_service
from src.schemas.user import UserCreate, UserResponse
from src.services.user import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserResponse)
def create_user(user_data: UserCreate, service: UserService = Depends(get_user_service)):
    return service.create_user(user_data)
