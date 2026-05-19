from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from src.database import Base


class UserDetails(Base):
    __tablename__ = "user_details"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    passport_type = Column(String, nullable=True)
    passport_serial = Column(String, nullable=True)
    passport_number = Column(String, nullable=True)

    user = relationship("User", back_populates="details")
