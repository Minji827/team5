"""TMAP pedestrian routing. Credentials stay on the backend."""
import math
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[3] / ".env")


class WalkingError(Exception):
    pass


def walking_leg(start_lat, start_lon, end_lat, end_lon):
    key = os.getenv("TMAP_APP_KEY")
    if not key:
        raise WalkingError("TMAP 키가 설정되어 있지 않습니다.")
    if (start_lat, start_lon) == (end_lat, end_lon):
        return {"leg_minutes": 0, "leg_distance_m": 0, "leg_path": []}
    try:
        response = requests.post(
            "https://apis.openapi.sk.com/tmap/routes/pedestrian",
            params={"version": "1"},
            headers={"appKey": key},
            json={"startX": start_lon, "startY": start_lat,
                  "endX": end_lon, "endY": end_lat,
                  "startName": "start", "endName": "end",
                  "reqCoordType": "WGS84GEO", "resCoordType": "WGS84GEO"},
            timeout=10,
        )
        if response.status_code in (401, 403):
            raise WalkingError("TMAP 인증에 실패했습니다. 앱 키와 TMAP 상품 연결 상태를 확인해주세요.")
        if response.status_code == 429:
            raise WalkingError("TMAP 호출 한도를 초과했습니다. 잠시 후 다시 시도해주세요.")
        response.raise_for_status()
        features = response.json()["features"]
        summary = next(f["properties"] for f in features if "totalTime" in f.get("properties", {}))
        seconds, distance = float(summary["totalTime"]), float(summary["totalDistance"])
        if not all(math.isfinite(v) and v >= 0 for v in (seconds, distance)):
            raise ValueError("Invalid routing summary")
        path = []
        for feature in features:
            geometry = feature.get("geometry", {})
            if geometry.get("type") == "LineString":
                path.extend([[lat, lon] for lon, lat in geometry["coordinates"]])
        return {"leg_minutes": round(seconds / 60, 1), "leg_distance_m": distance, "leg_path": path}
    except WalkingError:
        raise
    except (requests.RequestException, ValueError, KeyError, TypeError, StopIteration):
        # Never forward upstream exceptions/headers containing credentials.
        raise WalkingError("TMAP 도보 경로를 계산하지 못했습니다. 잠시 후 다시 시도해주세요.") from None
