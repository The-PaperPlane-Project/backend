import enum
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from src.database import Base


class FlightStatus(str, enum.Enum):
    REGISTRATION = "registration"
    REGISTRATION_CLOSED = "registration_closed"
    DELAYED = "delayed"
    ARRIVED = "arrived"
    IN_FLIGHT = "in_flight"


class Flight(Base):
    __tablename__ = "flights"

    id = Column(Integer, primary_key=True, index=True)
    airplane_id = Column(Integer, ForeignKey("airplanes.id"), nullable=False, default=101)
    flight_number = Column(String, nullable=False, index=True)
    airline = Column(String, nullable=False)
    origin_city = Column(String, nullable=False)
    origin_code = Column(String, nullable=False)
    destination_city = Column(String, nullable=False)
    destination_code = Column(String, nullable=False)
    departure_date = Column(String, nullable=False)
    departure_time = Column(String, nullable=False)
    arrival_date = Column(String, nullable=False)
    arrival_time = Column(String, nullable=False)
    status = Column(String, nullable=True)
    is_departure = Column(Boolean, nullable=False, default=True)
    base_price = Column(Float, nullable=False, default=6800)

    airplane = relationship("Airplane", back_populates="flights")
    tickets = relationship("Ticket", back_populates="flight", cascade="all, delete-orphan")
