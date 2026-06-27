import { useEffect, useState } from "react";

import { API_BASE } from "../api";
import { intent, type Lang } from "../i18n";

interface Centre {
  name: string;
  slug: string;
  lat: number | null;
  lng: number | null;
}
interface Desk extends Centre {
  km: number | null;
}

const NASHIK = { lat: 19.9975, lng: 73.7898 }; // venue fallback if location is blocked

function haversine(aLat: number, aLng: number, bLat: number, bLng: number): number {
  const R = 6371;
  const p = Math.PI / 180;
  const x =
    Math.sin(((bLat - aLat) * p) / 2) ** 2 +
    Math.cos(aLat * p) * Math.cos(bLat * p) * Math.sin(((bLng - aLng) * p) / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(x));
}

// Nearest lost-and-found (Kho-Ya-Paya) help desks. Uses geolocation; falls back to the
// venue centre when location is unavailable so the list is never empty.
export function NearbyDesks({ lang, limit = 3, primary = false }: { lang: Lang; limit?: number; primary?: boolean }) {
  const r = intent(lang);
  const [desks, setDesks] = useState<Desk[] | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = (lat: number, lng: number) => {
      fetch(`${API_BASE}/api/v1/centres`)
        .then((res) => res.json())
        .then((d) => {
          if (cancelled) return;
          const list: Desk[] = (d.centres ?? [])
            .map((c: Centre) => ({
              ...c,
              km: c.lat != null && c.lng != null ? haversine(lat, lng, c.lat, c.lng) : null,
            }))
            .sort((a: Desk, b: Desk) => (a.km ?? 1e9) - (b.km ?? 1e9))
            .slice(0, limit);
          setDesks(list);
        })
        .catch(() => setDesks([]));
    };
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => load(pos.coords.latitude, pos.coords.longitude),
        () => load(NASHIK.lat, NASHIK.lng),
        { timeout: 6000, maximumAge: 60000 },
      );
    } else {
      load(NASHIK.lat, NASHIK.lng);
    }
    return () => {
      cancelled = true;
    };
  }, [lang, limit]);

  const dist = (km: number) => (km < 1 ? `${Math.round(km * 1000)} m` : `${km.toFixed(1)} km`);

  return (
    <div className="nearby">
      <h2 className="nearby__title">{r.nearby}</h2>
      {desks === null && <div className="nearby__loading">{r.locating}</div>}
      {desks?.length === 0 && <div className="nearby__empty">—</div>}
      {desks?.map((d, i) => (
        <div key={d.slug} className={`desk ${primary && i === 0 ? "desk--primary" : ""}`}>
          <div>
            <div className="desk__name">{d.name}</div>
            {d.km != null && (
              <div className="desk__dist">
                {dist(d.km)} {r.away}
              </div>
            )}
          </div>
          {d.lat != null && d.lng != null && (
            <a
              className="desk__go"
              href={`https://www.google.com/maps/dir/?api=1&destination=${d.lat},${d.lng}`}
              target="_blank"
              rel="noreferrer"
            >
              ↗ {r.directions}
            </a>
          )}
        </div>
      ))}
    </div>
  );
}
