from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.database import SessionLocal
from src.services.data_file import build_airport_data_from_sql, replace_sql_from_payload, seed_sql_from_json

router = APIRouter(prefix="/api/database", tags=["database-file"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("")
def get_database_file(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Return the whole frontend-compatible database as one JSON object from SQL DB."""
    return build_airport_data_from_sql(db)


@router.put("")
def put_database_file(payload: dict[str, Any], db: Session = Depends(get_db)) -> dict[str, Any]:
    """Replace SQL airport data using the whole frontend-compatible JSON object."""
    return replace_sql_from_payload(db, payload)


@router.post("/sync-to-sql")
def sync_database_file_to_sql(db: Session = Depends(get_db)) -> dict[str, str]:
    """Seed empty SQL tables from airport_data.json."""
    seed_sql_from_json(db)
    return {"status": "ok"}
