from pydantic import BaseModel
from src.schemas.common import camel_model_config


class UserDetailsCreate(BaseModel):
    model_config = camel_model_config

    user_id: int
    first_name: str
    last_name: str
    passport_type: str | None = None
    passport_serial: str | None = None
    passport_number: str | None = None


class UserDetailsResponse(UserDetailsCreate):
    id: int
