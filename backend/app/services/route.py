"""부산페이 도보 루트 추천 로직 (순수 함수들).

PRD 기준: 소비/방문자 데이터는 권역 선정 근거용일 뿐 실시간 추천에는 쓰지 않는다.
ML 없이 필터(카테고리/거리) + 경로는 전수비교(순열)로 구한다.

흐름: merchants(동백전=결제확인) x tourist_spots(카테고리) 근접 매칭으로 카탈로그 생성
     -> 카테고리/거리로 후보 K개 선정 -> 전수비교로 도보시간 최소 순서 결정
"""

import itertools
import re

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from app.services.geo import haversine_m, within_radius

SANGGA_MATCH_RADIUS_M = 150  # 상호 "완전일치"가 기준이라 반경을 넓혀도 오매칭 위험이 낮음
MARKET_MATCH_RADIUS_M = 50
WALK_SPEED_MPS = 4.5 * 1000 / 3600  # 4.5km/h
WALK_DISTANCE_FACTOR = 1.3  # 직선거리 보정계수 (실제 보행로는 직선보다 김)

CATEGORIES = ["카페", "식당", "기념품", "시장"]

# 부산 대략 중심 위도 기준으로 경위도를 평면 좌표(m)로 근사 변환 (KD-tree 공간탐색용)
_LAT0 = 35.18
_M_PER_DEG_LAT = 111320
_M_PER_DEG_LON = 111320 * np.cos(np.radians(_LAT0))


def _to_xy(lat, lon):
    return lon * _M_PER_DEG_LON, lat * _M_PER_DEG_LAT


# "소매" 대분류를 통째로 기념품 취급했더니 약국/편의점/슈퍼까지 다 기념품으로 잡혔다.
# 한국표준산업분류엔 "기념품점"이라는 코드가 따로 없어서 완벽한 매핑은 불가능하지만,
# 장식품/시계·귀금속 소매 정도가 그나마 관광객 기념품 구매와 제일 가깝다.
GIFT_SHOP_MINORS = {"장식품 소매", "시계·귀금속 소매"}


def _sangga_category(category_major, category_minor):
    if category_major == "음식":
        return "카페" if category_minor == "비알코올" else "식당"
    if category_minor in GIFT_SHOP_MINORS:
        return "기념품"
    return None


def _kakao_category(category_group_name, category_name):
    """카카오 자체 업종분류. "시장"은 상호명에 흔히 섞여 오매칭이 나서
    (예: "OO스쿼시장") 여기선 다루지 않고 전통시장 반경 매칭에 맡긴다."""
    if category_group_name == "카페":
        return "카페"
    if category_group_name == "음식점":
        return "식당"
    if isinstance(category_name, str) and category_name.startswith("여행 > 기념품"):
        return "기념품"
    return None


_BRANCH_SUFFIX_RE = re.compile(r"(점|지점|호점)$")
_PAREN_RE = re.compile(r"\(.*?\)")
_NON_ALNUM_RE = re.compile(r"[^0-9a-zA-Z가-힣]")


def _normalize_name(name) -> str:
    """괄호 안 내용, 특수문자/공백, 끝의 '점/지점/호점'을 지워서 표기만 다른
    같은 상호를 더 많이 잡는다 (예: "본죽(서면점)" == "본죽 서면"). 그래도
    여전히 "완전 일치"만 허용해서 지점명 부분일치로 인한 오매칭은 재발하지 않는다."""
    s = _PAREN_RE.sub("", str(name))
    s = _NON_ALNUM_RE.sub("", s)
    s = _BRANCH_SUFFIX_RE.sub("", s)
    return s


def _name_matches(merchant_name, other_name) -> bool:
    """좌표만으로 매칭하면 근처의 상관없는 가게를 잘못 묶는 경우가 많아서,
    실제로 같은 상호인지 반드시 같이 확인한다.

    처음엔 부분 포함(in)으로 했었는데, "OO 구포시장점"/"OO 동래시장점"처럼
    서로 다른 업종인데 지점명(동네 이름)만 겹쳐도 매칭돼버리는 오매칭이 생겨서
    완전히 같은 상호명일 때만 매칭하는 걸로 엄격하게 바꿨다."""
    a, b = _normalize_name(merchant_name), _normalize_name(other_name)
    if len(a) < 2:
        return False
    return a == b


_catalog_cache = None


def estimate_walk_minutes(distance_m):
    return distance_m * WALK_DISTANCE_FACTOR / WALK_SPEED_MPS / 60


def _match_via_sangga(merchants_df: pd.DataFrame, sangga_df: pd.DataFrame) -> list:
    """카페/식당/기념품은 상가(상권)정보가 TourAPI보다 훨씬 촘촘해서 이쪽으로 매칭한다.
    merchants x sangga 둘 다 15만건대라 전수탐색은 느려서 KD-tree로 반경 검색만 하고,
    실제 매칭 확정은 상호명이 일치하는지로 한다 (좌표만 믿으면 오매칭이 많음)."""
    sangga = sangga_df.copy()
    sangga["category"] = [
        _sangga_category(mj, mn) for mj, mn in zip(sangga["category_major"], sangga["category_minor"])
    ]
    sangga = sangga.dropna(subset=["category"]).reset_index(drop=True)

    sx, sy = _to_xy(sangga["lat"].to_numpy(), sangga["lon"].to_numpy())
    tree = cKDTree(np.column_stack([sx, sy]))

    mx, my = _to_xy(merchants_df["lat"].to_numpy(), merchants_df["lon"].to_numpy())
    neighbor_lists = tree.query_ball_point(np.column_stack([mx, my]), r=SANGGA_MATCH_RADIUS_M, workers=-1)

    sangga_names = sangga["name"].to_numpy()
    sangga_categories = sangga["category"].to_numpy()
    merchants = merchants_df.reset_index(drop=True)

    rows = []
    for i, idxs in enumerate(neighbor_lists):
        if len(idxs) == 0:
            continue
        merchant_name = merchants.at[i, "name"]
        for j in idxs:
            if _name_matches(merchant_name, sangga_names[j]):
                rows.append({
                    "id": merchants.at[i, "id"],
                    "name": merchant_name,
                    "address": merchants.at[i, "address"],
                    "lon": merchants.at[i, "lon"],
                    "lat": merchants.at[i, "lat"],
                    "category": sangga_categories[j],
                    "data_date": merchants.at[i, "data_date"],
                })
                break
    return rows


def _match_via_traditional_market(merchants_df: pd.DataFrame, spots_df: pd.DataFrame) -> list:
    """시장은 "매장명이 시장이름과 같다"가 성립할 수가 없다 (개별 점포는 "동래시장"이 아니라
    "틸다블루"처럼 자기 상호가 따로 있음) — 그래서 여기만 상호명 매칭을 안 하고,
    시장 좌표(입구/중심점) 반경 안에 있으면 그 시장 소속으로 본다."""
    markets = spots_df[spots_df["category_major"] == "전통시장"]

    rows = []
    for spot in markets.itertuples():
        nearby = within_radius(merchants_df, spot.lat, spot.lon, MARKET_MATCH_RADIUS_M)
        for merchant in nearby.itertuples():
            rows.append({
                "id": merchant.id,
                "name": merchant.name,
                "address": merchant.address,
                "lon": merchant.lon,
                "lat": merchant.lat,
                "category": "시장",
                "data_date": merchant.data_date,
            })
    return rows


def _match_via_kakao(merchants_df: pd.DataFrame, kakao_df: pd.DataFrame) -> list:
    """카카오 키워드검색 결과를 id로 붙이되, 검색 반경(100m) 안의 다른 가게가 잡혔을
    위험이 있어 상호명이 완전일치(sangga와 동일 기준)하는 것만 받아들인다."""
    kakao = kakao_df[kakao_df["status"] == "ok"].copy()
    kakao["category"] = [
        _kakao_category(g, n) for g, n in zip(kakao["category_group_name"], kakao["category_name"])
    ]
    kakao = kakao.dropna(subset=["category"])

    merged = merchants_df.merge(kakao[["id", "place_name", "category"]], on="id", how="inner")
    merged = merged[[_name_matches(n, p) for n, p in zip(merged["name"], merged["place_name"])]]
    return merged[["id", "name", "address", "lon", "lat", "category", "data_date"]].to_dict("records")


def _match_via_busan_mat(merchants_df: pd.DataFrame, busan_mat_df: pd.DataFrame) -> list:
    """"부산의 맛" 인증 식당 목록 - 전부 식당이라 상호명(+구 일치)만 맞으면 "식당"으로 태그한다.
    좌표가 없는 목록이라 구 단위로 먼저 추려서(이름 흔한 가게 오매칭 방지) 비교한다."""
    rows = []
    for bm in busan_mat_df.itertuples():
        candidates = merchants_df[merchants_df["address"].str.contains(bm.gu, na=False)]
        for m in candidates.itertuples():
            if _name_matches(m.name, bm.name):
                rows.append({
                    "id": m.id, "name": m.name, "address": m.address,
                    "lon": m.lon, "lat": m.lat, "category": "식당", "data_date": m.data_date,
                })
    return rows


def build_catalog(merchants_df: pd.DataFrame, spots_df: pd.DataFrame, sangga_df: pd.DataFrame,
                   kakao_df: pd.DataFrame = None, busan_mat_df: pd.DataFrame = None) -> pd.DataFrame:
    """동백전(결제확인) 매장에 카테고리를 붙인다. 카카오 자체 분류/부산의맛 인증 목록이 있으면
    그걸 우선 쓰고, 없는 매장은 근접+상호명 매칭(sangga)/전통시장 반경 매칭으로 보강한다.
    다 안 되는 매장은 카테고리를 알 수 없어 후보에서 제외한다 (알려진 한계)."""
    rows = _match_via_sangga(merchants_df, sangga_df) + _match_via_traditional_market(merchants_df, spots_df)
    if kakao_df is not None:
        rows = _match_via_kakao(merchants_df, kakao_df) + rows
    if busan_mat_df is not None:
        rows = _match_via_busan_mat(merchants_df, busan_mat_df) + rows
    catalog = pd.DataFrame(rows)
    return catalog.drop_duplicates(subset="id", keep="first")


def get_catalog(merchants_df, spots_df, sangga_df, kakao_df=None, busan_mat_df=None) -> pd.DataFrame:
    global _catalog_cache
    if _catalog_cache is None:
        _catalog_cache = build_catalog(merchants_df, spots_df, sangga_df, kakao_df, busan_mat_df)
    return _catalog_cache


MIN_STOP_SEPARATION_M = 30  # 이보다 가까우면 같은 상가 다른 호실/상호 취급, 하나만 남긴다
PER_CATEGORY_POOL_SIZE = 20  # 카테고리 하나가 전체를 독점하지 못하게, 카테고리별로 이만큼만 후보군에 넣는다


def nearest_candidates(catalog: pd.DataFrame, start_lat, start_lon, categories=None, limit=5):
    """카테고리별로 가까운 후보를 고르게 모아두되(한 카테고리가 독점 못 하게),
    최종 정렬/선택은 순수 거리순으로 한다 — 그래야 "다양성" 때문에 터무니없이
    먼 곳(예: 2km 밖 카페 하나 끼워넣기)이 억지로 뽑히지 않는다."""
    pool = catalog
    if categories:
        pool = pool[pool["category"].isin(categories)]
    if pool.empty:
        return []

    pool = pool.copy()
    pool["distance_m"] = haversine_m(start_lat, start_lon, pool["lat"].to_numpy(), pool["lon"].to_numpy())
    pool = pool.sort_values("distance_m")

    capped_parts = [g.head(PER_CATEGORY_POOL_SIZE) for _, g in pool.groupby("category")]
    capped = pd.concat(capped_parts).sort_values("distance_m").to_dict("records")

    deduped = []
    for cand in capped:
        too_close = any(
            haversine_m(cand["lat"], cand["lon"], kept["lat"], kept["lon"]) < MIN_STOP_SEPARATION_M
            for kept in deduped
        )
        if not too_close:
            deduped.append(cand)
        if len(deduped) >= limit * 4:
            break

    return deduped


def optimal_order(start_lat, start_lon, candidates: list, stop_count):
    """candidates 중 stop_count개를 골라 모든 순열을 비교, 총 도보시간이 최소인 조합을 찾는다.
    candidates는 이미 출발지에서 가까운 순으로 정렬된 상태라고 가정하고,
    상위 min(len, stop_count + 2)개 안에서만 순열을 돌려 조합 폭발을 막는다."""
    pool = candidates[: stop_count + 2]
    if len(pool) <= stop_count:
        chosen_sets = [tuple(pool)]
    else:
        chosen_sets = list(itertools.combinations(pool, stop_count))

    best_order = None
    best_minutes = None
    for combo in chosen_sets:
        for perm in itertools.permutations(combo):
            cur_lat, cur_lon = start_lat, start_lon
            total = 0.0
            legs = []
            for stop in perm:
                d = haversine_m(cur_lat, cur_lon, stop["lat"], stop["lon"])
                leg_minutes = estimate_walk_minutes(d)
                legs.append(leg_minutes)
                total += leg_minutes
                cur_lat, cur_lon = stop["lat"], stop["lon"]
            if best_minutes is None or total < best_minutes:
                best_minutes = total
                best_order = (perm, legs)

    return best_order, best_minutes


def recommend_route(merchants_df, spots_df, sangga_df, start_lat, start_lon,
                     categories=None, stop_count=5, max_minutes=None, kakao_df=None, busan_mat_df=None):
    catalog = get_catalog(merchants_df, spots_df, sangga_df, kakao_df, busan_mat_df)
    candidates = nearest_candidates(catalog, start_lat, start_lon, categories, stop_count)
    if not candidates:
        return {"stops": [], "total_minutes": 0, "over_budget": False}

    (order, legs), total_minutes = optimal_order(start_lat, start_lon, candidates, stop_count)

    stops = []
    for i, (stop, leg_minutes) in enumerate(zip(order, legs), start=1):
        stops.append({
            "order": i,
            "id": stop["id"],
            "name": stop["name"],
            "category": stop["category"],
            "address": stop["address"],
            "lon": stop["lon"],
            "lat": stop["lat"],
            "data_date": stop["data_date"],
            "leg_minutes": round(leg_minutes, 1),
        })

    return {
        "stops": stops,
        "total_minutes": round(total_minutes, 1),
        "over_budget": bool(max_minutes is not None and total_minutes > max_minutes),
    }
