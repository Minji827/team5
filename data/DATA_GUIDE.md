# 데이터 적재 가이드 (Busan Full-Course · 제5조)

> 담당: 백엔드·데이터 개발(강민지) 기준 작성. 이 문서는 PR 없이 각자 raw 데이터를 올리고,
> AI로 정제해서 정해진 스키마의 CSV로 만드는 과정을 다룹니다. Supabase 실제 적재는 다음 단계.

## 0. 전체 흐름

```
[각자 raw 원본 업로드] → [AI 프롬프트로 정제/스키마 매핑] → [data/processed/*.csv] → (이후) Supabase Postgres 적재
```

- raw 폴더의 파일은 원본 그대로, 가공 금지
- 정제는 반드시 AI 프롬프트(아래 3번) 결과로 나온 pandas 코드를 실행해서 만들고, `data/processed/`에 저장
- 최종 컬럼명·타입은 PRD의 ERD(6.2, 6.3)를 기준으로 통일 — 담당자가 임의로 컬럼명을 바꾸지 않기

## 1. 폴더 구조 (소스별)

```
data/
  raw/
    dongbaekjeon/        # 동백전 가맹점 (데이터 A·김채원)
    sangga/              # 상가정보 분기 CSV (데이터 B·엄유성)
    tourapi/             # TourAPI 관광지·음식점 (데이터 B·엄유성)
    traditional_market/  # 전통시장 표준데이터 (데이터 B·엄유성)
    tour_consumption/    # 관광 데이터랩 소비 (데이터 C·강미)
    visitors/            # 관광공사 방문자 수 (데이터 C·강미)
    population_flow/     # 생활인구 유입·유출 GIS 대시보드 (데이터 C·강미)
    weather/             # 날씨 API/캐시 (데이터 C·강미)
  processed/
    merchant.csv
    merchant_source_link.csv
    payment_capability.csv
    opening_hours.csv
    region_monthly_spend.csv
    region_monthly_visitors.csv
    region_flow.csv
```

## 2. 소스별 업로드 규칙

| 폴더 | 담당 | 원본 형태 | 파일명 규칙 | 목표 테이블 |
|---|---|---|---|---|
| `dongbaekjeon/` | 데이터 A | CSV (공공데이터포털) | `YYYYMMDD_동백전가맹점.csv` | `merchant`, `merchant_source_link`, `payment_capability` |
| `sangga/` | 데이터 B | 분기 CSV (소진공) | `YYYYMMDD_상가정보_Q.csv` | `merchant`, `merchant_source_link` |
| `tourapi/` | 데이터 B | API 응답 저장(JSON/CSV) | `YYYYMMDD_tourapi_관광지.csv` | `opening_hours`, (관광지 보조정보) |
| `traditional_market/` | 데이터 B | CSV (표준데이터) | `YYYYMMDD_전통시장.csv` | `merchant` (태그만 병합) |
| `tour_consumption/` | 데이터 C | 다운로드 CSV | `YYYYMMDD_관광데이터랩_소비.csv` | `region_monthly_spend` |
| `visitors/` | 데이터 C | API 응답 CSV | `YYYYMMDD_방문자수.csv` | `region_monthly_visitors` |
| `population_flow/` | 데이터 C | GIS 대시보드 추출 CSV/GeoJSON | `YYYYMMDD_생활인구_유입유출.csv(.geojson)` | `region_flow` |
| `weather/` | 데이터 C | API/캐시 CSV | `YYYYMMDD_날씨.csv` | (서비스 로직에서 실시간 보정용, 별도 테이블 없음) |

공통 규칙:
- 날짜는 데이터 **기준일**(수집일 아님)로 기재
- 인코딩 UTF-8, 헤더 1행 필수
- 같은 소스를 다시 받으면 파일을 덮어쓰지 말고 날짜를 올려 새 파일로 추가 (버전 추적용)

## 3. AI 프롬프트 ("딸깍" 적재용)

아래 프롬프트는 **그대로 복붙**해서 담당자 본인 데이터 + 아래 공통 지침을 채운 뒤 AI에게 넣으면 됩니다.
AI는 "정제 코드"까지 바로 출력하도록 설계했습니다 (사람이 직접 pandas 코드 짤 필요 없음).

### 공통 지침 (모든 프롬프트 맨 앞에 붙이기)

```
너는 "Busan Full-Course" 프로젝트의 데이터 적재 담당 AI야.
최종 목표는 아래 "목표 스키마"에 맞는 CSV를 data/processed/ 아래 저장하는 pandas 코드를 만드는 거야.

규칙:
- 원본 파일은 절대 수정하지 말고, 새 파일로만 저장해.
- 목표 스키마에 없는 컬럼은 버리거나 별도로 "미사용 컬럼" 목록으로 알려줘.
- 목표 스키마에 있는데 원본에 없는 컬럼은 NULL이 아니라, 지정한 기본값/"unknown" 등으로 채워 (어떤 값인지 꼭 설명).
- 결측치·중복·좌표 이상치를 먼저 점검표로 보여주고, 그다음에 정제 코드를 출력해.
- 최종적으로 pandas 코드 + "이 코드가 하는 일 요약 5줄 이하"를 같이 줘.
```

### 3-1. 동백전 가맹점 (데이터 A)

```
[공통 지침 붙여넣기]

목표 테이블: merchant, merchant_source_link, payment_capability

목표 스키마:
- merchant: merchant_id(결정적 생성, 예: source+원본키 해시), name, category, region(sigungu_code), lat, lng, crowd_level
- merchant_source_link: source="dongbaekjeon", source_record_key(원본 고유키), merchant_id
- payment_capability: merchant_id, method(예: "동백전"), status(available/unavailable/unknown 중 하나, NULL 금지),
  verified_at(확인일, 없으면 데이터 기준일로 대체), trust_grade(A=공식확인/B=공식목록존재/C=오래됨)

요청:
1. 원본에서 매장명·주소·좌표·업종 컬럼을 찾아 위 스키마에 매핑해줘 (매핑표로 먼저 보여줘).
2. merchant_id는 어떻게 결정적으로 만들지 제안해줘 (예: source + 원본 PK를 해시).
3. status는 원본에 결제 가능 여부 컬럼이 없으면 전부 "unknown"으로 채우고, 그 이유를 설명해줘.
4. 주소만 있고 좌표가 없는 행은 "좌표 변환 필요" 목록으로 따로 뽑아줘.
5. 위 내용 반영한 pandas 코드 + 3개 CSV(merchant.csv, merchant_source_link.csv, payment_capability.csv) 저장 코드 출력해줘.

[원본 데이터 샘플 or 파일 붙여넣기]
```

### 3-2. 상가정보 (데이터 B)

```
[공통 지침 붙여넣기]

목표 테이블: merchant, merchant_source_link

목표 스키마:
- merchant: merchant_id, name, category, region(sigungu_code), lat, lng
- merchant_source_link: source="sangga", source_record_key, merchant_id

요청:
1. 업종 분류 컬럼이 원본에서 어떤 컬럼인지 찾아 매핑해줘.
2. 주소 기반 좌표 변환이 필요한 행 비율을 알려줘.
3. 기존 dongbaekjeon merchant.csv(있으면 같이 줄게)와 같은 매장이 중복으로 들어가지 않도록
   병합 전 "중복 후보"를 주소+상호명 유사도로 찾아줘.
4. pandas 코드 + merchant.csv / merchant_source_link.csv 저장 코드 출력해줘.

[원본 데이터 샘플 or 파일 붙여넣기]
[있으면 기존 merchant.csv도 붙여넣기]
```

### 3-3. TourAPI 관광지·음식점 (데이터 B)

```
[공통 지침 붙여넣기]

목표 테이블: opening_hours (+ 참고용 관광지 정보)

목표 스키마:
- opening_hours: place_id, day_of_week(월~일), open_time, close_time (휴무일은 open_time/close_time을 null 대신 "closed"로 표기)

요청:
1. TourAPI 응답에서 운영시간 관련 필드를 찾아 요일별로 펼쳐줘 (한 장소당 최대 7행).
2. 다국어 명칭(영/중/일)이 있으면 별도 컬럼으로 남겨줘 (스키마엔 없지만 버리지 말고 "참고 컬럼"으로 표시).
3. 운영시간 정보가 없는 장소는 "정보없음" 목록으로 따로 보여줘.
4. pandas 코드 + opening_hours.csv 저장 코드 출력해줘.

[원본 API 응답 샘플 or 파일 붙여넣기]
```

### 3-4. 전통시장 표준데이터 (데이터 B)

```
[공통 지침 붙여넣기]

목표: 기존 merchant.csv에 "전통시장" 태그만 추가 (새 테이블 아님)

요청:
1. 전통시장 목록과 기존 merchant.csv를 상호명/주소 기준으로 매칭해줘.
2. 매칭된 merchant_id에 is_traditional_market=True 컬럼을 추가해줘.
3. 매칭 안 된 전통시장(merchant에 아직 없는 곳)은 "신규 추가 후보" 목록으로 보여줘.
4. pandas 코드 + 업데이트된 merchant.csv 저장 코드 출력해줘.

[전통시장 원본 데이터 붙여넣기]
[기존 merchant.csv 붙여넣기]
```

### 3-5. 관광 데이터랩 소비 (데이터 C)

```
[공통 지침 붙여넣기]

목표 테이블: region_monthly_spend (visitor_count 컬럼 넣지 말 것 — region_monthly_visitors와 분리)

목표 스키마:
- region_monthly_spend: sigungu_code, year_month, category, spend_amount, spend_unit

요청:
1. 원본의 지역 표기(구/군 이름)를 sigungu_code로 매핑할 수 있는 매핑표를 먼저 만들어줘 (부산 구·군 기준).
2. 업종 분류가 원본과 서비스 업종 분류가 다르면 매핑표를 보여줘.
3. 방문자 수 관련 컬럼이 같이 섞여 있으면 반드시 분리해서 알려주고, region_monthly_spend에는 넣지 마.
4. pandas 코드 + region_monthly_spend.csv 저장 코드 출력해줘.

[원본 데이터 샘플 or 파일 붙여넣기]
```

### 3-6. 관광공사 방문자 수 (데이터 C)

```
[공통 지침 붙여넣기]

목표 테이블: region_monthly_visitors

목표 스키마:
- region_monthly_visitors: sigungu_code, year_month, visitor_count

요청:
1. sigungu_code 매핑표를 적용해줘 (3-5에서 만든 매핑표 재사용).
2. 월 단위가 아닌 데이터(일별 등)가 있으면 월 단위로 집계하는 방법을 제안해줘.
3. pandas 코드 + region_monthly_visitors.csv 저장 코드 출력해줘.

[원본 데이터 샘플 or 파일 붙여넣기]
```

### 3-7. 생활인구 유입·유출 (데이터 C)

```
[공통 지침 붙여넣기]

목표 테이블: region_flow

목표 스키마:
- region_flow: sigungu_code, flow_date, time_slot, direction(inflow/outflow), flow_count(명 단위)
  - 결측치는 0이 아니라 "unknown"으로 표시 (0과 결측을 구분해야 함)

요청:
1. GIS 대시보드에서 뽑은 원본의 시간대 구분 기준(예: 1시간 단위/3시간 단위)을 먼저 알려줘.
2. direction이 원본에 없고 순유입/유출만 있으면 어떻게 inflow/outflow 두 행으로 나눌지 제안해줘.
3. 결측 시간대를 0으로 메우지 말고 "unknown"으로 표시하는 코드로 작성해줘.
4. pandas 코드 + region_flow.csv 저장 코드 출력해줘.

[원본 데이터 샘플(CSV/GeoJSON) or 파일 붙여넣기]
```

### 3-8. 날씨 데이터 (데이터 C)

```
[공통 지침 붙여넣기]

목표: 별도 DB 테이블 없음. 추천 로직에서 실시간/캐시로 참조할 수 있는 형태로만 정리.

요청:
1. 일별 날씨 상태(비/눈/맑음 등)와 장소 유형(실내/실외) 매핑에 쓸 수 있게 컬럼을 정리해줘.
2. 캐시용 CSV 저장 코드(날짜, 지역, 날씨상태, 강수여부)를 만들어줘.

[원본 데이터 샘플 or 파일 붙여넣기]
```

## 4. 체크리스트 (적재 전 확인)

- [ ] sigungu_code 매핑표가 모든 소스에서 동일한 기준을 쓰는가
- [ ] merchant_id가 소스 간에 중복 생성되지 않는가 (merchant_source_link로 추적 가능한가)
- [ ] status/trust_grade에 NULL이 없는가
- [ ] region_flow 결측이 0으로 둔갑하지 않았는가
- [ ] 출처·기준일·확인일 컬럼이 빠진 파일이 없는가
