from sqlalchemy import Column, Integer, String
from src.database import Base


class AirportCity(Base):
    __tablename__ = "airport_cities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, nullable=False, unique=True, index=True)
