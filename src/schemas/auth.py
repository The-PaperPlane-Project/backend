from pydantic import BaseModel, EmailStr, Field
from src.schemas.common import camel_model_config


class UserRegister(BaseModel):
    model_config = camel_model_config

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=24)


class UserLogin(BaseModel):
    model_config = camel_model_config

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
