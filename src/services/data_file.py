import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any
from fastapi import HTTPException
from sqlalchemy.orm import Session
from src.models.airplane import Airplane
from src.models.airport_city import AirportCity
from src.models.flight import Flight, FlightStatus
from src.models.passenger import Passenger
from src.models.seat import Seat
from src.models.ticket import Ticket
from src.models.user import User, UserRole
from src.models.user_details import UserDetails

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "airport_data.json"
BACKUP_DIR = DATA_DIR / "backups"

REQUIRED_KEYS = {"planes", "cities", "flights", "passengers", "tickets"}
DEFAULT_ACCOUNTS = (
    ("admin@paperplane.ru", "admin", UserRole.ADMIN.value),
    ("user1@paperplane.ru", "qwerty112", UserRole.USER.value),
    ("user2@paperplane.ru", "qwerty112", UserRole.USER.value),
)
LEGACY_DEFAULT_EMAIL_TARGETS = (
    ("admin@paperplane.local", "admin@paperplane.ru"),
    ("itakashh11@gmail.com", "user1@paperplane.ru"),
    ("coperman2006@gmail.com", "user2@paperplane.ru"),
    ("user1@mail.ru", "user1@paperplane.ru"),
    ("user2@mail.ru", "user2@paperplane.ru"),
)


def load_airport_data() -> dict[str, Any]:
    if not DATA_FILE.exists():
        raise HTTPException(status_code=500, detail="airport_data.json not found")
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"airport_data.json is invalid: {exc}") from exc


def save_airport_data(payload: dict[str, Any]) -> dict[str, Any]:
    missing = REQUIRED_KEYS - set(payload.keys())
    if missing:
        raise HTTPException(status_code=422, detail=f"Missing keys: {', '.join(sorted(missing))}")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    if DATA_FILE.exists():
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(DATA_FILE, BACKUP_DIR / f"airport_data_{stamp}.json")

    tmp_file = DATA_FILE.with_suffix(".json.tmp")
    tmp_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_file.replace(DATA_FILE)
    return payload


def _seat_number(row_index: int, col_index: int) -> str:
    return f"{row_index + 1}{chr(65 + col_index)}"


def _upsert_default_account(db: Session, email: str, password: str, role: str) -> None:
    import hashlib

    normalized_email = email.lower()
    password_hash = hashlib.md5(password.encode()).hexdigest()
    user = db.query(User).filter(User.email == normalized_email).first()

    if user:
        user.password_hash = password_hash
        user.role = role
    else:
        db.add(User(
            email=normalized_email,
            password_hash=password_hash,
            role=role,
        ))
    db.flush()


def _move_legacy_default_account(db: Session, legacy_email: str, target_email: str) -> None:
    legacy_email = legacy_email.lower()
    target_email = target_email.lower()
    if legacy_email == target_email:
        return

    legacy = db.query(User).filter(User.email == legacy_email).first()
    if not legacy:
        return

    target = db.query(User).filter(User.email == target_email).first()
    if target and target.id != legacy.id:
        db.query(Passenger).filter(Passenger.user_id == legacy.id).update(
            {"user_id": target.id},
            synchronize_session=False,
        )
        db.query(Ticket).filter(Ticket.user_id == legacy.id).update(
            {"user_id": target.id},
            synchronize_session=False,
        )

        legacy_details = db.query(UserDetails).filter(UserDetails.user_id == legacy.id).first()
        target_details = db.query(UserDetails).filter(UserDetails.user_id == target.id).first()
        if legacy_details:
            if target_details:
                db.delete(legacy_details)
            else:
                legacy_details.user_id = target.id

        db.delete(legacy)
    else:
        legacy.email = target_email
    db.flush()


def seed_sql_from_json(db: Session) -> None:
    data = load_airport_data()

    if db.query(Airplane).count() == 0:
        for plane in data.get("planes", []):
            db.add(Airplane(
                id=plane["id"],
                name=plane.get("name") or plane.get("model") or "Самолет",
                model=plane.get("model") or plane.get("name") or "Unknown",
                type_label=plane.get("typeLabel", "Пассажирский"),
                cabin_rows=plane.get("cabinRows", 8),
                cabin_cols=plane.get("cabinCols", 4),
                cabin_matrix=plane.get("cabinMatrix", []),
                registration_number=plane.get("registrationNumber"),
            ))
        db.commit()

    if db.query(AirportCity).count() == 0:
        for city in data.get("cities", []):
            db.add(AirportCity(id=city["id"], name=city["name"], code=city["code"].upper()))
        db.commit()

    if db.query(Flight).count() == 0:
        for flight in data.get("flights", []):
            status_value = flight.get("status")
            db.add(Flight(
                id=flight["id"],
                airplane_id=flight.get("planeId", 101),
                flight_number=flight["flightNumber"],
                airline=flight["airline"],
                origin_city=flight["originCity"],
                origin_code=flight["originCode"],
                destination_city=flight["destinationCity"],
                destination_code=flight["destinationCode"],
                departure_date=flight["departureDate"],
                departure_time=flight["departureTime"],
                arrival_date=flight["arrivalDate"],
                arrival_time=flight["arrivalTime"],
                status=status_value,
                is_departure=flight.get("isDeparture", True),
                base_price=flight.get("basePrice", 6800),
            ))
        db.commit()

    if db.query(Seat).count() == 0:
        for plane in data.get("planes", []):
            matrix = plane.get("cabinMatrix") or []
            for row_index, row in enumerate(matrix):
                for col_index, cell in enumerate(row):
                    cell_type = cell.get("type", "economy") if isinstance(cell, dict) else "economy"
                    if cell_type in {"empty", "toilet"}:
                        continue
                    db.add(Seat(
                        airplane_id=plane["id"],
                        seat_number=_seat_number(row_index, col_index),
                        cabin_class_type=cell_type,
                    ))
        db.commit()

    if db.query(Passenger).count() == 0:
        for passenger in data.get("passengers", []):
            db.add(Passenger(
                id=str(passenger["id"]),
                surname=passenger["surname"],
                name=passenger["name"],
                patronymic=passenger.get("patronymic", ""),
                type=passenger.get("type", "adult"),
                doc_type=passenger.get("docType", "passport"),
                doc_number=passenger.get("docNumber", ""),
            ))
        db.commit()

    for legacy_email, target_email in LEGACY_DEFAULT_EMAIL_TARGETS:
        _move_legacy_default_account(db, legacy_email, target_email)
    for email, password, role in DEFAULT_ACCOUNTS:
        _upsert_default_account(db, email, password, role)
    db.commit()



def _validate_payload(payload: dict[str, Any]) -> None:
    missing = REQUIRED_KEYS - set(payload.keys())
    if missing:
        raise HTTPException(status_code=422, detail=f"Missing keys: {', '.join(sorted(missing))}")


def _normalize_seat_number(row_index: int, col_index: int) -> str:
    return f"{row_index + 1}{chr(65 + col_index)}"


def replace_sql_from_payload(db: Session, payload: dict[str, Any]) -> dict[str, Any]:
    _validate_payload(payload)

    seen_plane_ids: set[int] = set()
    seen_city_ids: set[int] = set()
    seen_city_codes: set[str] = set()
    seen_flight_ids: set[int] = set()
    seen_flight_numbers: set[str] = set()
    seen_passenger_ids: set[str] = set()
    seen_ticket_ids: set[str] = set()
    seen_flight_seats: set[tuple[int, str]] = set()

    try:
        db.query(Ticket).delete()
        db.query(Passenger).delete()
        db.query(Seat).delete()
        db.query(Flight).delete()
        db.query(Airplane).delete()
        db.query(AirportCity).delete()
        db.commit()

        for plane in payload.get("planes", []):
            plane_id = int(plane["id"])
            if plane_id in seen_plane_ids:
                raise HTTPException(status_code=400, detail=f"Duplicate plane id: {plane_id}")
            seen_plane_ids.add(plane_id)

            matrix = plane.get("cabinMatrix") or []
            cabin_rows = int(plane.get("cabinRows") or len(matrix) or 8)
            cabin_cols = int(plane.get("cabinCols") or (len(matrix[0]) if matrix else 4))
            db.add(Airplane(
                id=plane_id,
                name=plane.get("name") or plane.get("model") or "Самолет",
                model=plane.get("model") or plane.get("name") or "Unknown",
                type_label=plane.get("typeLabel", "Пассажирский"),
                cabin_rows=cabin_rows,
                cabin_cols=cabin_cols,
                cabin_matrix=matrix,
                registration_number=plane.get("registrationNumber"),
            ))
        db.flush()

        for city in payload.get("cities", []):
            city_id = int(city["id"])
            code = str(city["code"]).upper()
            if city_id in seen_city_ids:
                raise HTTPException(status_code=400, detail=f"Duplicate city id: {city_id}")
            if code in seen_city_codes:
                raise HTTPException(status_code=400, detail=f"Duplicate city code: {code}")
            seen_city_ids.add(city_id)
            seen_city_codes.add(code)
            db.add(AirportCity(id=city_id, name=city["name"], code=code))
        db.flush()

        for plane in payload.get("planes", []):
            plane_id = int(plane["id"])
            matrix = plane.get("cabinMatrix") or []
            seen_seats_for_plane: set[str] = set()
            for row_index, row in enumerate(matrix):
                for col_index, cell in enumerate(row):
                    cell_type = cell.get("type", "economy") if isinstance(cell, dict) else "economy"
                    if cell_type in {"empty", "toilet"}:
                        continue
                    seat_number = _normalize_seat_number(row_index, col_index)
                    if seat_number in seen_seats_for_plane:
                        raise HTTPException(status_code=400, detail=f"Duplicate seat {seat_number} for plane {plane_id}")
                    seen_seats_for_plane.add(seat_number)
                    db.add(Seat(
                        airplane_id=plane_id,
                        seat_number=seat_number,
                        cabin_class_type=cell_type,
                    ))
        db.flush()

        for flight in payload.get("flights", []):
            flight_id = int(flight["id"])
            flight_number = str(flight["flightNumber"]).strip()
            airplane_id = int(flight.get("planeId", 101))
            if flight_id in seen_flight_ids:
                raise HTTPException(status_code=400, detail=f"Duplicate flight id: {flight_id}")
            if flight_number.lower() in seen_flight_numbers:
                raise HTTPException(status_code=400, detail=f"Duplicate flight number: {flight_number}")
            if airplane_id not in seen_plane_ids:
                raise HTTPException(status_code=400, detail=f"Flight {flight_number} references unknown plane {airplane_id}")
            seen_flight_ids.add(flight_id)
            seen_flight_numbers.add(flight_number.lower())
            db.add(Flight(
                id=flight_id,
                airplane_id=airplane_id,
                flight_number=flight_number,
                airline=flight["airline"],
                origin_city=flight["originCity"],
                origin_code=str(flight["originCode"]).upper(),
                destination_city=flight["destinationCity"],
                destination_code=str(flight["destinationCode"]).upper(),
                departure_date=flight["departureDate"],
                departure_time=flight["departureTime"],
                arrival_date=flight["arrivalDate"],
                arrival_time=flight["arrivalTime"],
                status=flight.get("status"),
                is_departure=bool(flight.get("isDeparture", True)),
                base_price=float(flight.get("basePrice", 6800)),
            ))
        db.flush()

        known_user_ids = {row[0] for row in db.query(User.id).all()}
        for passenger in payload.get("passengers", []):
            passenger_id = str(passenger["id"])
            if passenger_id in seen_passenger_ids:
                raise HTTPException(status_code=400, detail=f"Duplicate passenger id: {passenger_id}")
            seen_passenger_ids.add(passenger_id)
            user_id = passenger.get("userId")
            user_id = int(user_id) if user_id is not None else None
            if user_id is not None and user_id not in known_user_ids:
                user_id = None
            db.add(Passenger(
                id=passenger_id,
                user_id=user_id,
                surname=passenger["surname"],
                name=passenger["name"],
                patronymic=passenger.get("patronymic", ""),
                type=passenger.get("type", "adult"),
                doc_type=passenger.get("docType", "passport"),
                doc_number=passenger.get("docNumber", ""),
            ))
        db.flush()

        for ticket in payload.get("tickets", []):
            ticket_id = str(ticket["id"])
            flight_id = int(ticket["flightId"])
            seat_number = str(ticket.get("seatNumber") or "").strip().upper()
            passenger_id = str(ticket.get("passengerId") or "") or None
            user_id = ticket.get("userId")
            user_id = int(user_id) if user_id is not None else None

            if ticket_id in seen_ticket_ids:
                raise HTTPException(status_code=400, detail=f"Duplicate ticket id: {ticket_id}")
            if flight_id not in seen_flight_ids:
                raise HTTPException(status_code=400, detail=f"Ticket {ticket_id} references unknown flight {flight_id}")
            if passenger_id and passenger_id not in seen_passenger_ids:
                raise HTTPException(status_code=400, detail=f"Ticket {ticket_id} references unknown passenger {passenger_id}")
            if user_id is not None and user_id not in known_user_ids:
                user_id = None
            if not seat_number:
                raise HTTPException(status_code=400, detail=f"Ticket {ticket_id} has empty seat number")
            if (flight_id, seat_number) in seen_flight_seats:
                raise HTTPException(status_code=400, detail=f"Seat {seat_number} is duplicated for flight {flight_id}")

            flight_obj = db.query(Flight).filter(Flight.id == flight_id).first()
            seat = db.query(Seat).filter(
                Seat.airplane_id == flight_obj.airplane_id,
                Seat.seat_number == seat_number,
            ).first()
            if not seat:
                raise HTTPException(status_code=400, detail=f"Seat {seat_number} not found for flight {flight_id}")

            seen_ticket_ids.add(ticket_id)
            seen_flight_seats.add((flight_id, seat_number))
            db.add(Ticket(
                id=ticket_id,
                user_id=user_id,
                passenger_id=passenger_id,
                flight_id=flight_id,
                seat_id=seat.id,
                seat_number=seat_number,
                cabin_class=ticket.get("cabinClass") or seat.cabin_class_type,
                price=ticket.get("price"),
                created_at=ticket.get("createdAt"),
                is_used=bool(ticket.get("isUsed", ticket.get("is_used", False))),
            ))
        db.commit()
        return build_airport_data_from_sql(db)
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Could not save database snapshot: {exc}") from exc


def build_airport_data_from_sql(db: Session) -> dict[str, Any]:
    planes = [
        {
            "id": plane.id,
            "name": plane.name,
            "model": plane.model,
            "typeLabel": plane.type_label,
            "cabinRows": plane.cabin_rows,
            "cabinCols": plane.cabin_cols,
            "cabinMatrix": plane.cabin_matrix or [],
            **({"registrationNumber": plane.registration_number} if plane.registration_number else {}),
        }
        for plane in db.query(Airplane).order_by(Airplane.id).all()
    ]

    cities = [
        {"id": city.id, "name": city.name, "code": city.code}
        for city in db.query(AirportCity).order_by(AirportCity.id).all()
    ]

    flights = [
        {
            "id": flight.id,
            "planeId": flight.airplane_id,
            "flightNumber": flight.flight_number,
            "airline": flight.airline,
            "originCity": flight.origin_city,
            "originCode": flight.origin_code,
            "destinationCity": flight.destination_city,
            "destinationCode": flight.destination_code,
            "departureDate": flight.departure_date,
            "departureTime": flight.departure_time,
            "arrivalDate": flight.arrival_date,
            "arrivalTime": flight.arrival_time,
            "status": flight.status,
            "isDeparture": flight.is_departure,
            "basePrice": flight.base_price,
        }
        for flight in db.query(Flight).order_by(Flight.id).all()
    ]

    passengers = [
        {
            "id": passenger.id,
            "userId": passenger.user_id,
            "surname": passenger.surname,
            "name": passenger.name,
            "patronymic": passenger.patronymic or "",
            "type": passenger.type,
            "docType": passenger.doc_type,
            "docNumber": passenger.doc_number,
        }
        for passenger in db.query(Passenger).order_by(Passenger.surname, Passenger.name).all()
    ]

    tickets = []
    for ticket in db.query(Ticket).order_by(Ticket.booked_at.desc()).all():
        flight = ticket.flight
        passenger = ticket.passenger
        tickets.append({
            "id": ticket.id,
            "userId": ticket.user_id,
            "flightId": ticket.flight_id,
            "flightNumber": flight.flight_number if flight else "",
            "airline": flight.airline if flight else "",
            "departureDate": flight.departure_date if flight else "",
            "departureTime": flight.departure_time if flight else "",
            "arrivalDate": flight.arrival_date if flight else "",
            "arrivalTime": flight.arrival_time if flight else "",
            "origin": f"{flight.origin_city} {flight.origin_code}" if flight else "",
            "destination": f"{flight.destination_city} {flight.destination_code}" if flight else "",
            "passengerId": ticket.passenger_id or "",
            "passengerName": (f"{passenger.surname} {passenger.name} {passenger.patronymic or ''}".strip() if passenger else ""),
            "seatNumber": ticket.seat_number,
            "cabinClass": ticket.cabin_class,
            "price": ticket.price,
            "createdAt": ticket.created_at or (ticket.booked_at.isoformat() if ticket.booked_at else ""),
            "isUsed": bool(ticket.is_used),
        })

    users = [
        {"id": user.id, "email": user.email, "role": user.role}
        for user in db.query(User).order_by(User.id).all()
    ]

    return {
        "planes": planes,
        "cities": cities,
        "flights": flights,
        "passengers": passengers,
        "tickets": tickets,
        "users": users,
    }
