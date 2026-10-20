# 부산페이 도보 루트 추천 (team5)

부산 관광객이 동백전(지역화폐) 결제 가능한 매장만으로 도보 루트를 추천받고,
결과를 이메일로 받아볼 수 있는 서비스.

- 데이터 수집/정제 가이드: [DATA_GUIDE.md](DATA_GUIDE.md)
- 추천 알고리즘 설명: [ROUTE_ALGORITHM.md](ROUTE_ALGORITHM.md)

## 실행 방법

```bash
# 백엔드
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# 프론트엔드
cd frontend
npm install
npm run dev
```

`.env`에 `KAKAO_REST_API_KEY`, `TOURAPI_SERVICE_KEY`, `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD` 필요.

## 파일 구조

```
team5/
├── backend/                     # FastAPI 서버
│   └── app/
│       ├── main.py              # FastAPI 앱 생성, 라우터 등록
│       ├── data_loader.py       # data/processed/*.csv 를 읽어 메모리 캐싱
│       ├── routers/
│       │   ├── spots.py         # 업종 카테고리 목록 조회
│       │   ├── merchants.py     # 반경 내 매장 조회
│       │   ├── geocode.py       # 주소/장소명 검색 (Kakao 키워드 검색 프록시)
│       │   ├── recommend.py     # 출발지+조건 → 도보 루트 추천
│       │   └── notify.py        # 추천 루트를 Gmail로 발송 (+ 구글맵 링크)
│       └── services/
│           ├── geo.py           # 거리 계산, 반경 필터 유틸
│           └── route.py         # 매장-카테고리 매칭, 루트 최적 순서 계산
│
├── frontend/                     # React + Vite
│   └── src/
│       ├── App.jsx               # 전체 레이아웃, 상태 관리
│       ├── api.js                # 백엔드 API 호출 함수 모음
│       ├── constants.js          # 지도 초기 중심좌표 등 상수
│       └── components/
│           ├── FilterPanel.jsx   # 출발지 검색, 업종/개수/시간 필터 UI
│           ├── MapView.jsx       # Leaflet 지도, 마커/경로 표시
│           └── RouteList.jsx     # 추천 결과 목록 + 이메일 발송 버튼
│
├── scripts/                      # 데이터 수집·가공 스크립트 (레포 루트에서 실행)
│   ├── download_localdata_raw.py # 인허가(일반음식점) 원본 다운로드
│   ├── fetch_bs_gis.py           # 부산시 카드소비 데이터 수집
│   ├── fetch_tourapi.py          # TourAPI 관광지/음식점 데이터 수집
│   ├── fetch_kakao_categories.py # 동백전 매장에 Kakao 업종분류 태깅 (쿼터 초과 시 캐시로 이어서 진행)
│   ├── geocode_dongbaekjeon.py   # 동백전 가맹점 주소 → 좌표 변환
│   ├── clean_data.py             # raw 데이터들을 공통 스키마로 정제 → data/processed/
│   └── load_to_supabase.py       # data/processed/*.csv 를 Supabase에 업로드
│
├── data/
│   ├── raw/                      # 팀원별 원본 데이터 (가공 전) — 담당/규칙은 DATA_GUIDE.md 참고
│   └── processed/                # 정제된 공통 스키마 CSV (merchants, tourist_spots, consumption 등)
│
├── supabase/schema.sql           # Supabase 테이블 스키마
├── load_data.py                  # (구) raw CSV 병합 스크립트, clean_data.py로 대체됨
├── DATA_GUIDE.md                 # 데이터 수집 규칙/폴더 담당자
├── ROUTE_ALGORITHM.md            # 루트 추천 로직 설명
└── .env                          # API 키/메일 계정 (git 추적 안 됨)
```
