import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { useEffect, useRef } from "react";

import { API_BASE, MAPS_API_KEY } from "../api";

// Nashik–Trimbakeshwar (lng, lat).
const NASHIK: [number, number] = [73.7898, 19.9975];

const EMPTY = { type: "FeatureCollection", features: [] } as const;

// With a MapTiler/Mapbox key, use a real street basemap; else the free MapLibre demo tiles.
function styleUrl(): string {
  if (MAPS_API_KEY) return `https://api.maptiler.com/maps/streets-v2/style.json?key=${MAPS_API_KEY}`;
  return "https://demotiles.maplibre.org/style.json";
}

const KIND_LABEL: Record<string, string> = {
  last_seen: "Last seen here",
  in_care: "In our care",
  reunited: "Reunited",
};

export function MapView() {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!ref.current) return;
    const map = new maplibregl.Map({ container: ref.current, style: styleUrl(), center: NASHIK, zoom: 12 });

    map.on("load", async () => {
      const [cases, geo] = await Promise.all([
        fetch(`${API_BASE}/ops/map`).then((r) => r.json()).catch(() => EMPTY),
        fetch(`${API_BASE}/ops/geo`).then((r) => r.json()).catch(() => ({ hotspots: EMPTY, police: EMPTY })),
      ]);

      // Risk hotspots (soft red halos) — where separations cluster.
      map.addSource("hotspots", { type: "geojson", data: geo.hotspots ?? EMPTY });
      map.addLayer({
        id: "hotspots",
        type: "circle",
        source: "hotspots",
        paint: { "circle-radius": 28, "circle-color": "#ef4444", "circle-opacity": 0.15, "circle-stroke-color": "#ef4444", "circle-stroke-width": 1 },
      });

      // Police stations.
      map.addSource("police", { type: "geojson", data: geo.police ?? EMPTY });
      map.addLayer({
        id: "police",
        type: "circle",
        source: "police",
        paint: { "circle-radius": 5, "circle-color": "#1d4ed8", "circle-stroke-color": "#fff", "circle-stroke-width": 1 },
      });

      // Cases — colored by kind; minors are a distinct redacted color (§12).
      map.addSource("cases", { type: "geojson", data: cases });
      map.addLayer({
        id: "cases",
        type: "circle",
        source: "cases",
        paint: {
          "circle-radius": 8,
          "circle-stroke-width": 2,
          "circle-stroke-color": "#fff",
          "circle-color": [
            "case",
            ["get", "is_minor"], "#7b1fa2",
            ["==", ["get", "kind"], "reunited"], "#16a34a",
            ["==", ["get", "kind"], "in_care"], "#0a7d4b",
            ["==", ["get", "kind"], "last_seen"], "#ef4444",
            "#64748b",
          ],
        },
      });

      map.on("click", "cases", (e) => {
        const f = e.features?.[0];
        if (!f) return;
        const p = f.properties as Record<string, string>;
        const coords = (f.geometry as { coordinates: [number, number] }).coordinates;
        new maplibregl.Popup()
          .setLngLat(coords)
          .setHTML(
            `<strong>${KIND_LABEL[p.kind] ?? p.kind}</strong><br/>${p.label}` +
              `<br/><small>status: ${p.status}${p.centre_id ? ` · ${p.centre_id}` : ""}</small>`,
          )
          .addTo(map);
      });
      map.on("mouseenter", "cases", () => (map.getCanvas().style.cursor = "pointer"));
      map.on("mouseleave", "cases", () => (map.getCanvas().style.cursor = ""));
    });

    return () => map.remove();
  }, []);

  return (
    <div className="mapwrap">
      <div ref={ref} className="map" />
      <div className="legend">
        <div><span className="dot last" /> Last seen (lost)</div>
        <div><span className="dot care" /> In our care (found)</div>
        <div><span className="dot reunited" /> Reunited</div>
        <div><span className="dot minor" /> Protected (minor)</div>
        <div><span className="dot police" /> Police</div>
        <div><span className="hot" /> Risk hotspot</div>
        {!MAPS_API_KEY && <div className="nokey">Free basemap · set VITE_MAPS_API_KEY for streets</div>}
      </div>
    </div>
  );
}
