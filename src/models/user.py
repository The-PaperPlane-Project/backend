import enum
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from src.database import Base


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default=UserRole.USER.value, nullable=False)

    details = relationship("UserDetails", back_populates="user", uselist=False, cascade="all, delete-orphan")
    passengers = relationship("Passenger", back_populates="user", cascade="all, delete-orphan")
    tickets = relationship("Ticket", back_populates="user", cascade="all, delete-orphan")
