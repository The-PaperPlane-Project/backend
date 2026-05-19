from typing import Any
from pydantic import BaseModel, Field
from src.schemas.common import camel_model_config


class AirplaneCreate(BaseModel):
    model_config = camel_model_config

    name: str = "Самолет"
    model: str
    type_label: str = "Пассажирский"
    cabin_rows: int = 8
    cabin_cols: int = 4
    cabin_matrix: list[list[dict[str, Any]]] = Field(default_factory=list)
    registration_number: str | None = None


class AirplaneResponse(AirplaneCreate):
    id: int
