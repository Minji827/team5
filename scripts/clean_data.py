"""여러 소스의 raw 데이터를 공통 스키마로 정제해서 data/processed/ 에 저장한다.

출력:
  merchants.csv          - 동백전 가맹점 (source, name, address, lon, lat, data_date)
  tourist_spots.csv      - TourAPI + 전통시장(부산) 통합 POI
  consumption.csv        - 카드소비(관광데이터랩), long format
  visitors.csv           - 외국인 지역별 방문자수, 연도 통합
  commercial_density.csv - 상가(상권)정보, 행정동x업종대분류 집계
"""

import glob
import os

import pandas as pd

RAW_DIR = "data/raw"
OUT_DIR = "data/processed"

POI_COLUMNS = ["source", "source_id", "name", "category_major", "category_minor",
               "address", "lon", "lat", "data_date"]


def latest_file(pattern):
    paths = sorted(glob.glob(pattern))
    if not paths:
        raise FileNotFoundError(pattern)
    return paths[-1]


def clean_merchants():
    path = os.path.join(OUT_DIR, "dongbaekjeon_geocoded.csv")
    df = pd.read_csv(path, encoding="utf-8-sig")
    df = df[df["geocode_status"] == "ok"].copy()
    out = pd.DataFrame({
        "source": "dongbaekjeon",
        "source_id": None,
        "name": df["store_name"],
        "category_major": "동백전가맹점",
        "category_minor": None,
        "address": df["address"],
        "lon": df["lon"],
        "lat": df["lat"],
        "data_date": df["data_date"],
    })
    out_path = os.path.join(OUT_DIR, "merchants.csv")
    out.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"저장: {out_path} ({len(out)}행)")


def clean_tourist_spots():
    frames = []

    for path in glob.glob(os.path.join(RAW_DIR, "tourapi", "*_tourapi_*.csv")):
        label = os.path.basename(path).split("_tourapi_")[1].replace(".csv", "")
        df = pd.read_csv(path, encoding="utf-8-sig")
        frames.append(pd.DataFrame({
            "source": "tourapi",
            "source_id": df["contentid"],
            "name": df["title"],
            "category_major": label,
            "category_minor": df["cat3"],
            "address": df["addr1"].fillna("") + " " + df["addr2"].fillna(""),
            "lon": df["mapx"],
            "lat": df["mapy"],
            "data_date": df["modifiedtime"].astype(str).str[:8],
        }))

    tm_path = os.path.join(RAW_DIR, "traditional_market", "전국전통시장표준데이터.csv")
    tm = pd.read_csv(tm_path, encoding="cp949")
    tm = tm[tm["소재지도로명주소"].str.startswith("부산", na=False)].copy()
    frames.append(pd.DataFrame({
        "source": "traditional_market",
        "source_id": None,
        "name": tm["시장명"],
        "category_major": "전통시장",
        "category_minor": tm["시장유형"],
        "address": tm["소재지도로명주소"],
        "lon": tm["경도"],
        "lat": tm["위도"],
        "data_date": tm["데이터기준일자"],
    }))

    out = pd.concat(frames, ignore_index=True)[POI_COLUMNS]
    out = out.dropna(subset=["lon", "lat"])
    out_path = os.path.join(OUT_DIR, "tourist_spots.csv")
    out.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"저장: {out_path} ({len(out)}행)")


def clean_consumption():
    path = latest_file(os.path.join(RAW_DIR, "tour_consumption", "*_관광데이터랩_소비.csv"))
    df = pd.read_csv(path, encoding="utf-8-sig")
    category_cols = ["여행/숙박", "여가/문화", "유통", "음식/주점", "음식료품",
                      "의류/잡화", "미용", "의료", "교육", "생활", "자동차"]
    id_cols = ["year_month", "gu", "dong_region_code", "dong_name", "lon", "lat"]
    long_df = df.melt(id_vars=id_cols, value_vars=category_cols,
                       var_name="category", value_name="amount_krw")
    out_path = os.path.join(OUT_DIR, "consumption.csv")
    long_df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"저장: {out_path} ({len(long_df)}행)")


def clean_visitors():
    frames = []
    for path in glob.glob(os.path.join(RAW_DIR, "visitors", "2*_외국인 지역별 방문자 수.csv")):
        period = os.path.basename(path).split("_")[0]
        df = pd.read_csv(path, encoding="utf-8-sig")
        df = df.rename(columns={"지역": "region", "외국인 방문자수": "foreign_visitors"})
        df["period"] = period
        frames.append(df)

    out = pd.concat(frames, ignore_index=True)[["period", "region", "foreign_visitors"]]
    out_path = os.path.join(OUT_DIR, "visitors.csv")
    out.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"저장: {out_path} ({len(out)}행)")


def clean_commercial_density():
    path = latest_file(os.path.join(RAW_DIR, "sangga", "*.zip"))
    df = pd.read_csv(path, compression="zip", encoding="utf-8-sig")

    grouped = df.groupby(["시군구명", "행정동명", "상권업종대분류명"]).agg(
        store_count=("상가업소번호", "count"),
        lon=("경도", "mean"),
        lat=("위도", "mean"),
    ).reset_index()
    grouped = grouped.rename(columns={
        "시군구명": "gu", "행정동명": "dong", "상권업종대분류명": "category_major",
    })
    out_path = os.path.join(OUT_DIR, "commercial_density.csv")
    grouped.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"저장: {out_path} ({len(grouped)}행)")


if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    clean_merchants()
    clean_tourist_spots()
    clean_consumption()
    clean_visitors()
    clean_commercial_density()
