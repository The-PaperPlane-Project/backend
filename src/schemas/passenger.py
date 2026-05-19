from typing import Literal
from pydantic import BaseModel
from src.schemas.common import camel_model_config


class PassengerCreate(BaseModel):
    model_config = camel_model_config

    id: str | None = None
    user_id: int | None = None
    surname: str
    name: str
    patronymic: str = ""
    type: Literal["adult", "child"] = "adult"
    doc_type: Literal["birth", "passport"]
    doc_number: str


class PassengerResponse(PassengerCreate):
    id: str
