from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from src.database import Base


class Passenger(Base):
    __tablename__ = "passengers"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    surname = Column(String, nullable=False)
    name = Column(String, nullable=False)
    patronymic = Column(String, nullable=True, default="")
    type = Column(String, nullable=False, default="adult")
    doc_type = Column(String, nullable=False)
    doc_number = Column(String, nullable=False)

    user = relationship("User", back_populates="passengers")
    tickets = relationship("Ticket", back_populates="passenger")
