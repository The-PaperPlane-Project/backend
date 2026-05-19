from datetime import datetime, timedelta, timezone
import hashlib
import os
from dotenv import load_dotenv
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from src.models.user import User, UserRole
from src.repositories.user import UserRepository
from src.schemas.user import UserResponse

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "change-me-for-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def register(self, email: str, password: str) -> UserResponse:
        email = email.lower()
        if self.user_repo.get_by_email(email):
            raise HTTPException(status_code=400, detail="Email already registered")
        user = User(email=email, password_hash=self._hash_password(password), role=UserRole.USER.value)
        return UserResponse.model_validate(self.user_repo.create(user))

    def authenticate(self, email: str, password: str) -> dict[str, str]:
        user = self.user_repo.get_by_email(email.lower())
        if not user or not self._verify_password(password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        access_token = self._create_access_token({"sub": user.email, "role": user.role})
        return {"access_token": access_token, "token_type": "bearer"}

    def _hash_password(self, password: str) -> str:
        # По ТЗ нужен md5. Если в БД есть bcrypt-хеши, verify ниже тоже их понимает.
        return hashlib.md5(password.encode()).hexdigest()

    def _verify_password(self, password: str, password_hash: str) -> bool:
        if len(password_hash) == 32:
            return hashlib.md5(password.encode()).hexdigest() == password_hash
        try:
            return pwd_context.verify(password, password_hash)
        except Exception:
            return False

    def _create_access_token(self, data: dict) -> str:
        payload = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        payload.update({"exp": expire})
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    def get_current_user(self, token: str = Depends(oauth2_scheme)) -> User:
        exception = HTTPException(status_code=401, detail="Could not validate credentials")
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            email = payload.get("sub")
            if email is None:
                raise exception
        except JWTError:
            raise exception
        user = self.user_repo.get_by_email(email)
        if not user:
            raise exception
        return user

    def get_current_admin(self, token: str = Depends(oauth2_scheme)) -> User:
        user = self.get_current_user(token)
        if user.role != UserRole.ADMIN.value:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        return user
