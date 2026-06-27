import { useRef } from "react";

import type { Draft } from "../App";
import { BigButton } from "../components/BigButton";
import { SpeakHint } from "../components/SpeakHint";

// Screen 3 — Photo, optional & skippable (spec §10). Never block progress on a photo.
export function PhotoScreen({
  draft,
  onNext,
  onBack,
}: {
  draft: Draft;
  onNext: (d: Partial<Draft>) => void;
  onBack: () => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div className="screen">
      <SpeakHint text="अगर फोटो है तो दिखाइए" lang={draft.language} />
      <h1 className="screen__title">
        फोटो है?
        <small>Have a photo? (optional)</small>
      </h1>

      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        capture="environment"
        hidden
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) onNext({ photo: f });
        }}
      />

      <BigButton icon="📷" label="Take / choose photo" labelHindi="फोटो दिखाइए" onPress={() => inputRef.current?.click()} />
      <BigButton
        label="No photo, continue"
        labelHindi="फोटो नहीं है, आगे बढ़िए"
        variant="secondary"
        onPress={() => onNext({})}
      />
      <BigButton label="Back" labelHindi="वापस" variant="secondary" onPress={onBack} />
    </div>
  );
}
