from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import relationship
from src.database import Base


class Ticket(Base):
    __tablename__ = "tickets"
    __table_args__ = (UniqueConstraint("flight_id", "seat_number", name="uq_flight_seat_number"),)

    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    passenger_id = Column(String, ForeignKey("passengers.id"), nullable=True)
    flight_id = Column(Integer, ForeignKey("flights.id"), nullable=False)
    seat_id = Column(Integer, ForeignKey("seats.id"), nullable=True)
    seat_number = Column(String, nullable=True)
    cabin_class = Column(String, nullable=True)
    price = Column(Float, nullable=True)
    created_at = Column(String, nullable=True)
    booked_at = Column(DateTime, server_default=func.now())
    is_used = Column(Boolean, nullable=False, default=False, server_default="0")

    user = relationship("User", back_populates="tickets")
    passenger = relationship("Passenger", back_populates="tickets")
    flight = relationship("Flight", back_populates="tickets")
    seat = relationship("Seat", back_populates="tickets")
