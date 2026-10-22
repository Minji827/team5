import { useI18n } from "../i18n.js";
import { useEffect, useState } from "react";

const STEPS = ["load1", "load2", "load3"];

export default function RouteLoading() {
  const { t } = useI18n();
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
      <div className="route-loading-text">{t(STEPS[stepIdx])}...</div>
      <div className="route-loading-bar">
        <div className="route-loading-fill" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
