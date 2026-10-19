"""좌표 관련 유틸: haversine 거리, bbox 1차 필터, 최근접 탐색."""

import math

import numpy as np
import pandas as pd

EARTH_RADIUS_M = 6371000


def haversine_m(lat1, lon1, lat2, lon2):
    """두 좌표(도) 사이 거리(미터). 벡터(np.array) 입력도 지원."""
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_M * np.arcsin(np.sqrt(a))


def bbox_filter(df: pd.DataFrame, lat, lon, radius_m, lat_col="lat", lon_col="lon") -> pd.DataFrame:
    """정밀 haversine 계산 전에 위경도 bbox로 1차로 걸러서 비용을 줄인다."""
    deg_margin = radius_m / 111_000  # 위도 1도 ~= 111km, 대략치로 충분
    return df[
        (df[lat_col] >= lat - deg_margin) & (df[lat_col] <= lat + deg_margin)
        & (df[lon_col] >= lon - deg_margin) & (df[lon_col] <= lon + deg_margin)
    ]


def within_radius(df: pd.DataFrame, lat, lon, radius_m, lat_col="lat", lon_col="lon") -> pd.DataFrame:
    """주어진 지점 반경 radius_m 이내 행만 반환 (distance_m 컬럼 추가, 가까운 순 정렬)."""
    candidates = bbox_filter(df, lat, lon, radius_m, lat_col, lon_col).copy()
    if candidates.empty:
        candidates["distance_m"] = []
        return candidates
    candidates["distance_m"] = haversine_m(lat, lon, candidates[lat_col].to_numpy(), candidates[lon_col].to_numpy())
    return candidates[candidates["distance_m"] <= radius_m].sort_values("distance_m")


def nearest_row(df: pd.DataFrame, lat, lon, lat_col="lat", lon_col="lon"):
    """df에서 (lat, lon)에 가장 가까운 한 행을 반환."""
    distances = haversine_m(lat, lon, df[lat_col].to_numpy(), df[lon_col].to_numpy())
    idx = np.argmin(distances)
    return df.iloc[idx]
