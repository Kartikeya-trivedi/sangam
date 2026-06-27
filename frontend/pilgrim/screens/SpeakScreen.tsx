import { useState } from "react";

import type { Draft } from "../App";
import { BigButton } from "../components/BigButton";
import { MicButton } from "../components/MicButton";
import { SpeakHint } from "../components/SpeakHint";
import { useRecorder } from "../hooks/useRecorder";

// Screen 2 — Speak (spec §10). One huge mic; typing is an optional fallback only (§2.1).
export function SpeakScreen({
  draft,
  onNext,
  onBack,
}: {
  draft: Draft;
  onNext: (d: Partial<Draft>) => void;
  onBack: () => void;
}) {
  const { recording, start, stop } = useRecorder();
  const [typing, setTyping] = useState(false);
  const [text, setText] = useState("");

  async function toggleMic() {
    if (!recording) {
      await start();
      return;
    }
    const audio = await stop();
    onNext({ audio });
  }

  return (
    <div className="screen">
      <SpeakHint text="किसे ढूंढ रहे हैं? बोलिए।" lang={draft.language} />
      <h1 className="screen__title">
        किसे ढूंढ रहे हैं?
        <small>Who are you looking for?</small>
      </h1>

      <MicButton recording={recording} onPress={toggleMic} />

      {typing ? (
        <div className="typed-fallback">
          <textarea
            value={text}
            placeholder="यहाँ लिखिए… (optional)"
            onChange={(e) => setText(e.target.value)}
          />
          <BigButton
            label="Continue"
            labelHindi="आगे बढ़िए"
            onPress={() => onNext({ text })}
            disabled={!text.trim()}
          />
        </div>
      ) : (
        <BigButton label="Type instead" labelHindi="टाइप करें" variant="secondary" onPress={() => setTyping(true)} />
      )}

      <BigButton label="Back" labelHindi="वापस" variant="secondary" onPress={onBack} />
    </div>
  );
}
