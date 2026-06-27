import { useState } from "react";

import { announce, type AnnounceResult, type MatchResult } from "../api";
import type { Lang } from "../i18n";
import { report } from "../i18n";
import { useSpeak } from "../hooks/useSpeak";

// Ranked candidate cards shown after a successful report (§10 screen 5).
// Each card: candidate_summary, a color-coded confidence pill, the "why it matched"
// explanation, the best score, and a per-candidate Connect action.
// ADULT  -> Connect calls POST /announce and shows the announcement_text (+ plays audio).
// MINOR  -> announce returns 403; we never expose Connect, we show the guardian path (§12).
export function MatchResults({ candidates, lang }: { candidates: MatchResult[]; lang: Lang }) {
  const r = report(lang);

  if (candidates.length === 0) {
    return (
      <div className="results-empty" role="status">
        <div className="results-empty__icon" aria-hidden>🔎</div>
        <p className="results-empty__title">{r.noMatchesTitle}</p>
        <p className="results-empty__sub">{r.noMatchesSub}</p>
      </div>
    );
  }

  return (
    <div className="results">
      <p className="results__count" role="status">🧩 {r.matchesCount(candidates.length)}</p>
      <div className="cards">
        {candidates.map((c, i) => (
          <CandidateCard key={c.candidate_id} candidate={c} rank={i + 1} lang={lang} />
        ))}
      </div>
    </div>
  );
}

const CONFIDENCE: Record<MatchResult["confidence"], { cls: string; key: "confHigh" | "confMedium" | "confLow" }> = {
  high: { cls: "high", key: "confHigh" },
  medium: { cls: "medium", key: "confMedium" },
  low: { cls: "low", key: "confLow" },
};

type ConnectState =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "announced"; result: AnnounceResult }
  | { kind: "guardian" }
  | { kind: "error" };

function CandidateCard({ candidate, rank, lang }: { candidate: MatchResult; rank: number; lang: Lang }) {
  const r = report(lang);
  const speak = useSpeak();
  const [state, setState] = useState<ConnectState>({ kind: "idle" });

  const conf = CONFIDENCE[candidate.confidence] ?? CONFIDENCE.low;
  const scorePct = Math.round(candidate.final_score * 100);

  async function onConnect() {
    setState({ kind: "loading" });
    try {
      const result = await announce(candidate.candidate_id, lang);
      if (result.blocked || result.action_required === "guardian_verification") {
        setState({ kind: "guardian" });
        return;
      }
      setState({ kind: "announced", result });
      if (result.audio_url) {
        new Audio(result.audio_url).play().catch(() => {});
      } else if (result.announcement_text) {
        speak(result.announcement_text, lang);
      }
    } catch {
      setState({ kind: "error" });
    }
  }

  return (
    <div className={`card card--candidate ${candidate.is_minor ? "card--minor" : ""}`}>
      <div className="card__head">
        <span className="card__rank">#{rank}</span>
        <span className={`conf-pill conf-pill--${conf.cls}`}>{r[conf.key]}</span>
        {candidate.is_minor && <span className="card__minor-badge">⚠️ {r.minorBadge}</span>}
      </div>

      <div className="card__summary">{candidate.candidate_summary}</div>

      <div className="card__why">
        <span className="card__why-label">{r.whyMatched}</span>
        <p className="card__reason">{candidate.explanation}</p>
      </div>

      <div className="card__score" aria-label={`${r.bestScore} ${scorePct}%`}>
        <div className="card__score-row">
          <span className="card__score-label">{r.bestScore}</span>
          <strong className={`card__score-val card__score-val--${conf.cls}`}>{scorePct}%</strong>
        </div>
        <div className="score-bar" role="presentation">
          <div className={`score-bar__fill score-bar__fill--${conf.cls}`} style={{ width: `${scorePct}%` }} />
        </div>
      </div>

      {/* Action / verification zone ---------------------------------------- */}
      {candidate.is_minor || state.kind === "guardian" ? (
        <div className="guardian-box" role="status">
          <p className="guardian-box__title">🛡 {r.guardianTitle}</p>
          <p className="guardian-box__msg">{r.guardianMsg}</p>
        </div>
      ) : state.kind === "announced" ? (
        <div className="announce-box" role="status">
          <p className="announce-box__title">✓ {r.announceDone}</p>
          {state.result.announcement_text && (
            <p className="announce-box__text">{state.result.announcement_text}</p>
          )}
          <button
            type="button"
            className="big-button secondary"
            onClick={() =>
              state.result.audio_url
                ? new Audio(state.result.audio_url).play().catch(() => {})
                : speak(state.result.announcement_text ?? "", lang)
            }
          >
            {r.playAnnounce}
          </button>
        </div>
      ) : (
        <>
          <button
            type="button"
            className="big-button card__connect"
            disabled={state.kind === "loading"}
            onClick={onConnect}
          >
            {state.kind === "loading" ? r.connecting : r.connect}
          </button>
          {state.kind === "error" && <p className="card__error" role="alert">⚠ {r.announceFailed}</p>}
        </>
      )}
    </div>
  );
}
