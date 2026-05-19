from pydantic import BaseModel
from src.schemas.common import camel_model_config


class SeatCreate(BaseModel):
    model_config = camel_model_config

    airplane_id: int
    seat_number: str
    cabin_class_id: int | None = None
    cabin_class_type: str | None = None


class SeatResponse(SeatCreate):
    id: int
    is_booked: bool = False
