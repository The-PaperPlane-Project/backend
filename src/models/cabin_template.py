from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from src.database import Base


class CabinTemplate(Base):
    __tablename__ = "cabin_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    number_of_aisles = Column(Integer, nullable=False, default=1)

    classes = relationship("CabinClass", back_populates="template", order_by="CabinClass.order", cascade="all, delete-orphan")
