import os
import smtplib
from email.message import EmailMessage
from pathlib import Path
from src.models.ticket import Ticket


class BookingEmailService:
    def __init__(self) -> None:
        self.smtp_host = os.getenv("MAIL_SMTP_HOST", "").strip()
        self.smtp_port = int(os.getenv("MAIL_SMTP_PORT", "587"))
        self.smtp_username = os.getenv("MAIL_SMTP_USERNAME", "").strip()
        self.smtp_password = os.getenv("MAIL_SMTP_PASSWORD", "").strip()
        self.from_email = os.getenv("MAIL_FROM_EMAIL", self.smtp_username).strip()
        self.from_name = os.getenv("MAIL_FROM_NAME", "Paper Plane").strip()
        self.use_ssl = os.getenv("MAIL_SMTP_USE_SSL", "false").lower() == "true"
        self.use_starttls = os.getenv("MAIL_SMTP_STARTTLS", "true").lower() == "true"
        self.outbox_dir = Path(os.getenv("MAIL_OUTBOX_DIR", "./data/outbox"))
        self.raise_on_error = os.getenv("MAIL_RAISE_ON_ERROR", "false").lower() == "true"

    def send_booking_confirmation(self, ticket: Ticket) -> None:
        recipient = ticket.user.email if ticket.user else ""
        if not recipient:
            return

        message = self._build_message(ticket, recipient)
        try:
            if self.smtp_host and self.from_email:
                self._send_smtp(message)
            else:
                self._save_to_outbox(message, ticket.id)
        except Exception:
            if self.raise_on_error:
                raise

    def _build_message(self, ticket: Ticket, recipient: str) -> EmailMessage:
        flight = ticket.flight
        passenger = ticket.passenger
        passenger_name = ""
        if passenger:
            passenger_name = f"{passenger.surname} {passenger.name} {passenger.patronymic or ''}".strip()

        subject = f"Paper Plane: ticket {ticket.id}"
        route = ""
        if flight:
            route = f"{flight.origin_city} ({flight.origin_code}) - {flight.destination_city} ({flight.destination_code})"

        lines = [
            "Your ticket has been booked.",
            "",
            f"Ticket: {ticket.id}",
            f"Passenger: {passenger_name or 'Not specified'}",
            f"Flight: {flight.flight_number if flight else ticket.flight_id}",
            f"Route: {route or 'Not specified'}",
            f"Departure: {flight.departure_date if flight else ''} {flight.departure_time if flight else ''}".strip(),
            f"Arrival: {flight.arrival_date if flight else ''} {flight.arrival_time if flight else ''}".strip(),
            f"Seat: {ticket.seat_number or 'Not specified'}",
            f"Class: {ticket.cabin_class or 'Not specified'}",
            f"Price: {ticket.price if ticket.price is not None else 'Not specified'}",
        ]

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = f"{self.from_name} <{self.from_email}>" if self.from_email else self.from_name
        message["To"] = recipient
        message.set_content("\n".join(lines))
        return message

    def _send_smtp(self, message: EmailMessage) -> None:
        smtp_class = smtplib.SMTP_SSL if self.use_ssl else smtplib.SMTP
        with smtp_class(self.smtp_host, self.smtp_port, timeout=15) as server:
            if self.use_starttls and not self.use_ssl:
                server.starttls()
            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)
            server.send_message(message)

    def _save_to_outbox(self, message: EmailMessage, ticket_id: str) -> None:
        self.outbox_dir.mkdir(parents=True, exist_ok=True)
        safe_ticket_id = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in ticket_id)
        (self.outbox_dir / f"{safe_ticket_id}.eml").write_text(message.as_string(), encoding="utf-8")
