from pydantic import BaseModel, Field
from src.schemas.common import camel_model_config


class FlightCreate(BaseModel):
    model_config = camel_model_config

    airplane_id: int = Field(101, alias="planeId")
    flight_number: str
    airline: str
    origin_city: str
    origin_code: str
    destination_city: str
    destination_code: str
    departure_date: str
    departure_time: str
    arrival_date: str
    arrival_time: str
    status: str | None = None
    is_departure: bool = True
    base_price: float = 6800


class FlightResponse(FlightCreate):
    id: int
