import { useEffect, useState } from "react";
import FilterPanel from "./components/FilterPanel";
import MapView from "./components/MapView";
import RouteList from "./components/RouteList";
import { getCategories, getRecommendation } from "./api";
import "./App.css";

export default function App() {
  const [startPoint, setStartPoint] = useState(null);
  const [allCategories, setAllCategories] = useState([]);
  const [categories, setCategories] = useState([]);
  const [stopCount, setStopCount] = useState(5);
  const [maxMinutes, setMaxMinutes] = useState(90);
  const [stops, setStops] = useState([]);
  const [totalMinutes, setTotalMinutes] = useState(0);
  const [overBudget, setOverBudget] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hasSearched, setHasSearched] = useState(false);

  useEffect(() => {
    getCategories().then(setAllCategories).catch(() => setAllCategories([]));
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
      setTotalMinutes(data.total_minutes);
      setOverBudget(data.over_budget);
    } catch (e) {
      setError("추천을 불러오지 못했습니다. 백엔드가 실행 중인지 확인해주세요.");
    } finally {
      setLoading(false);
    }
  }

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
          />
          {error && <div className="error">⚠ {error}</div>}
          <RouteList
            stops={stops} totalMinutes={totalMinutes} overBudget={overBudget}
            loading={loading} hasSearched={hasSearched} startPoint={startPoint}
          />
        </div>
      </aside>
      <main className="map-area">
        <MapView stops={stops} startPoint={startPoint} onPickStart={setStartPoint} />
      </main>
    </div>
  );
}
