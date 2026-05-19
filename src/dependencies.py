from fastapi import Depends
from src.database import SessionLocal
from src.repositories.airplane import AirplaneRepository
from src.repositories.airport_city import AirportCityRepository
from src.repositories.cabin_class import CabinClassRepository
from src.repositories.cabin_template import CabinTemplateRepository
from src.repositories.flight import FlightRepository
from src.repositories.passenger import PassengerRepository
from src.repositories.seat import SeatRepository
from src.repositories.ticket import TicketRepository
from src.repositories.user import UserRepository
from src.repositories.user_details import UserDetailsRepository
from src.services.airplane import AirplaneService
from src.services.auth import AuthService, oauth2_scheme
from src.services.cabin_template import CabinTemplateService
from src.services.flight import FlightService
from src.services.seat import SeatService
from src.services.ticket import TicketService
from src.services.user import UserService
from src.services.user_details import UserDetailsService
from src.models.user import User


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_repo(db=Depends(get_db)):
    return UserRepository(db)


def get_user_details_repo(db=Depends(get_db)):
    return UserDetailsRepository(db)


def get_airplane_repo(db=Depends(get_db)):
    return AirplaneRepository(db)


def get_airport_city_repo(db=Depends(get_db)):
    return AirportCityRepository(db)


def get_seat_repo(db=Depends(get_db)):
    return SeatRepository(db)


def get_flight_repo(db=Depends(get_db)):
    return FlightRepository(db)


def get_ticket_repo(db=Depends(get_db)):
    return TicketRepository(db)


def get_passenger_repo(db=Depends(get_db)):
    return PassengerRepository(db)


def get_cabin_template_repo(db=Depends(get_db)):
    return CabinTemplateRepository(db)


def get_cabin_class_repo(db=Depends(get_db)):
    return CabinClassRepository(db)


def get_user_service(user_repo=Depends(get_user_repo)):
    return UserService(user_repo)


def get_user_details_service(details_repo=Depends(get_user_details_repo)):
    return UserDetailsService(details_repo)


def get_airplane_service(airplane_repo=Depends(get_airplane_repo)):
    return AirplaneService(airplane_repo)


def get_seat_service(seat_repo=Depends(get_seat_repo)):
    return SeatService(seat_repo)


def get_flight_service(
    flight_repo=Depends(get_flight_repo),
    seat_repo=Depends(get_seat_repo),
    ticket_repo=Depends(get_ticket_repo),
):
    return FlightService(flight_repo, seat_repo, ticket_repo)


def get_ticket_service(
    ticket_repo=Depends(get_ticket_repo),
    seat_repo=Depends(get_seat_repo),
    flight_repo=Depends(get_flight_repo),
):
    return TicketService(ticket_repo, seat_repo, flight_repo)


def get_cabin_template_service(
    template_repo=Depends(get_cabin_template_repo),
    class_repo=Depends(get_cabin_class_repo),
    seat_repo=Depends(get_seat_repo),
):
    return CabinTemplateService(template_repo, class_repo, seat_repo)


def get_auth_service(user_repo=Depends(get_user_repo)):
    return AuthService(user_repo)


def get_current_user(auth_service: AuthService = Depends(get_auth_service), token: str = Depends(oauth2_scheme)) -> User:
    return auth_service.get_current_user(token)


def get_current_admin(auth_service: AuthService = Depends(get_auth_service), token: str = Depends(oauth2_scheme)) -> User:
    return auth_service.get_current_admin(token)
