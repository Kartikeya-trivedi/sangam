import { useState } from "react";

import type { ReportResponse } from "./api";
import type { Lang } from "./i18n";
import { LANGUAGES } from "./i18n";
import { LanguageScreen } from "./screens/LanguageScreen";
import { ReportScreen } from "./screens/ReportScreen";
import type { GenderValue } from "./options";

// Crisis-oriented flow: just two screens — Language → Report (single intake + states).
export type Step = "language" | "report";

export interface Draft {
  language: Lang; // e.g. "hi-IN"
  languageLabel: string; // e.g. "हिन्दी"
  audio?: Blob;
  text?: string;
  gender?: GenderValue;
  ageBand?: string;
  lastSeen?: string;
  photo?: Blob;
  report?: ReportResponse;
}

const FRESH: Draft = { language: "hi-IN", languageLabel: "हिन्दी" };

export default function App() {
  const [step, setStep] = useState<Step>("language");
  const [draft, setDraft] = useState<Draft>(FRESH);

  const merge = (d: Partial<Draft>) => setDraft((prev) => ({ ...prev, ...d }));

  // Persistent language pill — tap any time to switch language without losing your place.
  const currentLabel = LANGUAGES.find((l) => l.code === draft.language)?.label ?? draft.languageLabel;

  return (
    <div className="app">
      {step !== "language" && (
        <button className="lang-pill" onClick={() => setStep("language")}>
          🌐 {currentLabel} <span className="lang-pill__change">⟳</span>
        </button>
      )}

      {step === "language" && (
        <LanguageScreen
          onNext={(d) => {
            merge(d);
            setStep("report");
          }}
        />
      )}

      {step === "report" && (
        <ReportScreen
          draft={draft}
          onRestart={() => {
            setDraft({ ...FRESH, language: draft.language, languageLabel: currentLabel });
            setStep("language");
          }}
        />
      )}
    </div>
  );
}
