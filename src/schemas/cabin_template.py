from pydantic import BaseModel
from src.schemas.cabin_class import CabinClassCreate, CabinClassResponse
from src.schemas.common import camel_model_config


class CabinTemplateCreate(BaseModel):
    model_config = camel_model_config

    name: str
    number_of_aisles: int = 1
    classes: list[CabinClassCreate]


class CabinTemplateResponse(BaseModel):
    model_config = camel_model_config

    id: int
    name: str
    number_of_aisles: int
    classes: list[CabinClassResponse] = []
