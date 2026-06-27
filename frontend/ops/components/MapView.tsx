import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { useEffect, useRef } from "react";

import { API_BASE } from "../api";

// Live map of open cases clustered by centre/ghat (spec §11). MapLibre + the free demo
// style — no Google key, reads better to a govt judge.
export function MapView() {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!ref.current) return;
    const map = new maplibregl.Map({
      container: ref.current,
      style: "https://demotiles.maplibre.org/style.json",
      center: [81.883, 25.432], // Sangam, Prayagraj
      zoom: 12,
    });

    map.on("load", async () => {
      const geo = await fetch(`${API_BASE}/ops/map`).then((r) => r.json());
      map.addSource("cases", { type: "geojson", data: geo, cluster: true, clusterRadius: 40 });
      map.addLayer({
        id: "clusters",
        type: "circle",
        source: "cases",
        filter: ["has", "point_count"],
        paint: { "circle-color": "#0a7d4b", "circle-radius": 18, "circle-opacity": 0.8 },
      });
      map.addLayer({
        id: "cluster-count",
        type: "symbol",
        source: "cases",
        filter: ["has", "point_count"],
        layout: { "text-field": "{point_count_abbreviated}", "text-size": 14 },
        paint: { "text-color": "#ffffff" },
      });
      map.addLayer({
        id: "points",
        type: "circle",
        source: "cases",
        filter: ["!", ["has", "point_count"]],
        // Minors drawn in a distinct color; never labeled publicly (§12).
        paint: {
          "circle-color": ["case", ["get", "is_minor"], "#7b1fa2", "#ef4444"],
          "circle-radius": 8,
          "circle-stroke-width": 2,
          "circle-stroke-color": "#fff",
        },
      });
    });

    return () => map.remove();
  }, []);

  return <div ref={ref} className="map" />;
}
