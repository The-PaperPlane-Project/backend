from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text
from src.database import Base, SessionLocal, engine
from src.models import *
from src.routes import airplane, auth, city, flight, passenger, seat, ticket, user, user_details
from src.routes import data_file
from src.routes.admin import airplane as admin_airplane
from src.routes.admin import city as admin_city
from src.routes.admin import cabin_template as admin_cabin_template
from src.routes.admin import flight as admin_flight
from src.routes.admin import seat as admin_seat
from src.routes.admin import ticket as admin_ticket
from src.routes.admin import user as admin_user
from src.services.data_file import seed_sql_from_json

app = FastAPI(title="Paper Plane Airport API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

with engine.begin() as connection:
    ticket_columns = {column["name"] for column in inspect(connection).get_columns("tickets")}
    if "is_used" not in ticket_columns:
        connection.execute(text("ALTER TABLE tickets ADD COLUMN is_used BOOLEAN NOT NULL DEFAULT 0"))

with SessionLocal() as db:
    seed_sql_from_json(db)

app.include_router(data_file.router)
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(user_details.router)
app.include_router(passenger.router)
app.include_router(city.router)
app.include_router(airplane.router)
app.include_router(seat.router)
app.include_router(flight.router)
app.include_router(ticket.router)

app.include_router(admin_airplane.router)
app.include_router(admin_city.router)
app.include_router(admin_seat.router)
app.include_router(admin_flight.router)
app.include_router(admin_ticket.router)
app.include_router(admin_user.router)
app.include_router(admin_cabin_template.router)


@app.get("/")
def root():
    return {
        "message": "Paper Plane API работает",
        "docs": "/docs",
        "database_file": "/api/database",
    }
