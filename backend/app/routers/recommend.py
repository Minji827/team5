import logging
import time
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.data_loader import load_recommendation_places, load_places, DATA_DIR
import pandas as pd
from app.services.route import recommend_route, recalculate_route
from app.services.walking import WalkingError

router = APIRouter(prefix="/api/recommend", tags=["recommend"])
logger = logging.getLogger("recommend")


class RecommendRequest(BaseModel):
    start_lat: float = Field(ge=-90, le=90)
    start_lon: float = Field(ge=-180, le=180)
    categories: Optional[List[str]] = None
    stop_count: int = Field(default=5, ge=3, le=5)
    max_minutes: Optional[int] = Field(default=None, ge=1)


def timed_catalog():
    catalog = load_recommendation_places().copy()
    places = load_places().set_index("id")
    rules = pd.read_csv(DATA_DIR / "place_support/duration_rules.csv", skipinitialspace=True).set_index("visit_type")
    # shortcut: untyped legacy places use category defaults until the curated catalog is complete.
    defaults = {"식당": "general_restaurant", "카페·디저트": "seated_cafe",
                "쇼핑": "general_shopping", "관광명소": "scenic_spot"}
    types = catalog.category.map(defaults).mask(catalog.place_type.eq("market"), "traditional_market")
    catalog["duration_min"] = types.map(rules.duration_min)
    catalog["duration_basis"] = "category_default"
    for i, row in catalog.iterrows():
        if row["id"] in places.index:
            catalog.at[i, "duration_min"] = places.at[row["id"], "duration_min"]
            catalog.at[i, "duration_basis"] = "place_default"
    return catalog


class RecalculateRequest(BaseModel):
    start_lat: float = Field(ge=-90, le=90)
    start_lon: float = Field(ge=-180, le=180)
    stop_ids: List[str] = Field(min_length=1, max_length=5)
    max_minutes: Optional[int] = Field(default=None, ge=1)


@router.post("/recalculate")
def recalculate(req: RecalculateRequest):
    catalog = timed_catalog().set_index("id")
    if len(set(req.stop_ids)) != len(req.stop_ids) or any(i not in catalog.index for i in req.stop_ids):
        raise HTTPException(422, "유효한 장소 ID를 중복 없이 선택해주세요.")
    from app.services.route import _place_fields
    stops = [_place_fields({**catalog.loc[i].to_dict(), "id": i}) for i in req.stop_ids]
    try:
        return recalculate_route(req.start_lat, req.start_lon, stops, req.max_minutes)
    except WalkingError as exc:
        raise HTTPException(502, str(exc)) from None


@router.post("")
def recommend(req: RecommendRequest):
    t0 = time.perf_counter()
    try:
        result = recommend_route(
            catalog=timed_catalog(),
            start_lat=req.start_lat,
            start_lon=req.start_lon,
            categories=req.categories,
            stop_count=req.stop_count,
            max_minutes=req.max_minutes,
        )
    except WalkingError as exc:
        raise HTTPException(502, str(exc)) from None
    elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
    logger.info(
        "recommend start=(%.5f,%.5f) categories=%s stop_count=%d -> %d stops in %sms",
        req.start_lat, req.start_lon, req.categories, req.stop_count, len(result["stops"]), elapsed_ms,
    )
    return result
