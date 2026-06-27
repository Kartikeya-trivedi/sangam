import { useMemo, useRef, useState } from "react";

import { reportLost } from "../api";
import type { Draft } from "../App";
import { ENREPORT, opt, report, t } from "../i18n";
import { AGE_BANDS, GENDERS, LOCATIONS, type GenderValue } from "../options";
import { ChipGroup } from "../components/ChipGroup";
import { SpeakHint } from "../components/SpeakHint";
import { useRecorder } from "../hooks/useRecorder";

type Status = "idle" | "submitting" | "success" | "error";

const WHEN_OPTIONS = [
  { value: "just_now", key: "justNow" as const },
  { value: "lt_1hr", key: "lt1hr" as const },
  { value: "today", key: "today" as const },
  { value: "earlier", key: "earlier" as const },
];

const MINOR = new Set(["0-12", "13-17"]);
const ELDERLY = new Set(["71-80", "80+"]);

// Screen 2 — the whole report in one focused, panic-friendly screen (tap-first).
// Owns its own submission state machine: idle → submitting → success | error → (retry).
export function ReportScreen({ draft, onRestart }: { draft: Draft; onRestart: () => void }) {
  const s = t(draft.language);
  const o = opt(draft.language);
  const r = report(draft.language);
  const { recording, start, stop } = useRecorder();

  const [gender, setGender] = useState<GenderValue | undefined>();
  const [ageBand, setAgeBand] = useState<string>();
  const [name, setName] = useState("");
  const [voice, setVoice] = useState<Blob | undefined>();
  const [lastSeen, setLastSeen] = useState<string>();
  const [whenSeen, setWhenSeen] = useState<string>();
  const [mobile, setMobile] = useState("");
  const [photo, setPhoto] = useState<Blob | undefined>();
  const [showAllLoc, setShowAllLoc] = useState(false);

  const [status, setStatus] = useState<Status>("idle");
  const [caseId, setCaseId] = useState("");
  const photoRef = useRef<HTMLInputElement>(null);

  // The only hard requirement: a callback number + at least one descriptor.
  const phoneOk = mobile.replace(/\D/g, "").length === 10;
  const hasDescriptor = !!(gender || ageBand || name.trim() || voice || lastSeen);
  const canSubmit = phoneOk && hasDescriptor && status !== "submitting";

  const priority = ageBand && MINOR.has(ageBand) ? "minor" : ageBand && ELDERLY.has(ageBand) ? "elderly" : null;

  const visibleLocations = useMemo(() => (showAllLoc ? LOCATIONS : LOCATIONS.slice(0, 6)), [showAllLoc]);

  async function toggleVoice() {
    if (!recording) {
      try {
        await start();
      } catch {
        /* mic unavailable — voice note is optional, ignore */
      }
      return;
    }
    setVoice(await stop());
  }

  async function submit() {
    setStatus("submitting");
    try {
      const res = await reportLost({
        audio: voice,
        photo,
        text: name.trim() || undefined,
        language_hint: draft.language,
        gender,
        age_band: ageBand,
        last_seen_location: lastSeen,
      });
      setCaseId(res.report_id || genCaseId());
      setStatus("success");
    } catch {
      setStatus("error");
    }
  }

  // --- Submission states ---------------------------------------------------
  if (status === "submitting") {
    return (
      <div className="screen state-screen">
        <div className="spinner" />
        <h1 className="state__title">{r.submitting}</h1>
        <p className="state__sub">{r.submittingSub}</p>
      </div>
    );
  }

  if (status === "success") {
    return (
      <div className="screen state-screen state-screen--success">
        <div className="state__badge state__badge--ok">✓</div>
        <h1 className="state__title">{r.successTitle}</h1>
        <div className="case-id">
          <span>{r.caseId}</span>
          <strong>{caseId}</strong>
        </div>
        <div className="next-steps">
          <p className="next-steps__h">{r.whatNow}</p>
          <ul>
            <li>🔎 {r.searchingCenters}</li>
            <li>🧩 {r.matching}</li>
            <li>📞 {r.willCall} ({formatMobile(mobile)})</li>
          </ul>
        </div>
        <button className="big-button" onClick={() => navigator.clipboard?.writeText(caseId)}>
          {r.saveCaseId}
        </button>
        <button className="big-button secondary" onClick={onRestart}>
          {r.reportAnother}
        </button>
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className="screen state-screen">
        <div className="state__badge state__badge--warn">⚠</div>
        <h1 className="state__title">{r.failTitle}</h1>
        <p className="state__sub">{r.failSaved}</p>
        <button className="big-button" onClick={submit}>{r.tryAgain}</button>
        <button className="big-button secondary" onClick={() => setStatus("idle")}>{r.saveOffline}</button>
        <button className="big-button secondary" onClick={onRestart}>{r.showVolunteer}</button>
      </div>
    );
  }

  // --- Idle: the form ------------------------------------------------------
  return (
    <div className="screen report">
      <div className="report__intro">
        <SpeakHint text={r.reportTitle} lang={draft.language} listenLabel={s.listenAgain} />
        <h1 className="screen__title">
          {r.reportTitle}
          <small>{ENREPORT.reportTitle}</small>
        </h1>
        <p className="report__reassure">🛡 {r.reportSub}</p>
      </div>

      {/* ① WHO */}
      <section className="field">
        <h2 className="field__q">① {r.who} <small>{ENREPORT.who}</small></h2>
        <label className="sub-q">{o.genderQ}</label>
        <ChipGroup columns={3} selected={gender} onSelect={setGender}
          chips={GENDERS.map((g) => ({ value: g.value, icon: g.icon, label: o[g.key] }))} />
        <label className="sub-q">{o.ageQ}</label>
        <ChipGroup columns={4} selected={ageBand} onSelect={setAgeBand}
          chips={AGE_BANDS.map((a) => ({ value: a.value, icon: a.icon, label: a.value }))} />
        <input className="text-input" placeholder={r.name} value={name} onChange={(e) => setName(e.target.value)} />
        <button type="button" className={`voice-note ${voice ? "voice-note--done" : ""} ${recording ? "voice-note--rec" : ""}`} onClick={toggleVoice}>
          {recording ? s.listening : voice ? `✓ ${r.voiceNote}` : r.voiceNote}
        </button>
      </section>

      {/* ② WHERE */}
      <section className="field">
        <h2 className="field__q">② {r.where} <small>{ENREPORT.where}</small></h2>
        <ChipGroup columns={2} selected={lastSeen} onSelect={setLastSeen}
          chips={visibleLocations.map((l) => ({ value: l, label: l }))} />
        {!showAllLoc && (
          <button type="button" className="link-btn" onClick={() => setShowAllLoc(true)}>
            ▾ {LOCATIONS.length - 6} more places
          </button>
        )}
        <label className="sub-q">{r.whenQ}</label>
        <ChipGroup columns={4} selected={whenSeen} onSelect={setWhenSeen}
          chips={WHEN_OPTIONS.map((w) => ({ value: w.value, label: r[w.key] }))} />
      </section>

      {/* ③ CONTACT (required) */}
      <section className="field field--required">
        <h2 className="field__q">③ {r.contact} <small>{ENREPORT.contact}</small></h2>
        <div className="phone-input">
          <span className="phone-input__cc">🇮🇳 +91</span>
          <input
            className="text-input text-input--phone"
            type="tel"
            inputMode="numeric"
            maxLength={10}
            placeholder="9876543210"
            value={mobile}
            onChange={(e) => setMobile(e.target.value.replace(/\D/g, "").slice(0, 10))}
          />
        </div>
        <p className="field__help">{r.mobileHelp}</p>
      </section>

      {/* ④ OPTIONAL */}
      <section className="field">
        <h2 className="field__q">④ {r.optional} <small>{ENREPORT.optional}</small></h2>
        <input ref={photoRef} type="file" accept="image/*" capture="environment" hidden
          onChange={(e) => { const f = e.target.files?.[0]; if (f) setPhoto(f); }} />
        <div className="optional-row">
          <button type="button" className={`opt-btn ${photo ? "opt-btn--done" : ""}`} onClick={() => photoRef.current?.click()}>
            {photo ? r.photoAdded : r.addPhoto}
          </button>
          <span className="opt-loc">{r.locationAuto}</span>
        </div>
      </section>

      {priority && (
        <div className={`priority priority--${priority}`}>
          {priority === "minor" ? r.priorityMinor : r.priorityElderly}
        </div>
      )}

      {/* Sticky submit */}
      <div className="submit-bar">
        <button className="big-button" disabled={!canSubmit} onClick={submit}>
          ✓ {r.submit}
        </button>
        <button className="link-btn link-btn--muted" onClick={onRestart}>{r.showVolunteer}</button>
      </div>
    </div>
  );
}

function genCaseId(): string {
  // Demo-only fallback when the backend doesn't return an id (matches dataset format).
  const n = Math.floor(10000 + (performance.now() * 7) % 89999);
  return `KMP-2027-${n}`;
}

function formatMobile(m: string): string {
  const d = m.replace(/\D/g, "");
  return d.length === 10 ? `${d.slice(0, 5)}-${d.slice(5)}` : d;
}
