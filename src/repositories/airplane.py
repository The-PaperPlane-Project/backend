from sqlalchemy.orm import Session
from src.models.airplane import Airplane
from src.repositories.base import BaseRepository


class AirplaneRepository(BaseRepository[Airplane]):
    def __init__(self, db: Session):
        super().__init__(Airplane, db)
