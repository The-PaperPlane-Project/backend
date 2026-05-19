from fastapi import APIRouter, Depends, HTTPException
from src.dependencies import get_airport_city_repo, get_current_admin
from src.models.airport_city import AirportCity
from src.models.flight import Flight
from src.schemas.airport_city import AirportCityCreate, AirportCityResponse

router = APIRouter(prefix="/admin/cities", tags=["admin-cities"])


def _normalize_code(code: str) -> str:
    return code.strip().upper()


@router.post("/", response_model=AirportCityResponse)
def create_city(data: AirportCityCreate, repo=Depends(get_airport_city_repo), admin=Depends(get_current_admin)):
    name = data.name.strip()
    code = _normalize_code(data.code)
    if not name or not code:
        raise HTTPException(status_code=400, detail="City name and code are required")
    if repo.db.query(AirportCity).filter(AirportCity.code == code).first():
        raise HTTPException(status_code=400, detail="City with this airport code already exists")
    if repo.db.query(AirportCity).filter(AirportCity.name.ilike(name)).first():
        raise HTTPException(status_code=400, detail="City with this name already exists")
    city = AirportCity(name=name, code=code)
    return AirportCityResponse.model_validate(repo.create(city))


@router.delete("/{city_id}")
def delete_city(city_id: int, repo=Depends(get_airport_city_repo), admin=Depends(get_current_admin)):
    city = repo.get(city_id)
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
    if city.code.upper() == "KUF":
        raise HTTPException(status_code=400, detail="Base airport city cannot be deleted")
    used = repo.db.query(Flight).filter(
        (Flight.origin_code == city.code) | (Flight.destination_code == city.code)
    ).first()
    if used:
        raise HTTPException(status_code=400, detail="City is used in flights")
    repo.delete(city_id)
    return {"status": "ok"}
