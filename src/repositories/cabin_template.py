from sqlalchemy.orm import Session
from src.models.cabin_template import CabinTemplate
from src.repositories.base import BaseRepository


class CabinTemplateRepository(BaseRepository[CabinTemplate]):
    def __init__(self, db: Session):
        super().__init__(CabinTemplate, db)
