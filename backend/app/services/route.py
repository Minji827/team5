"""Four-category route selection from the offline place catalog."""
import itertools

import pandas as pd

from app.services.geo import haversine_m

CATEGORIES = ["식당", "카페·디저트", "관광명소", "쇼핑"]
WALK_SPEED_MPS = 4.5 * 1000 / 3600
WALK_DISTANCE_FACTOR = 1.3


def estimate_walk_minutes(distance_m):
    return distance_m * WALK_DISTANCE_FACTOR / WALK_SPEED_MPS / 60


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


def recommend_route(catalog, start_lat, start_lon, categories=None, stop_count=5, max_minutes=None):
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
            "place_type": stop["place_type"],
            "payment_status": stop["payment_status"],
            "source": stop["source"],
            "leg_minutes": round(leg_minutes, 1),
        })

    return {
        "stops": stops,
        "total_minutes": round(total_minutes, 1),
        "over_budget": bool(max_minutes is not None and total_minutes > max_minutes),
    }
