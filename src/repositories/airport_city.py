from sqlalchemy.orm import Session
from src.models.airport_city import AirportCity
from src.repositories.base import BaseRepository


class AirportCityRepository(BaseRepository[AirportCity]):
    def __init__(self, db: Session):
        super().__init__(AirportCity, db)

    def get_by_code(self, code: str) -> AirportCity | None:
        return self.db.query(AirportCity).filter(AirportCity.code == code.upper()).first()
