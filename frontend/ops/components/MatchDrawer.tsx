import { useEffect, useState } from "react";

import {
  confirmMatch,
  fetchMatches,
  rejectMatch,
  type CaseRow,
  type MatchResult,
} from "../api";

// Slide-in panel for one case: fetches ranked candidates from GET /match/{id} and lets staff
// confirm (-> /ops/confirm) or reject (-> /ops/reject) each reunion. The clicked case's role
// decides which id is lost vs found; the candidate carries the opposite candidate_role.
function lostFoundIds(c: CaseRow, m: MatchResult): { lost: string; found: string } | null {
  // The clicked case and the candidate must be opposite roles for a valid pair.
  if (c.role === "lost" && m.candidate_role === "found") return { lost: c.id, found: m.candidate_id };
  if (c.role === "found" && m.candidate_role === "lost") return { lost: m.candidate_id, found: c.id };
  return null;
}

function pct(v: number): string {
  return `${Math.round(v * 100)}%`;
}

interface Props {
  case_: CaseRow;
  onClose: () => void;
  onActioned: () => void; // refresh the queue after a confirm/reject
}

export function MatchDrawer({ case_, onClose, onActioned }: Props) {
  const [candidates, setCandidates] = useState<MatchResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [busy, setBusy] = useState<string | null>(null); // candidate_id currently acting
  const [toast, setToast] = useState<{ kind: "ok" | "err"; text: string } | null>(null);

  function load() {
    setLoading(true);
    setError(false);
    fetchMatches(case_.id)
      .then((d) => setCandidates(d.candidates ?? []))
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }

  useEffect(load, [case_.id]);

  // Esc closes the drawer.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  async function onConfirm(m: MatchResult) {
    const pair = lostFoundIds(case_, m);
    if (!pair) {
      setToast({ kind: "err", text: "Cannot pair: both records have the same role." });
      return;
    }
    // Backend requires non-empty notes when either side is a minor, else it 400s.
    let notes = "";
    const minorInvolved = case_.is_minor || m.is_minor || m.requires_guardian_verification;
    if (minorInvolved) {
      const entered = window.prompt(
        "This reunion involves a minor — a short guardian-verification note is required to confirm:",
        "",
      );
      if (entered === null) return; // staffer cancelled
      notes = entered.trim();
      if (!notes) {
        setToast({ kind: "err", text: "A note is required for minor cases. Confirm cancelled." });
        return;
      }
    }
    setBusy(m.candidate_id);
    const res = await confirmMatch(pair.lost, pair.found, notes).catch(() => null);
    setBusy(null);
    if (res && res.ok) {
      setToast({ kind: "ok", text: "Reunion confirmed — both records marked reunited." });
      onActioned();
      onClose();
    } else if (res && res.status === 400) {
      // Most likely guardian_verification_required.
      setToast({ kind: "err", text: "Confirm rejected: guardian verification note required." });
    } else {
      setToast({ kind: "err", text: "Could not confirm — backend unreachable." });
    }
  }

  async function onReject(m: MatchResult) {
    const pair = lostFoundIds(case_, m);
    if (!pair) {
      setToast({ kind: "err", text: "Cannot pair: both records have the same role." });
      return;
    }
    const reason = window.prompt("Reason for rejecting this match (optional):", "") ?? "";
    setBusy(m.candidate_id);
    const res = await rejectMatch(pair.lost, pair.found, reason.trim()).catch(() => null);
    setBusy(null);
    if (res && res.ok) {
      setToast({ kind: "ok", text: "Match rejected and logged." });
      // A rejection doesn't change case status, but refresh so staff see fresh ranking.
      setCandidates((cs) => cs.filter((c) => c.candidate_id !== m.candidate_id));
      onActioned();
    } else {
      setToast({ kind: "err", text: "Could not reject — backend unreachable." });
    }
  }

  return (
    <>
      <div className="drawer__scrim" onClick={onClose} />
      <aside className="drawer" role="dialog" aria-label="Match review" aria-modal="true">
        <header className="drawer__head">
          <div>
            <h2>Match review</h2>
            <p className="drawer__case">
              <span className={`tag tag--${case_.role}`}>{case_.role}</span>
              {case_.is_minor && <span className="tag tag--minor">👶 minor</span>}
              <span className="drawer__id">#{case_.id.slice(0, 8)}</span>
              {" · "}centre {case_.centre_id ?? "—"}
            </p>
          </div>
          <button className="drawer__close" onClick={onClose} aria-label="Close">
            ✕
          </button>
        </header>

        {toast && (
          <div className={`drawer__toast drawer__toast--${toast.kind}`} role="status">
            {toast.text}
          </div>
        )}

        <div className="drawer__body">
          {loading && <p className="drawer__msg">Loading ranked candidates…</p>}
          {error && (
            <p className="drawer__msg error">
              Could not load matches.{" "}
              <button className="link" onClick={load}>
                Retry
              </button>
            </p>
          )}
          {!loading && !error && candidates.length === 0 && (
            <p className="drawer__msg">No candidate matches above threshold for this case yet.</p>
          )}

          {candidates.map((m) => (
            <article key={m.candidate_id} className="cand">
              <div className="cand__top">
                <span className={`pill pill--${m.confidence}`}>{m.confidence}</span>
                <span className="cand__score">{pct(m.final_score)}</span>
                <span className={`tag tag--${m.candidate_role}`}>{m.candidate_role}</span>
                {m.is_minor && <span className="tag tag--minor">👶</span>}
              </div>
              <p className="cand__summary">{m.candidate_summary || "(no summary)"}</p>
              <p className="cand__explain">{m.explanation}</p>
              <div className="cand__breakdown">
                {(
                  [
                    ["face", m.breakdown.face],
                    ["name", m.breakdown.name],
                    ["age", m.breakdown.age],
                    ["gender", m.breakdown.gender],
                    ["lang", m.breakdown.language],
                    ["clothes", m.breakdown.clothing],
                    ["marks", m.breakdown.distinguishing],
                    ["location", m.breakdown.location],
                    ["centre", m.breakdown.centre],
                    ["time", m.breakdown.time],
                  ] as [string, number | null][]
                )
                  .filter(([, v]) => v !== null && v !== undefined)
                  .map(([label, v]) => {
                    const val = v as number;
                    const band = val >= 0.66 ? "hi" : val >= 0.33 ? "mid" : "lo";
                    return (
                      <span key={label} className="bd" title={`${label}: ${pct(val)}`}>
                        <span className="bd__label">{label}</span>
                        <span className="bd__bar">
                          <span className={`bd__fill bd__fill--${band}`} style={{ width: pct(val) }} />
                        </span>
                      </span>
                    );
                  })}
              </div>
              <div className="cand__actions">
                <button
                  className="btn btn--confirm"
                  disabled={busy === m.candidate_id}
                  onClick={() => onConfirm(m)}
                >
                  ✓ Confirm reunion
                </button>
                <button
                  className="btn btn--reject"
                  disabled={busy === m.candidate_id}
                  onClick={() => onReject(m)}
                >
                  ✗ Reject
                </button>
              </div>
            </article>
          ))}
        </div>
      </aside>
    </>
  );
}
