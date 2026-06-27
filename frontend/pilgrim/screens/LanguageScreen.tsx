import type { Draft } from "../App";
import { SpeakHint } from "../components/SpeakHint";
import { useSpeak } from "../hooks/useSpeak";

// Screen 1 — Language (spec §10). Each button shows the language in its OWN script;
// tapping speaks the name aloud to confirm (§2.12).
const LANGUAGES = [
  { code: "hi-IN", label: "हिन्दी" },
  { code: "ta-IN", label: "தமிழ்" },
  { code: "bn-IN", label: "বাংলা" },
  { code: "mr-IN", label: "मराठी" },
  { code: "te-IN", label: "తెలుగు" },
  { code: "gu-IN", label: "ગુજરાતી" },
  { code: "kn-IN", label: "ಕನ್ನಡ" },
  { code: "ml-IN", label: "മലയാളം" },
];

export function LanguageScreen({ onNext }: { onNext: (d: Partial<Draft>) => void }) {
  const speak = useSpeak();

  return (
    <div className="screen">
      <SpeakHint text="अपनी भाषा चुनिए" />
      <h1 className="screen__title">
        अपनी भाषा चुनिए
        <small>Choose your language</small>
      </h1>
      <div className="lang-grid">
        {LANGUAGES.map((l) => (
          <button
            key={l.code}
            className="lang-button"
            onClick={async () => {
              await speak(l.label, l.code); // §2.12 speak the name aloud
              onNext({ language: l.code, languageLabel: l.label });
            }}
          >
            {l.label}
          </button>
        ))}
      </div>
    </div>
  );
}
