from fastapi import APIRouter, Depends
from src.dependencies import get_current_admin, get_user_service
from src.schemas.user import AdminUserCreate, UserResponse
from src.services.user import UserService

router = APIRouter(prefix="/admin/users", tags=["admin-users"])


@router.get("/admins", response_model=list[UserResponse])
def list_admins(
    service: UserService = Depends(get_user_service),
    admin=Depends(get_current_admin),
):
    return service.get_admins()


@router.post("/admins", response_model=UserResponse)
def create_admin(
    data: AdminUserCreate,
    service: UserService = Depends(get_user_service),
    admin=Depends(get_current_admin),
):
    return service.create_admin(data)


@router.delete("/admins/{admin_id}")
def delete_admin(
    admin_id: int,
    service: UserService = Depends(get_user_service),
    admin=Depends(get_current_admin),
):
    return service.delete_admin(admin_id, admin.id)
