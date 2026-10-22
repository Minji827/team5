import { useI18n } from "../i18n.js";

export default function NextPlacePicker({ categories, activeCategory, candidates, busy, stops, remainingMinutes, onCategory, onSelect, onFinish }) {
  const { t, approx, walkTime, stayTime } = useI18n();
  return <section className="next-place-picker" aria-label={t("buildCourse")}>
    <div className="panel-heading"><h2>{t("nextStop", { n: stops.length + 1 })}</h2></div>
    <p className="source-note">{t("chooseNextHint")}</p>
    <p className="remaining-time">{t("remainingTime", { time: approx(remainingMinutes) })}</p>
    <div className="next-category-tabs">{categories.map((category) => <button key={category} type="button" aria-pressed={activeCategory === category} disabled={busy} onClick={() => onCategory(category)}>{t(category)}</button>)}</div>
    <div aria-live="polite" aria-busy={busy}>
      {busy ? <p className="source-note">{t("findingNext")}</p> : activeCategory && (candidates.length ? <ul className="alt-list next-candidates">{candidates.map((place) => <li key={place.id}><button type="button" onClick={() => onSelect(place)}>
        <span className="result-name">{place.name}</span><span className="result-address">{place.address}</span>
        <span className="result-address">{stops.length ? t("fromLastStop") : t("start")}: {walkTime(place.leg_minutes)} · {stayTime(place.duration_min)}</span>
        <span className="result-address">{t("afterAdding", { time: approx(place.projected_total_minutes) })}</span>
        <span className="candidate-tags">{place.payment_status === "merchant_listed" && <span className="payment-tag">{t("paymentTag")}</span>}{place.is_busan_taste && <span className="taste-tag">{t("tasteTag")}</span>}</span>
        <span className="confirm-place">{t("confirmPlace", { n: stops.length + 1 })}</span>
      </button></li>)}</ul> : <p className="source-note">{t("noNextPlaces")}</p>)}
    </div>
    <button type="button" className="submit-btn" disabled={busy || !stops.length} onClick={onFinish}>{t("finishCourse")}</button>
  </section>;
}
