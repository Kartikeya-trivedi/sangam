import { useEffect } from "react";

import { useSpeak } from "../hooks/useSpeak";

// Spec §2.2: auto-speak the screen's instruction on mount + a persistent "Listen again"
// button. Drop one at the top of every pilgrim screen.
export function SpeakHint({ text, lang = "hi-IN" }: { text: string; lang?: string }) {
  const speak = useSpeak();

  useEffect(() => {
    speak(text, lang);
  }, [text, lang, speak]);

  return (
    <button className="speak-hint" onClick={() => speak(text, lang)}>
      🔊 सुनिए / Listen again
    </button>
  );
}
