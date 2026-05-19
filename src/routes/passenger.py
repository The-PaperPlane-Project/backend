import re
import uuid
from fastapi import APIRouter, Depends, HTTPException
from src.dependencies import get_passenger_repo
from src.models.passenger import Passenger
from src.models.user import User
from src.schemas.passenger import PassengerCreate, PassengerResponse

router = APIRouter(prefix="/passengers", tags=["passengers"])


def _normalize_text(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _doc_digits(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def _identity_key(passenger: PassengerCreate | Passenger) -> tuple[str, str, str, str, str]:
    return (
        _normalize_text(passenger.surname),
        _normalize_text(passenger.name),
        _normalize_text(passenger.patronymic or ""),
        passenger.doc_type,
        _doc_digits(passenger.doc_number),
    )


def _validate_user_exists(repo, user_id: int | None) -> None:
    if user_id is None:
        return
    user = repo.db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")


@router.get("/user/{user_id}", response_model=list[PassengerResponse])
def list_user_passengers(user_id: int, repo=Depends(get_passenger_repo)):
    _validate_user_exists(repo, user_id)
    return [PassengerResponse.model_validate(item) for item in repo.get_by_user(user_id)]


@router.post("/", response_model=PassengerResponse)
def create_passenger(data: PassengerCreate, repo=Depends(get_passenger_repo)):
    _validate_user_exists(repo, data.user_id)
    candidate_key = _identity_key(data)
    existing_passengers = repo.get_by_user(data.user_id) if data.user_id is not None else repo.get_all()
    for passenger in existing_passengers:
        if _identity_key(passenger) == candidate_key:
            raise HTTPException(status_code=400, detail="Passenger with the same personal data already exists")

    payload = data.model_dump(by_alias=False)
    if not payload.get("id"):
        payload["id"] = str(uuid.uuid4())
    passenger = Passenger(**payload)
    return PassengerResponse.model_validate(repo.create(passenger))


@router.get("/{passenger_id}", response_model=PassengerResponse)
def get_passenger(passenger_id: str, repo=Depends(get_passenger_repo)):
    passenger = repo.get(passenger_id)
    if not passenger:
        raise HTTPException(status_code=404, detail="Passenger not found")
    return PassengerResponse.model_validate(passenger)


@router.put("/{passenger_id}", response_model=PassengerResponse)
def update_passenger(passenger_id: str, data: PassengerCreate, repo=Depends(get_passenger_repo)):
    passenger = repo.get(passenger_id)
    if not passenger:
        raise HTTPException(status_code=404, detail="Passenger not found")
    _validate_user_exists(repo, data.user_id)

    candidate_key = _identity_key(data)
    existing_passengers = repo.get_by_user(data.user_id) if data.user_id is not None else repo.get_all()
    for existing in existing_passengers:
        if existing.id != passenger_id and _identity_key(existing) == candidate_key:
            raise HTTPException(status_code=400, detail="Passenger with the same personal data already exists")

    passenger.user_id = data.user_id
    passenger.surname = data.surname
    passenger.name = data.name
    passenger.patronymic = data.patronymic
    passenger.type = data.type
    passenger.doc_type = data.doc_type
    passenger.doc_number = data.doc_number
    repo.db.commit()
    repo.db.refresh(passenger)
    return PassengerResponse.model_validate(passenger)


@router.delete("/{passenger_id}")
def delete_passenger(passenger_id: str, repo=Depends(get_passenger_repo)):
    passenger = repo.get(passenger_id)
    if not passenger:
        raise HTTPException(status_code=404, detail="Passenger not found")
    if passenger.tickets:
        raise HTTPException(status_code=400, detail="Passenger has booked tickets")
    repo.db.delete(passenger)
    repo.db.commit()
    return {"status": "ok"}
