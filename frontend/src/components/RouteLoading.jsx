import { useEffect, useState } from "react";

const STEPS = ["주변 장소 탐색 중", "최적 동선 계산 중", "루트 완성 중"];

export default function RouteLoading() {
  const [pct, setPct] = useState(8);

  useEffect(() => {
    const t = setInterval(() => {
      setPct((p) => (p >= 92 ? 92 : p + Math.random() * 12));
    }, 350);
    return () => clearInterval(t);
  }, []);

  const stepIdx = Math.min(STEPS.length - 1, Math.floor((pct / 100) * STEPS.length));

  return (
    <div className="route-loading">
      <span className="spinner" />
      <div className="route-loading-text">{STEPS[stepIdx]}...</div>
      <div className="route-loading-bar">
        <div className="route-loading-fill" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
