import { useI18n } from "./i18n.js";
import { useEffect, useState } from "react";
import FilterPanel from "./components/FilterPanel";
import MapView from "./components/MapView";
import RouteList from "./components/RouteList";
import NextPlacePicker from "./components/NextPlacePicker";
import { getCategories, getNextPlaces } from "./api";
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
  const [building, setBuilding] = useState(false);
  const [activeCategory, setActiveCategory] = useState(null);
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

  function applyRoute(data) {
    setStops(data.stops);
    setAlternatives(data.alternatives || []);
    setReturnLeg(data.return_leg || null);
    setTotalMinutes(data.total_minutes);
    setOverBudget(data.over_budget);
  }

  function handleSubmit() {
    if (!startPoint || loading) return;
    setAppliedConditions({ startPoint, maxMinutes, returnToStart, categories: [...categories] });
    applyRoute({ stops: [], total_minutes: 0, over_budget: false });
    setActiveCategory(null);
    setError(null);
    setNotice(null);
    setHasSearched(true);
    setBuilding(true);
  }

  async function updateSelection(nextStops, category = null) {
    if (!appliedConditions || loading) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getNextPlaces({ ...appliedConditions, stops: nextStops, category });
      applyRoute(data);
      setActiveCategory(category);
      return true;
    } catch (e) {
      setError(e.message || t("recalculateError"));
      return false;
    } finally {
      setLoading(false);
    }
  }

  const phase = hasSearched ? "result" : "setup";

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
              building={building} busy={loading}
              onRemoveStop={(index) => updateSelection(stops.filter((_, i) => i !== index))}
            />
              {hasSearched && (building ? <NextPlacePicker
                categories={appliedConditions.categories.length ? appliedConditions.categories : allCategories}
                activeCategory={activeCategory} candidates={alternatives} busy={loading}
                stops={stops} remainingMinutes={Math.max(0, appliedConditions.maxMinutes - totalMinutes)}
                onCategory={(category) => updateSelection(stops, category)}
                onSelect={(place) => updateSelection([...stops, place])}
                onFinish={() => { setBuilding(false); setAlternatives([]); }}
              /> : <button type="button" className="secondary-btn" onClick={() => { setBuilding(true); setActiveCategory(null); }}>{t("editCourse")}</button>)}
            </div>
          </div>
        </aside>
        <main className="map-area">
          <MapView
            stops={stops} returnLeg={returnLeg} startPoint={hasSearched ? appliedConditions?.startPoint : startPoint} onPickStart={(point) => { if (!hasSearched) setStartPoint(point); }}
            totalMinutes={totalMinutes} overBudget={overBudget} maxMinutes={appliedConditions?.maxMinutes || maxMinutes}
          />
        </main>
      </div>
      <footer className="app-footer"><span>© BUSAN FULL COURSE <span className="footer-divider">|</span> {t("footer")}</span><div><button type="button" onClick={() => setInfo("guide")}>{t("guide")}</button><button type="button" onClick={() => setInfo("privacy")}>{t("privacy")}</button></div></footer>
      {info && <ServiceInfo section={info} onClose={() => setInfo(null)} />}
    </div>
  );
}
