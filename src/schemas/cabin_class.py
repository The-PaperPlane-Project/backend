from pydantic import BaseModel, Field
from src.schemas.common import camel_model_config


class CabinClassCreate(BaseModel):
    model_config = camel_model_config

    class_type: str = Field(..., pattern="^(first|business|economy)$")
    rows: int = Field(..., gt=0)
    seats_per_row: int = Field(..., ge=1, le=8)
    order: int


class CabinClassResponse(CabinClassCreate):
    id: int
