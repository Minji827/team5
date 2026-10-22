# places.csv 연동 명세

## 폴더와 적용 상태

서비스 출력은 data/processed/fin/places.csv 하나다. 기준표·출처·검수·집계는 data/processed/place_support에 보관한다. process라는 별도 폴더를 만들지 않는다.
현재 식당·카페만 766건으로 부분 생성했다. 쇼핑10·관광명소 담당자 입력은 미수신이며 추천 API는 전환하지 않는다.
새 load_places()는 CSV를 읽는 별도 함수로 준비하고 기존 load_recommendation_places() 호출을 유지한다.

현재 코드에는 build_catalog()가 없다. 기존 scripts/build_recommendation_places.py의 category_for()와
최신 GIS/mvp/mvp_merchants.csv의 동백전·카카오·상가 매칭 결과를 재사용한다.
재생성 때 원본 전체 API 매칭을 반복하지 않고, 최신 승인된 분류를 전처리 입력으로 사용한다.
전처리는 QGIS Python(기존 데스크톱 GIS 환경)에서 실행한다. 서비스 서버에는 QGIS가 필요하지 않다.

## 컬럼 계약

필수: id(str), name(str), category(str), visit_type(str), address(str), lon(float), lat(float), admin_dong(str), duration_min(양의 정수).
선택: estimated_spend(원/1인), rating, review_count, image_url, opening_hours.
기존 추천 응답 호환을 위해 추가: data_date, place_type, payment_status, source.
CSV 빈칸은 NULL. 누락 정보에 0이나 가상 값을 넣지 않는다. 숫자 정보 미확보와 실제 0은 구분한다.
영업시간은 안내용이며 필수 제외조건으로 쓰지 않는다.

place_type: merchant / attraction / market.
payment_status: merchant_listed(가맹점 명부 등재) / not_verified(관광명소 자체 결제 미확인).
명부 등재는 현재 실제 결제 가능 여부의 현장 확인을 보증하지 않는다.
id는 기존 가맹점ID를 유지하며 관광명소는 spot: 접두사로 이름공간을 분리한다.
행정동은 남포·광복·부평·대청 4개 행정동 경계의 좌표 포함 여부로 검사한다.
겹친 경계로 동을 하나로 확정하지 못하는 곳은 review로 분리한다.
시장 내부 가게는 별도의 merchant이며 시장 소속을 이유로 category를 관광명소로 덮어쓰지 않는다.
시장 소속·원천 상세근거는 data/processed/place_support/place_sources.csv에서 관리한다.

## 방문 유형별 초기 시간

| visit_type | 카테고리 | 분 |
|---|---|---:|
| general_restaurant | 식당 | 60 |
| quick_meal | 식당 | 30 |
| seated_cafe | 카페·디저트 | 45 |
| takeaway_dessert | 카페·디저트 | 15 |
| general_shopping | 쇼핑 | 40 |
| souvenir_shop | 쇼핑 | 20 |
| scenic_spot | 관광명소 | 30 |
| exhibition_experience | 관광명소 | 60 |
| traditional_market | 관광명소 | 60 |

사용자 제공 시간 관련.png의 MVP 초기 가정값이며 실측 평균이 아니다.
사진의 최소/최대 범위는 data/processed/place_support/duration_rules.csv에 참고값으로 보관하며 사용자 수정값을 자동으로 제한하지 않는다.
좌석 유무·포장 여부를 확인하지 못한 유형 기본 배정은 data/processed/place_support/place_sources.csv의 규칙에서 확인할 수 있다.

## 일정 데이터와 사용자 변경 시간 (API/UI 구현은 별도)

일정의 각 방문에 stop_id, place_id, duration_override_min을 보관한다.
duration_override_min=NULL이면 places.duration_min을 사용한다.
수정값이 있으면 해당 일정에서만 적용한다. places.csv와 유형 기준표는 변경하지 않는다.
적용시간 = override가 NULL이면 기본값, 아니면 override.
전체시간 = 출발지부터 첫 장소까지 + 장소 사이 이동시간 + 각 장소 적용 체류시간.
돌아오는 지점이 지정된 경우 마지막 이동시간도 포함한다.
시장 자체와 그 안 가게를 함께 넣으면 체류시간을 중복 계산할 수 있으므로 코스 설계 단계에서 별도 규칙을 정한다.
현재 route.py는 이동시간만 계산한다. load_places()를 연결하는 것만으로 체류시간·시간예산 검증이 구현되는 것은 아니다.

## 담당자 입력

쇼핑: id,visit_type 헤더의 10개 고유 가맹점ID. 현재 MVP 가맹점 목록에 있는 ID여야 한다.
관광명소: id,name,address,lon,lat,visit_type. admin_dong은 입력 문자열을 믿지 않고 경계로 재판정한다.
기타 선택정보는 확보된 값만 제공한다. 개인정보·계정 정보는 수집하지 않는다.
서비스 카테고리·방문유형·좌표·이름·주소가 불명확한 행은 data/processed/place_support/places_review.csv로 보낸다.

## 완료/미완료

완료: 부분 CSV 생성, 근거 분리, MVP 경계 필터, 초기시간 적용, load_places 검증 함수 준비.
대기: 쇼핑10/관광명소 담당자 데이터, 대표메뉴 가격.
미구현: 추천 API 입력 전환, 일정별 시간 수정 API/UI, 총시간 제약 반영. 기존 파이프라인과 팀원 작업은 유지한다.
