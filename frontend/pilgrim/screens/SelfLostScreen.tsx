import { useState } from "react";

import { API_BASE, CENTRE_ID } from "../api";
import { ENINTENT, intent, t, type Lang } from "../i18n";
import { NearbyDesks } from "../components/NearbyDesks";
import { SpeakHint } from "../components/SpeakHint";

// "I am lost" path. Calm the pilgrim, point them to the nearest help desk, and let them
// register themselves as FOUND there — so a family's lost-report matches them instantly.
export function SelfLostScreen({ lang, onBack }: { lang: Lang; onBack: () => void }) {
  const r = intent(lang);
  const s = t(lang);
  const [status, setStatus] = useState<"idle" | "saving" | "done">("idle");

  async function registerMe() {
    setStatus("saving");
    try {
      const fd = new FormData();
      fd.append("centre_id", CENTRE_ID);
      fd.append("text", "self-registered lost pilgrim seeking their family");
      fd.append("language_hint", lang);
      await fetch(`${API_BASE}/api/v1/report/found`, { method: "POST", body: fd });
    } catch {
      /* even offline, we reassure — the desk staff will help in person */
    }
    setStatus("done");
  }

  if (status === "done") {
    return (
      <div className="screen state-screen state-screen--success">
        <div className="state__badge state__badge--ok">✓</div>
        <h1 className="state__title">{r.registeredTitle}</h1>
        <p className="state__sub">{r.registeredSub}</p>
        <NearbyDesks lang={lang} limit={1} primary />
        <button className="back-link" onClick={onBack}>
          ← {r.back}
        </button>
      </div>
    );
  }

  return (
    <div className="screen">
      <SpeakHint text={`${r.selfTitle}. ${r.selfSub}`} lang={lang} listenLabel={s.listenAgain} />
      <div className="selflost__hero">
        <div className="selflost__safe" aria-hidden>
          🪔
        </div>
      </div>
      <h1 className="screen__title screen__title--center">
        {r.selfTitle}
        <small>{ENINTENT.selfTitle}</small>
      </h1>
      <p className="report__reassure selflost__sub">{r.selfSub}</p>

      <NearbyDesks lang={lang} primary />

      <button className="big-button register-btn" disabled={status === "saving"} onClick={registerMe}>
        {status === "saving" ? r.registering : `🪧 ${r.registerHere}`}
      </button>
      <button className="back-link" onClick={onBack}>
        ← {r.back}
      </button>
    </div>
  );
}
