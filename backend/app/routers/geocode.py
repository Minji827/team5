"""사용자가 출발지를 주소/장소명으로 검색할 수 있게, Kakao 키워드 검색 API를 프록시한다.
프론트에 Kakao 키를 노출하지 않으려고 백엔드를 거친다."""

import os

import requests
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException

load_dotenv()

router = APIRouter(prefix="/api/geocode", tags=["geocode"])

KAKAO_KEY = os.environ.get("KAKAO_REST_API_KEY")
KAKAO_KEYWORD_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"


@router.get("")
def search_location(query: str):
    if not KAKAO_KEY:
        raise HTTPException(500, "KAKAO_REST_API_KEY가 설정되어 있지 않습니다.")

    resp = requests.get(
        KAKAO_KEYWORD_URL,
        params={"query": query, "size": 5},
        headers={"Authorization": f"KakaoAK {KAKAO_KEY}"},
        timeout=5,
    )
    resp.raise_for_status()
    data = resp.json()

    return {
        "results": [
            {
                "name": d["place_name"],
                "address": d.get("road_address_name") or d.get("address_name"),
                "lon": float(d["x"]),
                "lat": float(d["y"]),
            }
            for d in data.get("documents", [])
        ]
    }
