from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from src.database import Base


class Seat(Base):
    __tablename__ = "seats"
    __table_args__ = (UniqueConstraint("airplane_id", "seat_number", name="uq_airplane_seat_number"),)

    id = Column(Integer, primary_key=True, index=True)
    airplane_id = Column(Integer, ForeignKey("airplanes.id"), nullable=False)
    seat_number = Column(String, nullable=False)
    cabin_class_id = Column(Integer, ForeignKey("cabin_classes.id"), nullable=True)
    cabin_class_type = Column(String, nullable=True)

    airplane = relationship("Airplane", back_populates="seats")
    cabin_class = relationship("CabinClass", back_populates="seats")
    tickets = relationship("Ticket", back_populates="seat")
