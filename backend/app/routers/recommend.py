import logging
import time
from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.data_loader import load_recommendation_places
from app.services.route import recommend_route

router = APIRouter(prefix="/api/recommend", tags=["recommend"])
logger = logging.getLogger("recommend")


class RecommendRequest(BaseModel):
    start_lat: float
    start_lon: float
    categories: Optional[List[str]] = None
    stop_count: int = Field(default=5, ge=3, le=5)
    max_minutes: Optional[int] = Field(default=None, ge=1)


@router.post("")
def recommend(req: RecommendRequest):
    t0 = time.perf_counter()
    result = recommend_route(
        catalog=load_recommendation_places(),
        start_lat=req.start_lat,
        start_lon=req.start_lon,
        categories=req.categories,
        stop_count=req.stop_count,
        max_minutes=req.max_minutes,
    )
    elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
    logger.info(
        "recommend start=(%.5f,%.5f) categories=%s stop_count=%d -> %d stops in %sms",
        req.start_lat, req.start_lon, req.categories, req.stop_count, len(result["stops"]), elapsed_ms,
    )
    return result
