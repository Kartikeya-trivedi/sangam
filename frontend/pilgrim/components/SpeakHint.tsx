import { useEffect } from "react";

import type { Lang } from "../i18n";
import { useSpeak } from "../hooks/useSpeak";

// Spec §2.2: auto-speak the screen's instruction on mount + a persistent "Listen again"
// button. `text` is in the user's language; the button label is localized too.
export function SpeakHint({
  text,
  listenLabel = "Listen again",
  lang = "hi-IN",
}: {
  text: string;
  listenLabel?: string;
  lang?: Lang;
}) {
  const speak = useSpeak();

  useEffect(() => {
    speak(text, lang);
  }, [text, lang, speak]);

  return (
    <button className="speak-hint" onClick={() => speak(text, lang)}>
      🔊 {listenLabel}
    </button>
  );
}
