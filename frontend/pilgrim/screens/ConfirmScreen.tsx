import { useEffect, useState } from "react";

import { reportLost, type ReportResponse } from "../api";
import type { Draft } from "../App";
import { BigButton } from "../components/BigButton";
import { SpeakHint } from "../components/SpeakHint";
import { useSpeak } from "../hooks/useSpeak";

// Screen 4 — Confirm (spec §10, §2.8). Submits the report, reads the captured profile
// back aloud, and asks ✓ हाँ / ✗ नहीं before showing results.
export function ConfirmScreen({
  draft,
  onConfirmed,
  onRedo,
}: {
  draft: Draft;
  onConfirmed: (d: Partial<Draft>) => void;
  onRedo: () => void;
}) {
  const speak = useSpeak();
  const [report, setReport] = useState<ReportResponse | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let alive = true;
    (async () => {
      speak("ढूंढ रहे हैं…", draft.language); // §2.9 spoken processing feedback
      try {
        const r = await reportLost({
          audio: draft.audio,
          photo: draft.photo,
          text: draft.text,
          language_hint: draft.language,
        });
        if (!alive) return;
        setReport(r);
        await speak(`आप ढूंढ रहे हैं: ${r.native_summary} — सही है?`, draft.language);
      } catch {
        if (!alive) return;
        setError(true);
        await speak("समझ नहीं आया, फिर से बोलिए", draft.language); // §2.7 plain-language error
      }
    })();
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (error) {
    return (
      <div className="screen">
        <h1 className="screen__title">
          समझ नहीं आया
          <small>Didn't catch that</small>
        </h1>
        <BigButton icon="🎤" label="Speak again" labelHindi="फिर से बोलिए" onPress={onRedo} />
      </div>
    );
  }

  if (!report) {
    return (
      <div className="screen">
        <div className="processing">ढूंढ रहे हैं… 🔎</div>
      </div>
    );
  }

  return (
    <div className="screen">
      <SpeakHint text={`आप ढूंढ रहे हैं: ${report.native_summary} — सही है?`} lang={draft.language} />
      <h1 className="screen__title">
        सही है?
        <small>Is this correct?</small>
      </h1>
      <p className="readback">{report.native_summary}</p>
      <BigButton icon="✓" label="Yes" labelHindi="हाँ" onPress={() => onConfirmed({ report })} />
      <BigButton icon="✗" label="No" labelHindi="नहीं" variant="secondary" onPress={onRedo} />
    </div>
  );
}
