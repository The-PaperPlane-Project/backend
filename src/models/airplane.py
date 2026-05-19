from sqlalchemy import Column, Integer, String, JSON
from sqlalchemy.orm import relationship
from src.database import Base


class Airplane(Base):
    __tablename__ = "airplanes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    model = Column(String, nullable=False)
    type_label = Column(String, nullable=False, default="Пассажирский")
    cabin_rows = Column(Integer, nullable=False, default=8)
    cabin_cols = Column(Integer, nullable=False, default=4)
    cabin_matrix = Column(JSON, nullable=False, default=list)
    registration_number = Column(String, unique=True, nullable=True)

    seats = relationship("Seat", back_populates="airplane", cascade="all, delete-orphan")
    flights = relationship("Flight", back_populates="airplane")
