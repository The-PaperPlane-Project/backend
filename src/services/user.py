import hashlib
from fastapi import HTTPException
from src.models.user import User, UserRole
from src.repositories.user import UserRepository
from src.schemas.user import AdminUserCreate, UserCreate, UserResponse


class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def create_user(self, user_data: UserCreate) -> UserResponse:
        email = user_data.email.lower()
        if self.user_repo.get_by_email(email):
            raise HTTPException(status_code=400, detail="Email already registered")
        md5_hash = hashlib.md5(user_data.password.encode()).hexdigest()
        user = User(email=email, password_hash=md5_hash, role=UserRole.USER.value)
        return UserResponse.model_validate(self.user_repo.create(user))

    def get_admins(self) -> list[UserResponse]:
        admins = (
            self.user_repo.db.query(User)
            .filter(User.role == UserRole.ADMIN.value)
            .order_by(User.id)
            .all()
        )
        return [UserResponse.model_validate(admin) for admin in admins]

    def create_admin(self, admin_data: AdminUserCreate) -> UserResponse:
        email = admin_data.email.lower()
        if self.user_repo.get_by_email(email):
            raise HTTPException(status_code=400, detail="Email already registered")
        md5_hash = hashlib.md5(admin_data.password.encode()).hexdigest()
        admin = User(email=email, password_hash=md5_hash, role=UserRole.ADMIN.value)
        return UserResponse.model_validate(self.user_repo.create(admin))

    def delete_admin(self, admin_id: int, current_admin_id: int) -> dict[str, str]:
        admin = self.user_repo.get(admin_id)
        if not admin or admin.role != UserRole.ADMIN.value:
            raise HTTPException(status_code=404, detail="Admin not found")
        if admin.id == current_admin_id:
            raise HTTPException(status_code=400, detail="Cannot delete current admin")

        admins_count = (
            self.user_repo.db.query(User)
            .filter(User.role == UserRole.ADMIN.value)
            .count()
        )
        if admins_count <= 1:
            raise HTTPException(status_code=400, detail="Cannot delete the last admin")

        self.user_repo.delete(admin.id)
        return {"status": "ok"}
