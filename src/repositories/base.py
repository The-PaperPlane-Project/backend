from typing import Any, Generic, List, Optional, Type, TypeVar

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get(self, id: Any) -> Optional[ModelType]:
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_all(self, skip: int = 0, limit: int = 1000) -> List[ModelType]:
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def create(self, obj_in: ModelType) -> ModelType:
        try:
            self.db.add(obj_in)
            self.db.commit()
            self.db.refresh(obj_in)
            return obj_in
        except IntegrityError as exc:
            self.db.rollback()
            raise HTTPException(status_code=400, detail="Database integrity error: duplicate or invalid related data") from exc

    def update(self, id: Any, **kwargs) -> Optional[ModelType]:
        obj = self.get(id)
        if not obj:
            return None
        try:
            for key, value in kwargs.items():
                setattr(obj, key, value)
            self.db.commit()
            self.db.refresh(obj)
            return obj
        except IntegrityError as exc:
            self.db.rollback()
            raise HTTPException(status_code=400, detail="Database integrity error: duplicate or invalid related data") from exc

    def delete(self, id: Any) -> None:
        obj = self.get(id)
        if obj:
            self.db.delete(obj)
            self.db.commit()
