from fastapi import APIRouter, HTTPException

from app.data_loader import load_merchants
from app.services.geo import within_radius

router = APIRouter(prefix="/api/merchants", tags=["merchants"])

MAX_RADIUS_M = 3000
MAX_RESULTS = 200


@router.get("")
def nearby_merchants(lat: float, lon: float, radius_m: int = 500):
    if radius_m > MAX_RADIUS_M:
        raise HTTPException(400, f"radius_m은 {MAX_RADIUS_M}m 이하로 요청해주세요.")

    df = load_merchants()
    nearby = within_radius(df, lat, lon, radius_m).head(MAX_RESULTS)
    return nearby.astype(object).where(nearby.notna(), None).to_dict(orient="records")
