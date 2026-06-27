import { useEffect, useState } from "react";

import { fetchCases, type CaseRow, type StaffAlert } from "../api";

// Case queue + private minor/vulnerable alerts (spec §11, §12). Match-review/confirm is
// stubbed here as a per-row action — wire to /ops/confirm in Phase 3/4.
export function CaseQueue() {
  const [cases, setCases] = useState<CaseRow[]>([]);
  const [alerts, setAlerts] = useState<StaffAlert[]>([]);
  const [error, setError] = useState(false);

  useEffect(() => {
    fetchCases()
      .then((d) => {
        setCases(d.cases);
        setAlerts(d.staff_alerts);
      })
      .catch(() => setError(true));
  }, []);

  if (error) return <p className="error">Could not reach the backend at /ops/cases.</p>;

  return (
    <div className="queue">
      {alerts.length > 0 && (
        <section className="alerts">
          <h3>🔒 Private staff alerts — minors / vulnerable (guardian verification required)</h3>
          <ul>
            {alerts.map((a) => (
              <li key={a.id}>
                {a.type} · centre {a.centre_id ?? "—"} · verified: {a.guardian_verified ? "yes" : "no"}
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
            <th>Minor</th>
          </tr>
        </thead>
        <tbody>
          {cases.map((c) => (
            <tr key={c.id} className={c.is_minor ? "minor" : ""}>
              <td>{c.role}</td>
              <td>{c.native_summary}</td>
              <td>{c.age_band}</td>
              <td>{c.gender}</td>
              <td>{c.centre_id ?? "—"}</td>
              <td>{c.status}</td>
              <td>{c.is_minor ? "👶" : ""}</td>
            </tr>
          ))}
          {cases.length === 0 && (
            <tr>
              <td colSpan={7} className="empty">
                No cases yet — run <code>python scripts/seed_found_persons.py</code>.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
