import { useEffect, useState } from "react";
import { searchLocation } from "../api";

export default function FilterPanel({
  startPoint, setStartPoint,
  allCategories,
  categories, toggleCategory,
  stopCount, setStopCount,
  maxMinutes, setMaxMinutes,
  onSubmit, loading, collapsed,
}) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState(null);
  const [locating, setLocating] = useState(false);
  const [expanded, setExpanded] = useState(true);

  useEffect(() => {
    if (collapsed) setExpanded(false);
  }, [collapsed]);

  const canSubmit = !!startPoint && !loading;

  async function handleSearch(e) {
    e.preventDefault();
    if (!query.trim()) return;
    setSearching(true);
    setSearchError(null);
    try {
      const data = await searchLocation(query.trim());
      setResults(data.results);
      if (data.results.length === 0) setSearchError("검색 결과가 없어요.");
    } catch (err) {
      setSearchError("검색에 실패했어요.");
    } finally {
      setSearching(false);
    }
  }

  function pickResult(r) {
    setStartPoint({ lat: r.lat, lon: r.lon, label: r.name });
    setResults([]);
    setQuery("");
  }

  function useMyLocation() {
    if (!navigator.geolocation) {
      setSearchError("이 브라우저는 위치 조회를 지원하지 않아요.");
      return;
    }
    setLocating(true);
    setSearchError(null);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setStartPoint({ lat: pos.coords.latitude, lon: pos.coords.longitude, label: "내 위치" });
        setLocating(false);
      },
      () => {
        setSearchError("위치 조회에 실패했어요. 권한을 허용했는지 확인해주세요.");
        setLocating(false);
      }
    );
  }

  if (collapsed && !expanded) {
    return (
      <div className="filter-summary">
        <div className="filter-summary-text">
          <span className="filter-summary-pin">📍 {startPoint?.label || "출발지"}</span>
          <span className="filter-summary-dot">·</span>
          <span>{maxMinutes}분</span>
          <span className="filter-summary-dot">·</span>
          <span>{categories.length ? categories.join(", ") : "전체"} {stopCount}곳</span>
        </div>
        <button type="button" className="filter-edit-btn" onClick={() => setExpanded(true)}>
          조건 수정
        </button>
      </div>
    );
  }

  return (
    <div className="filter-panel">
      <div className="field">
        <span>출발지</span>

        {startPoint ? (
          <div className="start-point-chip">
            📍 {startPoint.label || `${startPoint.lat.toFixed(5)}, ${startPoint.lon.toFixed(5)}`}
            <button type="button" className="clear-start" onClick={() => setStartPoint(null)}>변경</button>
          </div>
        ) : (
          <>
            <form className="search-row" onSubmit={handleSearch}>
              <input
                type="text"
                placeholder="장소 또는 주소 검색 (예: 서면역, 광안리해수욕장)"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
              <button type="submit" disabled={searching}>{searching ? "..." : "검색"}</button>
            </form>

            <button type="button" className="my-location-btn" onClick={useMyLocation} disabled={locating}>
              {locating ? "위치 확인 중..." : "📍 내 위치 사용"}
            </button>

            {searchError && <div className="search-error">{searchError}</div>}

            {results.length > 0 && (
              <ul className="search-results">
                {results.map((r, i) => (
                  <li key={i} onClick={() => pickResult(r)}>
                    <div className="result-name">{r.name}</div>
                    <div className="result-address">{r.address}</div>
                  </li>
                ))}
              </ul>
            )}

            <div className="start-point-hint">또는 지도를 클릭해서 출발지를 찍어도 돼요</div>
          </>
        )}
      </div>

      <label className="field">
        <span>여행 시간: {maxMinutes}분</span>
        <input
          type="range" min={30} max={180} step={10} value={maxMinutes}
          onChange={(e) => setMaxMinutes(Number(e.target.value))}
        />
      </label>

      <div className="field">
        <span>관심 카테고리</span>
        <div className="category-grid">
          <label className="category-chip">
            <input
              type="checkbox"
              checked={categories.length === 0}
              onChange={() => categories.forEach((c) => toggleCategory(c))}
            />
            전체
          </label>
          {allCategories.map((c) => (
            <label key={c} className="category-chip">
              <input
                type="checkbox"
                checked={categories.includes(c)}
                onChange={() => toggleCategory(c)}
              />
              {c === "관광명소" ? "관광명소(시장 포함)" : c}
            </label>
          ))}
        </div>
      </div>

      <div className="field">
        <span>방문 지점 수</span>
        <div className="segmented">
          {[3, 4, 5].map((n) => (
            <button
              key={n}
              type="button"
              className={stopCount === n ? "segment active" : "segment"}
              onClick={() => setStopCount(n)}
            >
              {n}곳
            </button>
          ))}
        </div>
      </div>

      <button
        className="submit-btn"
        onClick={() => { onSubmit(); setExpanded(false); }}
        disabled={!canSubmit}
      >
        {loading ? "루트 짜는 중..." : "루트 짜기"}
      </button>
    </div>
  );
}
