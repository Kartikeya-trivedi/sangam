import { useEffect, useRef, useState } from "react";

import { API_BASE, GOOGLE_MAPS_API_KEY, fetchCases, type CaseRow } from "../api";
import { loadGoogleMaps } from "../lib/gmaps";

type Step = { n: number; kind: string; title: string; detail: string; status: string; data: any };

const ICON: Record<string, string> = {
  assess: "📋", match: "🔍", predict: "🗺️", dispatch: "📢", verdict: "✅", error: "⚠️",
};

// Sahayak — the agentic reunification dispatcher. Pick an open lost case and watch Claude
// work it live: read → scan → predict the drift zone → dispatch → verdict.
export function SahayakView() {
  const [cases, setCases] = useState<CaseRow[]>([]);
  const [sel, setSel] = useState<CaseRow | null>(null);

  useEffect(() => {
    fetchCases()
      .then((d) => {
        const lost = (d.cases ?? [])
          .filter((c) => c.role === "lost")
          .sort((a, b) => (b.best_match_score ?? 0) - (a.best_match_score ?? 0));
        setCases(lost);
        setSel((s) => s ?? lost[0] ?? null);
      })
      .catch(() => {});
  }, []);

  return (
    <div className="sahayak">
      <aside className="sahayak__list">
        <div className="sahayak__listhead">🤖 Sahayak · open lost cases</div>
        {cases.map((c) => (
          <button
            key={c.id}
            className={`sacase ${sel?.id === c.id ? "sacase--on" : ""}`}
            onClick={() => setSel(c)}
          >
            <div className="sacase__top">
              <span className="sacase__name">{c.name ?? "Unidentified"}</span>
              {c.best_match_score != null && (
                <span className="sacase__score">{Math.round(c.best_match_score * 100)}%</span>
              )}
            </div>
            <div className="sacase__sum">
              <span className="sacase__id">#{c.id.slice(0, 8)}</span> ·{" "}
              {[c.age_band !== "unknown" && c.age_band, c.gender !== "unknown" && c.gender, c.last_seen_location]
                .filter(Boolean)
                .join(" · ") || "unidentified"}
            </div>
          </button>
        ))}
        {!cases.length && <div className="sahayak__empty">No open lost cases yet.</div>}
      </aside>

      <section className="sahayak__stage">
        {sel ? <SahayakRun key={sel.id} c={sel} /> : <div className="sahayak__empty">Select a case for Sahayak to work.</div>}
      </section>
    </div>
  );
}

function SahayakRun({ c }: { c: CaseRow }) {
  const [steps, setSteps] = useState<Step[]>([]);
  const [done, setDone] = useState(false);
  const mapRef = useRef<HTMLDivElement>(null);
  const gref = useRef<any>(null);
  const overlays = useRef<any[]>([]);

  // Live agent stream.
  useEffect(() => {
    setSteps([]);
    setDone(false);
    const es = new EventSource(`${API_BASE}/api/v1/ops/dispatch/${c.id}/stream`);
    es.onmessage = (e) => {
      try {
        const s = JSON.parse(e.data);
        if (s?.kind) setSteps((p) => [...p, s]);
      } catch {
        /* ignore keep-alive / malformed */
      }
    };
    es.addEventListener("done", () => {
      setDone(true);
      es.close();
    });
    es.onerror = () => {
      setDone(true);
      es.close();
    };
    return () => es.close();
  }, [c.id]);

  // Init the map once per case.
  useEffect(() => {
    if (!mapRef.current || !GOOGLE_MAPS_API_KEY) return;
    let cancelled = false;
    loadGoogleMaps(GOOGLE_MAPS_API_KEY)
      .then((g) => {
        if (cancelled || !mapRef.current) return;
        gref.current = {
          g,
          map: new g.maps.Map(mapRef.current, {
            center: { lat: 19.9975, lng: 73.7898 },
            zoom: 14,
            disableDefaultUI: true,
            zoomControl: true,
          }),
        };
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [c.id]);

  // Light up the predicted drift zones on the map when that step arrives.
  useEffect(() => {
    const predict = steps.find((s) => s.kind === "predict");
    const assess = steps.find((s) => s.kind === "assess");
    if (!predict || !gref.current) return;
    const { g, map } = gref.current;
    overlays.current.forEach((o) => o.setMap?.(null));
    overlays.current = [];
    const bounds = new g.maps.LatLngBounds();

    const origin = assess?.data?.origin ?? predict.data?.origin;
    if (origin) {
      overlays.current.push(
        new g.maps.Marker({
          map,
          position: origin,
          title: "Last seen",
          icon: { path: g.maps.SymbolPath.CIRCLE, scale: 6, fillColor: "#0f172a", fillOpacity: 1, strokeColor: "#fff", strokeWeight: 2 },
        }),
      );
      bounds.extend(origin);
    }
    (predict.data?.zones ?? []).forEach((z: any, i: number) => {
      const color = z.priority === "high" ? "#dc2626" : z.priority === "medium" ? "#f97316" : "#eab308";
      overlays.current.push(
        new g.maps.Circle({ map, center: { lat: z.lat, lng: z.lng }, radius: 280, fillColor: color, fillOpacity: 0.18, strokeColor: color, strokeWeight: 2 }),
      );
      overlays.current.push(
        new g.maps.Marker({
          map,
          position: { lat: z.lat, lng: z.lng },
          title: z.name,
          label: { text: String(i + 1), color: "#fff", fontWeight: "700" },
          icon: { path: g.maps.SymbolPath.CIRCLE, scale: 13, fillColor: color, fillOpacity: 0.95, strokeColor: "#fff", strokeWeight: 2 },
        }),
      );
      bounds.extend({ lat: z.lat, lng: z.lng });
    });
    if (!bounds.isEmpty()) map.fitBounds(bounds, 60);
  }, [steps]);

  return (
    <div className="sarun">
      <div className="sarun__timeline">
        <div className="sarun__case">
          Working <strong>{c.name ?? "an unnamed case"}</strong> · #{c.id.slice(0, 8)}
        </div>
        {steps.map((s) => (
          <div key={s.n} className={`sastep sastep--${s.kind}`}>
            <div className="sastep__icon">{ICON[s.kind] ?? "•"}</div>
            <div className="sastep__body">
              <div className="sastep__title">{s.title}</div>
              {s.detail && <div className="sastep__detail">{s.detail}</div>}

              {s.kind === "match" &&
                (s.data?.candidates ?? []).slice(0, 3).map((m: any) => (
                  <div key={m.candidate_id} className="samatch">
                    <span className={`sapill sapill--${m.confidence}`}>{Math.round(m.final_score * 100)}%</span>
                    {m.candidate_summary}
                  </div>
                ))}

              {s.kind === "predict" &&
                (s.data?.zones ?? []).map((z: any, i: number) => (
                  <div key={i} className={`sazone sazone--${z.priority}`}>
                    <b>
                      {i + 1}. {z.name}
                    </b>{" "}
                    — {z.reason}
                  </div>
                ))}

              {s.kind === "dispatch" && (
                <div className={`sadispatch ${s.data?.blocked ? "sadispatch--blocked" : ""}`}>
                  <div className="sadispatch__text">{s.data?.text}</div>
                  <div className="sadispatch__meta">
                    {(s.data?.zones ?? []).map((z: string) => (
                      <span key={z} className="satag">📍 {z}</span>
                    ))}
                  </div>
                  {s.data?.audio_url && <audio className="saaudio" controls src={s.data.audio_url} />}
                </div>
              )}

              {s.kind === "verdict" && s.data?.notify_family && (
                <div className="saverdict">📞 Notifying family · {s.data?.mobile}</div>
              )}
            </div>
          </div>
        ))}
        {!done && (
          <div className="sastep sastep--pending">
            <div className="sastep__icon">
              <span className="saspin" />
            </div>
            <div className="sastep__body">
              <div className="sastep__title">Sahayak is thinking…</div>
            </div>
          </div>
        )}
      </div>
      <div className="sarun__map">
        <div ref={mapRef} className="sarun__mapcanvas" />
      </div>
    </div>
  );
}
