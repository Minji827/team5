import { useState } from "react";
import { sendRouteEmail } from "../api";

export default function RouteList({ stops, totalMinutes, overBudget, loading, hasSearched, startPoint }) {
  const [email, setEmail] = useState("");
  const [sending, setSending] = useState(false);
  const [sendResult, setSendResult] = useState(null);

  async function handleSendEmail() {
    if (!email) return;
    setSending(true);
    setSendResult(null);
    try {
      const res = await sendRouteEmail({ email, stops, totalMinutes, startPoint });
      setSendResult(res.sent ? "success" : "pending");
    } catch (e) {
      setSendResult("error");
    } finally {
      setSending(false);
    }
  }

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

      <div className="email-send-box">
        <input
          type="email"
          placeholder="이메일 주소 입력"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="email-input"
        />
        <button
          type="button"
          onClick={handleSendEmail}
          disabled={!email || sending}
          className="email-send-btn"
        >
          {sending ? "전송 중..." : "이메일로 보내기"}
        </button>
        {sendResult === "success" && <div className="email-send-note">전송 요청을 보냈어요.</div>}
        {sendResult === "pending" && (
          <div className="email-send-note muted">전송 기능은 아직 연결 중이에요 (Gmail 설정 필요).</div>
        )}
        {sendResult === "error" && <div className="email-send-note error">전송에 실패했어요. 다시 시도해주세요.</div>}
      </div>

      <div className="source-note">
        출처: 동백전 가맹점 데이터 (기준일 {sourceDate})
      </div>
    </div>
  );
}
