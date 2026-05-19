from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from src.database import Base


class CabinClass(Base):
    __tablename__ = "cabin_classes"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("cabin_templates.id"), nullable=False)
    class_type = Column(String, nullable=False)
    rows = Column(Integer, nullable=False)
    seats_per_row = Column(Integer, nullable=False)
    order = Column(Integer, nullable=False)

    template = relationship("CabinTemplate", back_populates="classes")
    seats = relationship("Seat", back_populates="cabin_class")
