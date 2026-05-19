from pydantic import BaseModel, EmailStr, Field
from src.schemas.common import camel_model_config


class UserCreate(BaseModel):
    model_config = camel_model_config

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=24)


class AdminUserCreate(BaseModel):
    model_config = camel_model_config

    email: EmailStr
    password: str = Field(..., min_length=5, max_length=24)


class UserResponse(BaseModel):
    model_config = camel_model_config

    id: int
    email: EmailStr
    role: str = "user"
