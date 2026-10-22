// shortcut: duplicates backend's haversine/walk-time formula (app/services/route.py) so
// swapping a stop can recompute leg times without a round trip; keep both in sync if tuned.
const WALK_SPEED_MPS = (4.5 * 1000) / 3600;
const WALK_DISTANCE_FACTOR = 1.3;

function haversineM(lat1, lon1, lat2, lon2) {
  const toRad = (d) => (d * Math.PI) / 180;
  const R = 6371000;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(a));
}

export function recomputeLegs(startPoint, stops) {
  let curLat = startPoint.lat;
  let curLon = startPoint.lon;
  let total = 0;
  const withLegs = stops.map((stop) => {
    const legMinutes =
      (haversineM(curLat, curLon, stop.lat, stop.lon) * WALK_DISTANCE_FACTOR) /
      WALK_SPEED_MPS /
      60;
    curLat = stop.lat;
    curLon = stop.lon;
    total += legMinutes;
    return { ...stop, leg_minutes: Math.round(legMinutes * 10) / 10 };
  });
  return { stops: withLegs, totalMinutes: Math.round(total * 10) / 10 };
}
