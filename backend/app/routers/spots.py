from typing import Optional

from fastapi import APIRouter

from app.data_loader import load_places

router = APIRouter(prefix="/api/spots", tags=["spots"])


@router.get("")
def list_spots(category: Optional[str] = None):
    df = load_places()
    df = df[df["category"] == "관광명소"]
    if category:
        df = df[df["category"] == category]
    return df.astype(object).where(df.notna(), None).to_dict(orient="records")


@router.get("/categories")
def list_categories():
    return ["식당", "카페/디저트", "관광명소", "쇼핑"]
