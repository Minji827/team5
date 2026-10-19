from typing import Optional

from fastapi import APIRouter

from app.data_loader import load_tourist_spots
from app.services.route import CATEGORIES

router = APIRouter(prefix="/api/spots", tags=["spots"])


@router.get("")
def list_spots(category: Optional[str] = None):
    df = load_tourist_spots().copy()
    if category:
        df = df[df["category_major"] == category]
    return df.astype(object).where(df.notna(), None).to_dict(orient="records")


@router.get("/categories")
def list_categories():
    return CATEGORIES
