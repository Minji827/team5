# 통합 Place 데이터 계약

기준: 2026-10-23. 추천 API는 `load_places()`로 `data/processed/fin/places.csv`를 읽습니다. 기준표·검수·출처는 `data/processed/place_support/`에 분리합니다. `data/process`는 사용하지 않습니다.

## 컬럼

| 컬럼 | 계약 |
|---|---|
| `id` | 고유 문자열. 가맹점 ID 유지, 관광명소는 `spot:` 접두사 |
| `name`, `address` | 확인된 장소명·주소, 필수 |
| `category` | 식당 / 카페·디저트 / 관광명소 / 쇼핑, 필수 |
| `visit_type` | 기본 체류시간 분류, 필수 |
| `lon`, `lat` | WGS84 경도·위도, 필수 |
| `admin_dong` | 남포동 / 광복동 / 부평동 / 대청동, 필수 |
| `duration_min` | 양의 정수 기본 체류시간, 필수 |
| `estimated_spend` | 대표 메뉴 기준 1인 예상 원화 금액. 미확보는 빈칸 |
| `rating`, `review_count` | 선택 필드. 운영 점수에 사용하지 않음 |
| `image_url`, `opening_hours` | 확보한 경우만 기록. 영업시간은 안내용 |
| `data_date`, `source` | 자료 기준일·출처 |
| `place_type` | merchant / attraction / market |
| `payment_status` | merchant_listed / not_verified |

빈칸은 결측값이며 미확보 금액·평점을 0으로 채우지 않습니다. 로더는 필수값·ID 중복·업종/유형 조합·행정동·좌표 범위·숫자를 검사하고 선택 필드 결측을 `null`로 응답합니다. Google 평점 영구 저장 전처리는 포함하지 않습니다.

## 기본 체류시간

| visit_type | 분 |
|---|---:|
| general_restaurant | 60 |
| quick_meal | 30 |
| seated_cafe | 45 |
| takeaway_dessert | 15 |
| general_shopping | 40 |
| souvenir_shop | 20 |
| retail_store | 25 |
| scenic_spot | 30 |
| exhibition_experience | 60 |
| traditional_market | 60 |

출처는 `duration_rules.csv`입니다. 사용자 제공 기준·담당자 자료의 초기 가정이며 실측 평균이 아닙니다. 장소별 체류시간 수정 UI·일정별 override 저장은 아직 구현하지 않았습니다.

## 재생성

현재 `build_catalog()` 함수는 없습니다. `scripts/build_places.py`가 기존 분류 함수와 승인된 GIS MVP 매칭 결과를 재사용합니다. 공간 검사는 전처리 단계에서 QGIS Python으로 수행하고 서비스 서버에는 QGIS가 필요하지 않습니다.

프로젝트 루트에서 아래처럼 쇼핑·관광명소 입력을 모두 지정합니다. 생략하면 부분 결과로 덮어쓸 수 있으므로 재생성 전에 산출물을 보관하세요.

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
& "C:/Program Files/QGIS 3.16/bin/python-qgis-ltr.bat" "$PWD/scripts/build_places.py" --shopping-file "$PWD/data/shopping_verification/shopping_places_final.csv" --tourism-file "$PWD/data/processed/mvp_tourist_spots.csv"
```

쇼핑 선정 ID는 좌표·정규화 상호로 기존 가맹점에 연결하며 최종 출력은 가맹점 ID를 사용합니다. 관광명소는 유형·좌표가 필요하고 행정동은 경계로 판정합니다. 산출물은 서비스 CSV, 출처 CSV, 검수 CSV, `summary.json`입니다. JSON의 과거 호환 필드 `backend_switched`를 현재 배포 상태로 해석하지 마세요.

## 일정·노출 데이터와의 관계

선택 순서는 프런트 상태와 API의 `stop_ids`에서 관리하며 완성 일정 테이블은 없습니다. 도보·체류·선택한 복귀시간을 합산하고 시간 초과는 경고로 처리합니다. 영속 DB에는 추천 목록 ID·장소 ID 배열·생성/표시 시각만 저장합니다. 분류 검토 CSV는 고객 리뷰나 방문 기록이 아닙니다.
