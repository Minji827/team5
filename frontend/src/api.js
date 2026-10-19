const API_BASE = "http://localhost:8000";

async function request(path, options) {
  const res = await fetch(`${API_BASE}${path}`, options);
  if (!res.ok) {
    throw new Error(`API ${path} failed: ${res.status}`);
  }
  return res.json();
}

export function getCategories() {
  return request("/api/spots/categories");
}

export function searchLocation(query) {
  return request(`/api/geocode?query=${encodeURIComponent(query)}`);
}

export function getRecommendation({ startLat, startLon, categories, stopCount, maxMinutes }) {
  return request("/api/recommend", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      start_lat: startLat,
      start_lon: startLon,
      categories: categories && categories.length ? categories : null,
      stop_count: stopCount,
      max_minutes: maxMinutes,
    }),
  });
}
