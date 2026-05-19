from sqlalchemy.orm import Session
from src.models.user_details import UserDetails
from src.repositories.base import BaseRepository


class UserDetailsRepository(BaseRepository[UserDetails]):
    def __init__(self, db: Session):
        super().__init__(UserDetails, db)

    def get_by_user_id(self, user_id: int) -> UserDetails | None:
        return self.db.query(UserDetails).filter(UserDetails.user_id == user_id).first()
