import { useEffect, useRef } from "react";

import { API_BASE, GOOGLE_MAPS_API_KEY } from "../api";

// Nashik–Trimbakeshwar — the real Simhastha Kumbh venue.
const NASHIK = { lat: 19.9975, lng: 73.7898 };
const EMPTY = { type: "FeatureCollection", features: [] as unknown[] };

declare global {
  interface Window {
    google?: any;
    __setuGmaps?: Promise<any>;
  }
}

// Load the Google Maps JS API once (idempotent across mounts / StrictMode double-invoke).
function loadGoogleMaps(key: string): Promise<any> {
  if (window.google?.maps) return Promise.resolve(window.google);
  if (window.__setuGmaps) return window.__setuGmaps;
  window.__setuGmaps = new Promise((resolve, reject) => {
    const s = document.createElement("script");
    s.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(key)}&v=weekly`;
    s.async = true;
    s.defer = true;
    s.onload = () => resolve(window.google);
    s.onerror = () => reject(new Error("google_maps_load_failed"));
    document.head.appendChild(s);
  });
  return window.__setuGmaps;
}

function subset(fc: any, type: string): any[] {
  return (fc?.features ?? []).filter((f: any) => f?.properties?.feature_type === type);
}

function dot(google: any, color: string, scale: number) {
  return {
    path: google.maps.SymbolPath.CIRCLE,
    scale,
    fillColor: color,
    fillOpacity: 0.95,
    strokeColor: "#ffffff",
    strokeWeight: 2,
  };
}

export function MapView() {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!ref.current || !GOOGLE_MAPS_API_KEY) return;
    let cancelled = false;

    (async () => {
      let google: any;
      try {
        google = await loadGoogleMaps(GOOGLE_MAPS_API_KEY);
      } catch {
        return; // map unavailable -> the legend + dashboard still render (graceful)
      }
      if (cancelled || !ref.current) return;

      const map = new google.maps.Map(ref.current, {
        center: NASHIK,
        zoom: 13,
        mapTypeId: "roadmap",
        streetViewControl: false,
        mapTypeControl: true,
        fullscreenControl: true,
        clickableIcons: false,
      });
      const info = new google.maps.InfoWindow();

      const fc = await fetch(`${API_BASE}/api/v1/ops/map`)
        .then((r) => r.json())
        .catch(() => EMPTY);
      if (cancelled) return;

      // Risk hotspots — chokepoints as translucent halos coloured by risk level.
      subset(fc, "chokepoint").forEach((f) => {
        const [lng, lat] = f.geometry.coordinates;
        const risk = f.properties.risk_level;
        const color = risk === "very-high" ? "#dc2626" : risk === "high" ? "#f97316" : "#eab308";
        new google.maps.Circle({
          map,
          center: { lat, lng },
          radius: risk === "very-high" ? 450 : 320,
          fillColor: color,
          fillOpacity: 0.16,
          strokeColor: color,
          strokeOpacity: 0.55,
          strokeWeight: 1,
        });
      });

      // Police stations.
      subset(fc, "police_station").forEach((f) => {
        const [lng, lat] = f.geometry.coordinates;
        new google.maps.Marker({
          map,
          position: { lat, lng },
          title: f.properties.station_name ?? "Police",
          icon: dot(google, "#1d4ed8", 5),
          zIndex: 2,
        });
      });

      // Case clusters per centre — size by open volume; red if anyone is still waiting, else green.
      subset(fc, "case_cluster").forEach((f) => {
        const [lng, lat] = f.geometry.coordinates;
        const ol = Number(f.properties.open_lost ?? 0);
        const of = Number(f.properties.open_found ?? 0);
        const marker = new google.maps.Marker({
          map,
          position: { lat, lng },
          title: f.properties.centre_id ?? "Centre",
          icon: dot(google, ol > 0 ? "#ef4444" : "#0a7d4b", Math.min(20, 8 + (ol + of) * 0.6)),
          zIndex: 3,
        });
        marker.addListener("click", () => {
          info.setContent(
            `<div style="font:600 13px system-ui;color:#0f172a">${f.properties.centre_id ?? "Centre"}</div>` +
              `<div style="font:12px system-ui;color:#475569">${ol} waiting · ${of} in our care</div>`,
          );
          info.open({ map, anchor: marker });
        });
      });
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="mapwrap">
      <div ref={ref} className="map" />
      <div className="legend">
        <div><span className="dot last" /> Waiting families (open lost)</div>
        <div><span className="dot care" /> In our care (open found)</div>
        <div><span className="dot police" /> Police</div>
        <div><span className="hot" /> Risk hotspot</div>
        {!GOOGLE_MAPS_API_KEY && (
          <div className="nokey">Set VITE_GOOGLE_MAPS_API_KEY in frontend/ops/.env for the live map</div>
        )}
      </div>
    </div>
  );
}
