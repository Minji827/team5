import { useEffect, useState } from "react";
import FilterPanel from "./components/FilterPanel";
import MapView from "./components/MapView";
import RouteList from "./components/RouteList";
import { getCategories, getRecommendation, recalculateRoute } from "./api";
import "./App.css";

export default function App() {
  const [startPoint, setStartPoint] = useState(null);
  const [allCategories, setAllCategories] = useState([]);
  const [categories, setCategories] = useState([]);
  const [stopCount, setStopCount] = useState(5);
  const [maxMinutes, setMaxMinutes] = useState(90);
  const [stops, setStops] = useState([]);
  const [alternatives, setAlternatives] = useState([]);
  const [totalMinutes, setTotalMinutes] = useState(0);
  const [overBudget, setOverBudget] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hasSearched, setHasSearched] = useState(false);

  useEffect(() => {
    getCategories().then(setAllCategories).catch(() => {
      setError("카테고리를 불러오지 못했어요. 잠시 후 새로고침해주세요.");
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
    setHasSearched(true);
    try {
      const data = await getRecommendation({
        startLat: startPoint.lat, startLon: startPoint.lon,
        categories, stopCount, maxMinutes,
      });
      setStops(data.stops);
      setAlternatives(data.alternatives || []);
      setTotalMinutes(data.total_minutes);
      setOverBudget(data.over_budget);
    } catch (e) {
      setError(e.message || "추천을 불러오지 못했습니다.");
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
    try {
      const data = await recalculateRoute({ startPoint, stops: nextStops, maxMinutes });
      setStops(data.stops);
      setTotalMinutes(data.total_minutes);
      setOverBudget(data.over_budget);
      setAlternatives((prev) => [replaced, ...prev.filter((a) => a.id !== altId)]);
    } catch (e) {
      setError(e.message || "이동시간을 다시 계산하지 못했습니다.");
    } finally {
      setLoading(false);
    }
  }

  const phase = loading ? "loading" : hasSearched ? "result" : "setup";

  return (
    <div className="app">
      <aside className="sidebar">
        <header className="sidebar-header">
          <span className="logo-badge">🧭</span>
          <div>
            <h1>부산페이</h1>
            <p className="subtitle">관광객 도보 루트 추천</p>
          </div>
        </header>

        <div className="sidebar-scroll">
          <FilterPanel
            startPoint={startPoint} setStartPoint={setStartPoint}
            allCategories={allCategories}
            categories={categories} toggleCategory={toggleCategory}
            stopCount={stopCount} setStopCount={setStopCount}
            maxMinutes={maxMinutes} setMaxMinutes={setMaxMinutes}
            onSubmit={handleSubmit} loading={loading}
            collapsed={phase === "result"}
          />
          {error && <div className="error">⚠ {error}</div>}
          <RouteList
            stops={stops} alternatives={alternatives}
            totalMinutes={totalMinutes} overBudget={overBudget}
            phase={phase} startPoint={startPoint}
            onSwapStop={handleSwapStop}
          />
        </div>
      </aside>
      <main className="map-area">
        <MapView
          stops={stops} startPoint={startPoint} onPickStart={setStartPoint}
          totalMinutes={totalMinutes} overBudget={overBudget} maxMinutes={maxMinutes}
        />
      </main>
    </div>
  );
}
