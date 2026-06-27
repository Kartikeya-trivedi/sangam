import type { Draft } from "../App";
import { EN, LANGUAGES } from "../i18n";
import { useSpeak } from "../hooks/useSpeak";

// Screen 1 — Language (spec §10). Each button shows the language in its OWN script;
// tapping speaks the name aloud to confirm (§2.12). This is the front door to the
// whole multilingual experience — pick once, the entire app + voice follow.
export function LanguageScreen({ onNext }: { onNext: (d: Partial<Draft>) => void }) {
  const speak = useSpeak();

  return (
    <div className="screen screen--language">
      <h1 className="screen__title screen__title--center">
        अपनी भाषा चुनिए
        <small>{EN.chooseLanguage}</small>
      </h1>
      <div className="lang-grid">
        {LANGUAGES.map((l) => (
          <button
            key={l.code}
            className="lang-button"
            onClick={() => {
              speak(l.label, l.code); // §2.12 speak the name aloud (fire-and-forget so the tap is instant)
              onNext({ language: l.code, languageLabel: l.label });
            }}
          >
            <span className="lang-button__native">{l.label}</span>
            <span className="lang-button__en">{l.english}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
