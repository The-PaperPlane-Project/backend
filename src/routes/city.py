from fastapi import APIRouter, Depends
from src.dependencies import get_airport_city_repo
from src.schemas.airport_city import AirportCityResponse

router = APIRouter(prefix="/cities", tags=["cities"])


@router.get("/", response_model=list[AirportCityResponse])
def list_cities(repo=Depends(get_airport_city_repo)):
    return [AirportCityResponse.model_validate(city) for city in repo.get_all()]
