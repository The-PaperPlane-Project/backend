from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from src.dependencies import get_auth_service, get_current_user
from src.schemas.auth import TokenResponse, UserLogin, UserRegister
from src.schemas.user import UserResponse
from src.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
def register(data: UserRegister, service: AuthService = Depends(get_auth_service)):
    return service.register(data.email, data.password)


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), service: AuthService = Depends(get_auth_service)):
    return service.authenticate(form_data.username, form_data.password)


@router.post("/login-json", response_model=TokenResponse)
def login_json(data: UserLogin, service: AuthService = Depends(get_auth_service)):
    return service.authenticate(data.email, data.password)


@router.get("/me", response_model=UserResponse)
def me(current_user=Depends(get_current_user)):
    return UserResponse.model_validate(current_user)
