# 통합 Place 전처리 참고자료

서비스용 파일은 ../fin/places.csv 하나이며, 이 폴더(place_support)는 기준표·검수·출처 보관용이다.

현재 상태: 부분 통합. 식당 599 + 카페·디저트 167 = 766건.
담당자의 쇼핑 10곳과 관광명소는 아직 수신 전이다. 기존 원도심 임시 쇼핑 목록이나 tourist_spots를 담당자 최종 목록으로 간주해 넣지 않았다.
현재 추천 API는 기존 recommendation_places.csv를 계속 사용한다.

## 파일
- places.csv: 필수 필드가 갖춰진 서비스용 부분 데이터.
- places_review.csv: 미매칭 960 / 분류검토 266 / 쇼핑 선정대기 15 / 간식 상세업종 충돌 1.
- place_sources.csv: 원천 ID·출처·분류 근거·방문유형 배정 규칙·시장 안팎 정보.
- duration_rules.csv: 사용자 제공 사진의 유형별 기본시간. 실측 평균이 아닌 MVP 초기 가정값.
- summary.json: 통합 현황과 미수신 카테고리 표시.

## 규칙
카테고리는 식당 / 카페·디저트 / 관광명소 / 쇼핑.
기존 분류 결과를 재사용하고 경계 포함 공간검사로 4개 행정동을 다시 확인한다.
기본 일반식당60·간편식30·카페45·포장디저트15분은 유형별 초기 가정이다.
카페의 좌석 유무·디저트의 실제 포장 비중을 확인한 실측값은 아니며 place_sources의 규칙에 표시한다.
식사/간식 복수 태그는 간편식으로 처리한다. 빵 업종과 닭강정 업종이 충돌하는 1건은 검수 대상으로 남긴다.

빈 CSV 셀은 NULL이다. 문자열 NULL/None 또는 미확보 금액 0을 저장하지 않는다.
현재 estimated_spend·rating·review_count·image_url·opening_hours는 확보되지 않아 모두 빈칸이다.
숫자 컬럼은 load_places에서 숫자로 읽고 결측값은 None으로 반환한다.
추가로 data_date·place_type·payment_status·source를 넣어 기존 응답 필드와 결제 상태를 구분한다.
관광명소 자체는 가맹점 결제 확인 대상이 아니며 payment_status=not_verified다.

## 재생성
프로젝트 루트에서 QGIS Python으로 실행한다.

"C:\Program Files\QGIS 3.16\bin\python-qgis-ltr.bat" scripts/build_places.py

담당자 파일을 받은 뒤에는 --shopping-file <CSV> --tourism-file <CSV>를 붙인다.
쇼핑 파일 필수: id(기존 MVP 가맹점ID), visit_type(general_shopping 또는 souvenir_shop). 10개 고유ID.
관광명소 파일 필수: id, name, address, lon, lat, visit_type(scenic_spot / exhibition_experience / traditional_market).
입력에서 중복 ID는 오류로 중단하며, 필수 정보 부족·권역 밖·유형 불명확 장소는 review로 분리한다.
상세 계약과 일정 시간 적용 방식은 docs/PLACES_SCHEMA.md 참고.
