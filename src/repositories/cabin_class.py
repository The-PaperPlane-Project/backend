from sqlalchemy.orm import Session
from src.models.cabin_class import CabinClass
from src.repositories.base import BaseRepository


class CabinClassRepository(BaseRepository[CabinClass]):
    def __init__(self, db: Session):
        super().__init__(CabinClass, db)
