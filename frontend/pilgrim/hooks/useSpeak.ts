import { useCallback } from "react";

import { speakViaApi } from "../api";

// Spec §2.2 + implementation note: the app talks back. Try Bulbul (backend) first; fall
// back to the browser's built-in TTS so guidance still plays offline / without a key (§13).
// Call this on every screen mount (see <SpeakHint/>).
export function useSpeak() {
  return useCallback(async (text: string, lang = "hi-IN") => {
    if (!text) return;
    try {
      const url = await speakViaApi(text, lang);
      if (url) {
        await new Audio(url).play();
        return;
      }
    } catch {
      /* fall through to browser TTS */
    }
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      const u = new SpeechSynthesisUtterance(text);
      u.lang = lang;
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(u);
    }
  }, []);
}
