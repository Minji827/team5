# 추천 장소 카테고리 (2026-10-21)

추천 데이터: data/processed/recommendation_places.csv. 원본 가맹점은 보존한다.
대상: 중구·서구·동구·영도구. 식당 3,172 / 카페·디저트 848 / 관광명소 73 / 쇼핑 10.

기존 여행목적 정제 결과와 kakao_update_20261021 승인 재매칭을 id로 합친다. 검토중·미매칭은 제외한다.
식사·분식·일반 간식은 식당, 빵·떡·빙수·디저트는 카페·디저트로 통합한다.
시장 35곳은 관광명소의 독립 방문지다. 주변 가게 업종을 시장으로 변경하지 않는다.
관광명소에는 관광지·문화시설·전통시장 자료를 사용한다.
쇼핑은 원도심 기념품 분류 가맹점 중 양쪽 원천 근거가 있는 곳을 우선, id순으로 10곳을 추린 임시 후보다.
shopping_mvp_candidates.csv에서 목록과 근거를 확인한다. 인기 순위나 현장 검수 결과가 아니다.

place_type: merchant / attraction / market
payment_status: merchant_listed(명부 등재) / not_verified(관광 방문지)
source, data_date, category_evidence: 출처·기준일·분류근거.
명부 등재가 현재 결제 가능 여부를 보증하지 않는다.

재생성: 프로젝트 루트에서 python scripts/build_recommendation_places.py 실행 후 백엔드 재시작.
검증: 카테고리별 API 3곳 추천, 중복id·시장분류·결제상태·디저트 분기, 프런트엔드 빌드 통과.
한계: 정확도·폐업 여부 수동 검수 전. 넓은 관광특구·거리의 대표 방문지 검토 필요.
가중치·체류시간·장소 대체 기능은 다음 단계다.
