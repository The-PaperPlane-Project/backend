from sqlalchemy.orm import Session
from src.models.passenger import Passenger
from src.repositories.base import BaseRepository


class PassengerRepository(BaseRepository[Passenger]):
    def __init__(self, db: Session):
        super().__init__(Passenger, db)

    def get_by_user(self, user_id: int) -> list[Passenger]:
        return self.db.query(Passenger).filter(Passenger.user_id == user_id).all()
