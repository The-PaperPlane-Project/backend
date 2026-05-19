from fastapi import HTTPException
from src.models.user import User
from src.models.user_details import UserDetails
from src.repositories.user_details import UserDetailsRepository
from src.schemas.user_details import UserDetailsCreate, UserDetailsResponse


class UserDetailsService:
    def __init__(self, details_repo: UserDetailsRepository):
        self.details_repo = details_repo

    def create_details(self, data: UserDetailsCreate) -> UserDetailsResponse:
        user = self.details_repo.db.query(User).filter(User.id == data.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        existing = self.details_repo.get_by_user_id(data.user_id)
        payload = data.model_dump(by_alias=False)
        if existing:
            return UserDetailsResponse.model_validate(self.details_repo.update(existing.id, **payload))
        return UserDetailsResponse.model_validate(self.details_repo.create(UserDetails(**payload)))

    def get_by_user(self, user_id: int) -> UserDetailsResponse:
        details = self.details_repo.get_by_user_id(user_id)
        if not details:
            raise HTTPException(status_code=404, detail="User details not found")
        return UserDetailsResponse.model_validate(details)
