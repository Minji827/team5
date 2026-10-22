import { useEffect } from "react";
import { MapContainer, TileLayer, Marker, Popup, Polyline, ZoomControl, useMap, useMapEvents } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { BUSAN_CENTER } from "../constants";

function numberedIcon(n) {
  return L.divIcon({
    className: "stop-marker",
    html: `<div class="stop-marker-inner">${n}</div>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  });
}

const startIcon = L.divIcon({
  className: "start-marker",
  html: `<div class="start-marker-inner">S</div>`,
  iconSize: [28, 28],
  iconAnchor: [14, 14],
});

function FlyToStart({ startPoint }) {
  const map = useMap();
  useEffect(() => {
    if (startPoint) {
      map.flyTo([startPoint.lat, startPoint.lon], 15, { duration: 0.8 });
    }
  }, [startPoint, map]);
  return null;
}

function ClickHandler({ onPick }) {
  useMapEvents({
    click(e) {
      onPick({ lat: e.latlng.lat, lon: e.latlng.lng });
    },
  });
  return null;
}

export default function MapView({ stops, startPoint, onPickStart, totalMinutes, overBudget, maxMinutes }) {
  const path = stops.some((s) => s.leg_path?.length)
    ? stops.flatMap((s) => s.leg_path || [])
    : startPoint
    ? [[startPoint.lat, startPoint.lon], ...stops.map((s) => [s.lat, s.lon])]
    : [];
  const progressPct = maxMinutes ? Math.min(100, Math.round((totalMinutes / maxMinutes) * 100)) : 0;

  return (
    <>
      <MapContainer center={BUSAN_CENTER} zoom={13} className="map" zoomControl={false}>
        <TileLayer
          attribution='&copy; OpenStreetMap contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <ClickHandler onPick={onPickStart} />
        <FlyToStart startPoint={startPoint} />
        <ZoomControl position="bottomright" />

        {path.length > 1 && <Polyline positions={path} color="#0d9488" weight={4} opacity={0.9} />}

        {startPoint && (
          <Marker position={[startPoint.lat, startPoint.lon]} icon={startIcon}>
            <Popup>출발지</Popup>
          </Marker>
        )}

        {stops.map((stop) => (
          <Marker key={stop.id} position={[stop.lat, stop.lon]} icon={numberedIcon(stop.order)}>
            <Popup>
              <strong>{stop.order}. {stop.name}</strong><br />
              {stop.category} · {stop.address}<br />
              이전 지점에서 도보 {stop.leg_minutes}분 (추정)
            </Popup>
          </Marker>
        ))}
      </MapContainer>

      {stops.length > 0 && (
        <div className="map-status-card">
          <div className="map-status-row">
            <span>루트 현황</span>
            <span className={overBudget ? "map-status-pct over" : "map-status-pct"}>
              총 {totalMinutes}분{maxMinutes ? ` / ${maxMinutes}분` : ""}
            </span>
          </div>
          <div className="map-status-bar">
            <div
              className={overBudget ? "map-status-fill over" : "map-status-fill"}
              style={{ width: `${progressPct}%` }}
            />
          </div>
        </div>
      )}
    </>
  );
}
