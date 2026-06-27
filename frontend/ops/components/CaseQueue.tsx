import { useEffect, useState } from "react";

import {
  fetchCases,
  fetchNotifications,
  fetchStats,
  type CaseRow,
  type CasesSummary,
  type OpsNotification,
  type OpsStats,
} from "../api";
import { MatchDrawer } from "./MatchDrawer";

// Case queue + private minor/vulnerable alerts (spec §11, §12). Clicking a row opens a match
// drawer that fetches GET /match/{id} and lets staff confirm/reject reunions; the queue refreshes
// after any action. A stats header surfaces GET /ops/stats; new notifications come from
// GET /ops/notifications. Minor cases (which need guardian verification) are derived client-side.
function caseSummary(c: CaseRow): string {
  return [
    c.age_band !== "unknown" ? c.age_band : "",
    c.gender !== "unknown" ? c.gender : "",
    c.name ?? "",
    (c.clothing ?? []).join(", "),
    (c.languages_spoken ?? []).join("/"),
  ]
    .filter((s) => s)
    .join(" · ");
}

function StatsHeader({ summary, stats, notifications }: {
  summary: CasesSummary | null;
  stats: OpsStats | null;
  notifications: number;
}) {
  const open = summary?.total_open ?? stats?.overall.total_open ?? 0;
  const matched = summary?.total_matched ?? stats?.overall.by_status.matched ?? 0;
  const reunited = summary?.total_reunited ?? stats?.overall.total_reunited ?? 0;
  const minors = summary?.total_minor_open ?? 0;
  return (
    <section className="kpis" aria-label="Operational summary">
      <div className="kpi">
        <span className="kpi__num">{open}</span>
        <span className="kpi__label">Open</span>
      </div>
      <div className="kpi">
        <span className="kpi__num">{matched}</span>
        <span className="kpi__label">Matched</span>
      </div>
      <div className="kpi kpi--good">
        <span className="kpi__num">{reunited}</span>
        <span className="kpi__label">Reunited</span>
      </div>
      <div className="kpi kpi--minor">
        <span className="kpi__num">{minors}</span>
        <span className="kpi__label">Minors open</span>
      </div>
      {notifications > 0 && (
        <div className="kpi kpi--alert">
          <span className="kpi__num">🔔 {notifications}</span>
          <span className="kpi__label">New alerts</span>
        </div>
      )}
    </section>
  );
}

export function CaseQueue() {
  const [cases, setCases] = useState<CaseRow[]>([]);
  const [summary, setSummary] = useState<CasesSummary | null>(null);
  const [stats, setStats] = useState<OpsStats | null>(null);
  const [notifications, setNotifications] = useState<OpsNotification[]>([]);
  const [error, setError] = useState(false);
  const [selected, setSelected] = useState<CaseRow | null>(null);

  function load() {
    fetchCases()
      .then((d) => {
        setCases(d.cases ?? []);
        setSummary(d.summary ?? null);
        setError(false);
      })
      .catch(() => setError(true));
    // Stats / notifications are best-effort enhancements; never block the queue on them.
    fetchStats().then(setStats).catch(() => undefined);
    fetchNotifications().then(setNotifications).catch(() => undefined);
  }

  useEffect(load, []);

  if (error) return <p className="error">Could not reach the backend at /api/v1/ops/cases.</p>;

  const rows = cases ?? [];
  const minors = rows.filter((c) => c.is_minor);

  return (
    <div className="queue">
      <StatsHeader summary={summary} stats={stats} notifications={notifications.length} />

      {minors.length > 0 && (
        <section className="alerts">
          <h3>🔒 Private staff alerts — minors / vulnerable (guardian verification required)</h3>
          <ul>
            {minors.map((c) => (
              <li key={c.id}>
                {c.age_band} · {c.gender} · centre {c.centre_id ?? "—"}
              </li>
            ))}
          </ul>
        </section>
      )}

      <table>
        <thead>
          <tr>
            <th>Role</th>
            <th>Summary</th>
            <th>Age</th>
            <th>Gender</th>
            <th>Centre</th>
            <th>Status</th>
            <th>Matches</th>
            <th>Minor</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((c) => (
            <tr
              key={c.id}
              className={`${c.is_minor ? "minor " : ""}clickable`}
              tabIndex={0}
              role="button"
              aria-label={`Review matches for ${c.role} case at ${c.centre_id ?? "unknown centre"}`}
              onClick={() => setSelected(c)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  setSelected(c);
                }
              }}
            >
              <td>{c.role}</td>
              <td>{caseSummary(c)}</td>
              <td>{c.age_band}</td>
              <td>{c.gender}</td>
              <td>{c.centre_id ?? "—"}</td>
              <td>{c.status}</td>
              <td>
                {c.match_count > 0 ? (
                  <span className="matchcount">
                    {c.match_count}
                    {c.best_match_score != null && (
                      <em> · {Math.round(c.best_match_score * 100)}%</em>
                    )}
                  </span>
                ) : (
                  "—"
                )}
              </td>
              <td>{c.is_minor ? "👶" : ""}</td>
            </tr>
          ))}
          {rows.length === 0 && (
            <tr>
              <td colSpan={8} className="empty">
                No cases yet — run <code>python scripts/seed_found_persons.py</code>.
              </td>
            </tr>
          )}
        </tbody>
      </table>

      {selected && (
        <MatchDrawer
          case_={selected}
          onClose={() => setSelected(null)}
          onActioned={load}
        />
      )}
    </div>
  );
}
