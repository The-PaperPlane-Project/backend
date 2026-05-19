from pydantic import BaseModel
from src.schemas.common import camel_model_config


class AirportCityCreate(BaseModel):
    model_config = camel_model_config

    name: str
    code: str


class AirportCityResponse(AirportCityCreate):
    id: int
