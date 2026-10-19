export default function RouteList({ stops, totalMinutes, overBudget, loading, hasSearched }) {
  if (loading) {
    return (
      <div className="route-list state-message">
        <span className="spinner" />
        루트를 계산하는 중...
      </div>
    );
  }

  if (!hasSearched) {
    return (
      <div className="route-list state-message muted">
        지도를 클릭해 출발지를 찍고, 조건을 고른 뒤 <strong>루트 추천받기</strong>를 눌러주세요.
      </div>
    );
  }

  if (!stops.length) {
    return (
      <div className="route-list state-message muted">
        조건에 맞는 부산페이 결제 가능 매장을 찾지 못했어요. 업종을 바꿔보세요.
      </div>
    );
  }

  const sourceDate = stops[0]?.data_date;

  return (
    <div className="route-list">
      <div className={overBudget ? "summary-bar over" : "summary-bar"}>
        총 도보 이동시간 <strong>{totalMinutes}분</strong> (추정)
        {overBudget && <span className="over-badge">⚠ 가능 시간 초과</span>}
      </div>

      {stops.map((stop, idx) => (
        <div key={stop.id} className="route-stop">
          <div className="timeline-col">
            <span className="order-badge">{stop.order}</span>
            {idx < stops.length - 1 && <span className="timeline-line" />}
          </div>
          <div className="route-stop-body">
            {idx > 0 && <div className="leg-label">도보 {stop.leg_minutes}분 (추정)</div>}
            <div className="stop-name">
              {stop.name} <span className="paid-badge">부산페이 결제 확인</span>
            </div>
            <div className="stop-meta">
              <span className="category-tag">{stop.category}</span>
              <span className="stop-address">{stop.address}</span>
            </div>
          </div>
        </div>
      ))}

      <div className="source-note">
        출처: 동백전 가맹점 데이터 (기준일 {sourceDate})
      </div>
    </div>
  );
}
