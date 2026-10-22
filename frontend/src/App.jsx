import { useI18n } from "./i18n.js";
import { useEffect, useState } from "react";
import FilterPanel from "./components/FilterPanel";
import MapView from "./components/MapView";
import RouteList from "./components/RouteList";
import { getCategories, getRecommendation, recalculateRoute } from "./api";
import "./App.css";
import Icon from "./components/Icon";
import ServiceInfo from "./components/ServiceInfo";

export default function App() {
  const { locale, setLocale, languages, t, message } = useI18n();
  const [info, setInfo] = useState(null);
  const [startPoint, setStartPoint] = useState(null);
  const [allCategories, setAllCategories] = useState([]);
  const [categories, setCategories] = useState([]);
  const [returnToStart, setReturnToStart] = useState(false);
  const [selectedOnly, setSelectedOnly] = useState(false);
  const [returnLeg, setReturnLeg] = useState(null);
  const [appliedConditions, setAppliedConditions] = useState(null);
  const [maxMinutes, setMaxMinutes] = useState(90);
  const [stops, setStops] = useState([]);
  const [alternatives, setAlternatives] = useState([]);
  const [totalMinutes, setTotalMinutes] = useState(0);
  const [overBudget, setOverBudget] = useState(false);
  const [loading, setLoading] = useState(false);
  const [notice, setNotice] = useState(null);
  const [error, setError] = useState(null);
  const [hasSearched, setHasSearched] = useState(false);

  useEffect(() => {
    getCategories().then(setAllCategories).catch(() => {
      setError("categoryError");
    });
  }, []);

  function toggleCategory(c) {
    setCategories((prev) =>
      prev.includes(c) ? prev.filter((x) => x !== c) : [...prev, c]
    );
  }

  async function handleSubmit() {
    if (!startPoint) return;
    setLoading(true);
    setError(null);
    setNotice(null);
    setHasSearched(true);
    try {
      const data = await getRecommendation({
        startLat: startPoint.lat, startLon: startPoint.lon,
        categories, maxMinutes, returnToStart, selectedOnly,
      });
      setNotice(data.message || null);
      setStops(data.stops);
      setAlternatives(data.alternatives || []);
      setAppliedConditions({ startPoint, maxMinutes, returnToStart });
      setReturnLeg(data.return_leg || null);
      setTotalMinutes(data.total_minutes);
      setOverBudget(data.over_budget);
    } catch (e) {
      setError(e.message || t("recommendError"));
    } finally {
      setLoading(false);
    }
  }

  async function handleSwapStop(index, altId) {
    const alt = alternatives.find((a) => a.id === altId);
    if (!alt || !startPoint) return;
    const replaced = stops[index];
    const nextStops = stops.map((s, i) => (i === index ? { ...alt, order: s.order } : s));
    setLoading(true);
    setError(null);
    setNotice(null);
    try {
      const data = await recalculateRoute({ ...appliedConditions, stops: nextStops });
      setNotice(data.message || null);
      setStops(data.stops);
      setReturnLeg(data.return_leg || null);
      setTotalMinutes(data.total_minutes);
      setOverBudget(data.over_budget);
      setAlternatives((prev) => [replaced, ...prev.filter((a) => a.id !== altId)]);
    } catch (e) {
      setError(e.message || t("recalculateError"));
    } finally {
      setLoading(false);
    }
  }

  const phase = loading ? "loading" : hasSearched ? "result" : "setup";

  return (
    <div className="app">
      <header className="app-header">
        <a className="brand" href="/" aria-label={t("home")}><span className="brand-image"><img src="/busan-full-course-logo.png" alt="BUSAN FULL COURSE" /></span></a>
        <nav className="header-nav" aria-label={t("navigation")}><span className="header-tab active"><Icon name="route" size={17} />{t("plan")}</span><button type="button" onClick={() => setInfo("guide")}>{t("guide")}</button></nav>
        <select className="language-select" aria-label={t("language")} value={locale} onChange={(e) => setLocale(e.target.value)}>{Object.entries(languages).map(([code, label]) => <option key={code} value={code}>{label}</option>)}</select>
      </header>

      <div className="app-body">
        <aside className="sidebar">
          <div className="sidebar-scroll">
            <section className="planner-intro" id="trip-planner"><h1>{t("appTitle")}</h1><p>{t("intro")}</p></section>
            <FilterPanel
              startPoint={startPoint} setStartPoint={setStartPoint}
              allCategories={allCategories}
              categories={categories} toggleCategory={toggleCategory}
              returnToStart={returnToStart} setReturnToStart={setReturnToStart}
              selectedOnly={selectedOnly} setSelectedOnly={setSelectedOnly}
              maxMinutes={maxMinutes} setMaxMinutes={setMaxMinutes}
              onSubmit={handleSubmit} loading={loading}
              collapsed={phase === "result"}
            />
            {notice && <div className="source-note" role="status">{message(notice)}</div>}
            {error && <div className="error">⚠ {message(error)}</div>}
            <div id="trip-results"><RouteList
              stops={stops} alternatives={alternatives}
              totalMinutes={totalMinutes} overBudget={overBudget}
              phase={phase} startPoint={appliedConditions?.startPoint || startPoint} returnLeg={returnLeg}
              onSwapStop={handleSwapStop}
            /></div>
          </div>
        </aside>
        <main className="map-area">
          <MapView
            stops={stops} returnLeg={returnLeg} startPoint={stops.length ? appliedConditions?.startPoint || startPoint : startPoint} onPickStart={setStartPoint}
            totalMinutes={totalMinutes} overBudget={overBudget} maxMinutes={appliedConditions?.maxMinutes || maxMinutes}
          />
        </main>
      </div>
      <footer className="app-footer"><span>© BUSAN FULL COURSE <span className="footer-divider">|</span> {t("footer")}</span><div><button type="button" onClick={() => setInfo("guide")}>{t("guide")}</button><button type="button" onClick={() => setInfo("privacy")}>{t("privacy")}</button></div></footer>
      {info && <ServiceInfo section={info} onClose={() => setInfo(null)} />}
    </div>
  );
}
