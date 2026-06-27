import { useState } from "react";

import type { ReportResponse } from "./api";
import type { Lang } from "./i18n";
import { LANGUAGES } from "./i18n";
import { LanguageScreen } from "./screens/LanguageScreen";
import { IntentScreen } from "./screens/IntentScreen";
import { SelfLostScreen } from "./screens/SelfLostScreen";
import { ReportScreen } from "./screens/ReportScreen";
import type { GenderValue } from "./options";

// Flow: Language → Intent (someone lost / I am lost) → Report | Self-lost.
export type Step = "language" | "intent" | "selflost" | "report";

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
      {step === "language" && (
        <LanguageScreen
          onNext={(d) => {
            merge(d);
            setStep("intent");
          }}
        />
      )}

      {step === "intent" && (
        <IntentScreen
          lang={draft.language}
          onChoose={(mode) => setStep(mode === "report" ? "report" : "selflost")}
        />
      )}

      {step === "selflost" && <SelfLostScreen lang={draft.language} onBack={() => setStep("intent")} />}

      {step === "report" && (
        <ReportScreen
          draft={draft}
          onRestart={() => {
            setDraft({ ...FRESH, language: draft.language, languageLabel: currentLabel });
            setStep("intent");
          }}
        />
      )}
    </div>
  );
}
