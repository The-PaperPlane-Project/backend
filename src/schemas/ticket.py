from pydantic import BaseModel, Field
from src.schemas.common import camel_model_config


class TicketCreate(BaseModel):
    model_config = camel_model_config

    id: str | None = None
    user_id: int | None = None
    passenger_id: str | None = None
    flight_id: int
    seat_id: int | None = None
    seat_number: str | None = None
    cabin_class: str | None = None
    price: float | None = Field(default=None, ge=0)
    created_at: str | None = None
    is_used: bool = False


class TicketResponse(TicketCreate):
    id: str
