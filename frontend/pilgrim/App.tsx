import { useState } from "react";

import type { ReportResponse } from "./api";
import { ConfirmScreen } from "./screens/ConfirmScreen";
import { LanguageScreen } from "./screens/LanguageScreen";
import { PhotoScreen } from "./screens/PhotoScreen";
import { ResultScreen } from "./screens/ResultScreen";
import { SpeakScreen } from "./screens/SpeakScreen";

// One action per screen, strictly linear (spec §2.3): Language → Speak → Photo → Confirm → Result.
export type Step = "language" | "speak" | "photo" | "confirm" | "result";

export interface Draft {
  language: string; // e.g. "hi-IN"
  languageLabel: string; // e.g. "हिन्दी"
  audio?: Blob;
  text?: string; // typed fallback (§2.1)
  photo?: Blob;
  report?: ReportResponse;
}

const FRESH: Draft = { language: "hi-IN", languageLabel: "हिन्दी" };

export default function App() {
  const [step, setStep] = useState<Step>("language");
  const [draft, setDraft] = useState<Draft>(FRESH);

  const merge = (d: Partial<Draft>) => setDraft((prev) => ({ ...prev, ...d }));

  return (
    <div className="app">
      {step === "language" && (
        <LanguageScreen
          onNext={(d) => {
            merge(d);
            setStep("speak");
          }}
        />
      )}
      {step === "speak" && (
        <SpeakScreen
          draft={draft}
          onNext={(d) => {
            merge(d);
            setStep("photo");
          }}
          onBack={() => setStep("language")}
        />
      )}
      {step === "photo" && (
        <PhotoScreen
          draft={draft}
          onNext={(d) => {
            merge(d);
            setStep("confirm");
          }}
          onBack={() => setStep("speak")}
        />
      )}
      {step === "confirm" && (
        <ConfirmScreen
          draft={draft}
          onConfirmed={(d) => {
            merge(d);
            setStep("result");
          }}
          onRedo={() => setStep("speak")}
        />
      )}
      {step === "result" && (
        <ResultScreen
          draft={draft}
          onRestart={() => {
            setDraft(FRESH);
            setStep("language");
          }}
        />
      )}
    </div>
  );
}
