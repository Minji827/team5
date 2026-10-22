import { useState } from "react";
import { sendRouteEmail } from "../api";
import RouteLoading from "./RouteLoading";

function EmailModal({ onClose, onSend, sending, sendResult }) {
  const [email, setEmail] = useState("");

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-title">루트를 메일로 받기</div>
        <p className="modal-desc">완성된 루트를 이메일로 보내드려요.</p>
        <input
          type="email"
          autoFocus
          placeholder="이메일 주소 입력"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="email-input"
        />
        <div className="modal-actions">
          <button type="button" className="modal-btn ghost" onClick={onClose}>취소</button>
          <button
            type="button"
            className="modal-btn primary"
            disabled={!email || sending}
            onClick={() => onSend(email)}
          >
            {sending ? "전송 중..." : "보내기"}
          </button>
        </div>
        {sendResult === "success" && <div className="email-send-note">전송 요청을 보냈어요.</div>}
        {sendResult === "pending" && (
          <div className="email-send-note muted">전송 기능은 아직 연결 중이에요 (Gmail 설정 필요).</div>
        )}
        {sendResult === "error" && <div className="email-send-note error">전송에 실패했어요. 다시 시도해주세요.</div>}
      </div>
    </div>
  );
}

export default function RouteList({
  stops, alternatives, totalMinutes, overBudget, phase, startPoint, onSwapStop,
}) {
  const [editingIdx, setEditingIdx] = useState(null);
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [sending, setSending] = useState(false);
  const [sendResult, setSendResult] = useState(null);

  async function handleSendEmail(email) {
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

  if (phase === "loading") return <RouteLoading />;

  if (phase === "setup") {
    return (
      <div className="route-list state-message muted">
        지도를 클릭해 출발지를 찍고, 조건을 고른 뒤 <strong>루트 짜기</strong>를 눌러주세요.
      </div>
    );
  }

  if (!stops.length) {
    return (
      <div className="route-list state-message muted">
        조건에 맞는 장소를 찾지 못했어요. 카테고리를 바꿔보세요.
      </div>
    );
  }

  return (
    <div className="route-list">
      <div className={overBudget ? "summary-bar over" : "summary-bar"}>
        총 일정 <strong>{totalMinutes}분</strong> (체류 + 예상 도보 이동)
        {overBudget && <span className="over-badge">⚠ 가능 시간 초과</span>}
      </div>

      {stops.map((stop, idx) => {
        const sameCategoryAlts = alternatives.filter((a) => a.category === stop.category);
        const altList = sameCategoryAlts.length ? sameCategoryAlts : alternatives;
        const isEditing = editingIdx === idx;

        return (
          <div key={stop.id} className="route-stop">
            <div className="timeline-col">
              <span className="order-badge">{stop.order}</span>
              {idx < stops.length - 1 && <span className="timeline-line" />}
            </div>
            <div className="route-stop-body">
              <div className="leg-label">{idx === 0 ? "출발지에서 " : ""}도보 {stop.leg_minutes}분 (TMAP 예상)</div>
              <div className="stop-card">
                <div className="stop-name">
                  {stop.name} <span className="paid-badge">
                    {stop.payment_status === "merchant_listed" ? "동백전 가맹점 명부 등재" : "관광 방문지 · 결제 미확인"}
                  </span>
                </div>
                <div className="stop-meta">
                  <span className="category-tag">{stop.category}</span>
                  <span>체류 {stop.duration_min}분 (기본값)</span>
                  <span className="stop-address">{stop.address}</span>
                </div>
                <button
                  type="button"
                  className="edit-stop-btn"
                  onClick={() => setEditingIdx(isEditing ? null : idx)}
                  disabled={!altList.length}
                >
                  {isEditing ? "닫기" : "수정"}
                </button>
              </div>

              {isEditing && (
                <ul className="alt-list">
                  {altList.length === 0 && <li className="alt-empty">대체할 다른 장소가 없어요.</li>}
                  {altList.map((alt) => (
                    <li
                      key={alt.id}
                      onClick={() => { onSwapStop(idx, alt.id); setEditingIdx(null); }}
                    >
                      <div className="result-name">{alt.name}</div>
                      <div className="result-address">{alt.category} · {alt.address}</div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        );
      })}

      <button type="button" className="submit-btn email-cta" onClick={() => setShowEmailModal(true)}>
        메일로 루트 전송하기
      </button>

      <div className="source-note">
        출처: 동백전 가맹점·한국관광공사·전통시장 데이터. 가맹점의 현재 결제 가능 여부는 방문 전 확인해주세요.
      </div>

      {showEmailModal && (
        <EmailModal
          onClose={() => setShowEmailModal(false)}
          onSend={handleSendEmail}
          sending={sending}
          sendResult={sendResult}
        />
      )}
    </div>
  );
}
