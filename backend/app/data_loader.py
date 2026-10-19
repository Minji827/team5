"""data/processed/*.csv 를 읽어 메모리에 캐싱한다.

나중에 Supabase/DB로 옮길 때는 이 모듈의 반환값(DataFrame)만 맞춰주면
services/routers 쪽은 그대로 쓸 수 있도록 데이터 접근을 여기 한 곳으로 모은다.
"""

from functools import lru_cache
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"


@lru_cache(maxsize=1)
def load_merchants() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "merchants.csv", encoding="utf-8-sig")


@lru_cache(maxsize=1)
def load_tourist_spots() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "tourist_spots.csv", encoding="utf-8-sig")


@lru_cache(maxsize=1)
def load_consumption() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "consumption.csv", encoding="utf-8-sig")


@lru_cache(maxsize=1)
def load_visitors() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "visitors.csv", encoding="utf-8-sig")


@lru_cache(maxsize=1)
def load_commercial_density() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "commercial_density.csv", encoding="utf-8-sig")


@lru_cache(maxsize=1)
def load_sangga_points() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "sangga_points.csv", encoding="utf-8-sig")
