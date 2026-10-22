import logging
import time
from typing import List, Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.data_loader import load_places
from app.services.route import recommend_route, recalculate_route, RouteConstraintError
from app.services.walking import WalkingError

router = APIRouter(prefix="/api/recommend", tags=["recommend"])
logger = logging.getLogger("recommend")


class RecommendRequest(BaseModel):
    start_lat: float = Field(ge=-90, le=90)
    start_lon: float = Field(ge=-180, le=180)
    return_to_start: bool = False
    selected_only: bool = False
    categories: Optional[List[Literal["식당", "카페/디저트", "카페·디저트", "관광명소", "쇼핑"]]] = None
    max_minutes: int = Field(default=90, ge=30, le=360)


class RecalculateRequest(BaseModel):
    start_lat: float = Field(ge=-90, le=90)
    start_lon: float = Field(ge=-180, le=180)
    return_to_start: bool = False
    stop_ids: List[str] = Field(min_length=1, max_length=24)
    max_minutes: int = Field(default=90, ge=30, le=360)


@router.post("/recalculate")
def recalculate(req: RecalculateRequest):
    catalog = load_places().set_index("id")
    if len(set(req.stop_ids)) != len(req.stop_ids) or any(i not in catalog.index for i in req.stop_ids):
        raise HTTPException(422, "유효한 장소 ID를 중복 없이 선택해주세요.")
    from app.services.route import _place_fields
    stops = [_place_fields({**catalog.loc[i].to_dict(), "id": i}) for i in req.stop_ids]
    try:
        result = recalculate_route(req.start_lat, req.start_lon, stops, req.max_minutes, req.return_to_start)
        if result["over_budget"]:
            raise HTTPException(422, "이 장소로 바꾸면 여행 시간을 초과해요. 다른 장소를 선택해주세요.")
        return result
    except RouteConstraintError as exc:
        raise HTTPException(422, str(exc)) from None
    except WalkingError as exc:
        raise HTTPException(502, str(exc)) from None


@router.post("")
def recommend(req: RecommendRequest):
    t0 = time.perf_counter()
    try:
        result = recommend_route(
            catalog=load_places(),
            start_lat=req.start_lat,
            start_lon=req.start_lon,
            categories=req.categories,
            max_minutes=req.max_minutes,
            return_to_start=req.return_to_start,
            selected_only=req.selected_only,
        )
    except RouteConstraintError as exc:
        raise HTTPException(422, str(exc)) from None
    except WalkingError as exc:
        raise HTTPException(502, str(exc)) from None
    elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
    logger.info(
        "recommend start=(%.5f,%.5f) categories=%s max_minutes=%d -> %d stops in %sms",
        req.start_lat, req.start_lon, req.categories, req.max_minutes, len(result["stops"]), elapsed_ms,
    )
    return result
