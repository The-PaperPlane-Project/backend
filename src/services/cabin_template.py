from collections import defaultdict
from typing import List
from fastapi import HTTPException
from sqlalchemy.orm import joinedload
from src.schemas.cabin_template import CabinTemplateCreate, CabinTemplateResponse
from src.schemas.seat import SeatResponse
from src.models.airplane import Airplane
from src.models.cabin_template import CabinTemplate
from src.models.cabin_class import CabinClass
from src.models.seat import Seat
from src.repositories.cabin_template import CabinTemplateRepository
from src.repositories.cabin_class import CabinClassRepository
from src.repositories.seat import SeatRepository


class CabinTemplateService:
    def __init__(
        self,
        template_repo: CabinTemplateRepository,
        cabin_class_repo: CabinClassRepository,
        seat_repo: SeatRepository,
    ):
        self.template_repo = template_repo
        self.cabin_class_repo = cabin_class_repo
        self.seat_repo = seat_repo

    def create_template(self, data: CabinTemplateCreate) -> CabinTemplateResponse:
        existing = self.template_repo.db.query(CabinTemplate).filter(CabinTemplate.name == data.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Cabin template with this name already exists")
        template = CabinTemplate(name=data.name, number_of_aisles=data.number_of_aisles)
        template = self.template_repo.create(template)

        for class_data in data.classes:
            cabin_class = CabinClass(
                template_id=template.id,
                class_type=class_data.class_type,
                rows=class_data.rows,
                seats_per_row=class_data.seats_per_row,
                order=class_data.order,
            )
            self.cabin_class_repo.create(cabin_class)

        template = self.template_repo.get(template.id)
        return CabinTemplateResponse.model_validate(template)

    def generate_seats(self, template_id: int, airplane_id: int) -> List[SeatResponse]:
        template = self.template_repo.get(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        airplane = self.seat_repo.db.query(Airplane).filter(Airplane.id == airplane_id).first()
        if not airplane:
            raise HTTPException(status_code=404, detail="Airplane not found")

        self.seat_repo.db.query(Seat).filter(Seat.airplane_id == airplane_id).delete()
        self.seat_repo.db.commit()

        seats = []
        for cabin_class in template.classes:
            for row in range(1, cabin_class.rows + 1):
                for seat_in_row in range(1, cabin_class.seats_per_row + 1):
                    prefix = cabin_class.class_type[0].upper()
                    seat_number = f"{prefix}{row}{chr(64 + seat_in_row)}"
                    seat = Seat(
                        airplane_id=airplane_id,
                        seat_number=seat_number,
                        cabin_class_id=cabin_class.id,
                        cabin_class_type=cabin_class.class_type,
                    )
                    seats.append(seat)
        self.seat_repo.bulk_create(seats)
        return [SeatResponse.model_validate(s) for s in seats]

    def visualize(self, template_id: int, airplane_id: int = None) -> dict:
        template = self.template_repo.get(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        if airplane_id:
            seats = (
                self.seat_repo.db.query(Seat)
                .options(joinedload(Seat.cabin_class))
                .filter(Seat.airplane_id == airplane_id)
                .order_by(Seat.seat_number)
                .all()
            )
            schema = self._build_schema_from_seats(seats, template.number_of_aisles)
        else:
            schema = self._build_schema_from_template(template)
        return schema

    def _build_schema_from_template(self, template: CabinTemplate) -> dict:
        schema = {"template_name": template.name, "aisles": template.number_of_aisles, "classes": []}
        for cabin_class in sorted(template.classes, key=lambda c: c.order):
            rows = []
            for row_num in range(1, cabin_class.rows + 1):
                row_seats = []
                for seat_num in range(1, cabin_class.seats_per_row + 1):
                    prefix = cabin_class.class_type[0].upper()
                    seat_name = f"{prefix}{row_num}{chr(64 + seat_num)}"
                    row_seats.append(seat_name)
                rows.append({"row_number": row_num, "seats": row_seats})
            schema["classes"].append({"class_type": cabin_class.class_type, "rows": rows})
        return schema

    def _build_schema_from_seats(self, seats: List[Seat], aisles: int) -> dict:
        by_class = defaultdict(list)
        for seat in seats:
            if seat.cabin_class:
                by_class[seat.cabin_class].append(seat)

        classes_schema = []
        sorted_classes = sorted(by_class.items(), key=lambda item: item[0].order)
        for cabin_class, class_seats in sorted_classes:
            by_row = defaultdict(list)
            for seat in class_seats:
                prefix = cabin_class.class_type[0].upper()
                number_part = seat.seat_number[len(prefix):]
                row_str = ""
                col_str = ""
                for ch in number_part:
                    if ch.isdigit():
                        row_str += ch
                    else:
                        col_str += ch
                row_num = int(row_str) if row_str else 0
                by_row[row_num].append(col_str)

            rows_schema = []
            for row_num in sorted(by_row.keys()):
                seats_in_row = sorted(by_row[row_num])
                rows_schema.append({
                    "row_number": row_num,
                    "seats": [f"{prefix}{row_num}{col}" for col in seats_in_row],
                })
            classes_schema.append({
                "class_type": cabin_class.class_type,
                "rows": rows_schema,
            })

        return {"aisles": aisles, "classes": classes_schema}
