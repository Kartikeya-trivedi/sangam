import { useEffect } from "react";

import { announce } from "../api";
import type { Draft } from "../App";
import { BigButton } from "../components/BigButton";
import { SpeakHint } from "../components/SpeakHint";
import { useSpeak } from "../hooks/useSpeak";

// Screen 5 — Result (spec §10). Large cards with a spoken/visual reason. Minors route to
// staff, never a public "Connect" (§12.1). No dead-end "no results" (§10).
export function ResultScreen({ draft, onRestart }: { draft: Draft; onRestart: () => void }) {
  const speak = useSpeak();
  const candidates = draft.report?.candidates ?? [];
  const found = candidates.length > 0;

  useEffect(() => {
    speak(
      found ? "हमें ये लोग मिले" : "हमने आपकी जानकारी दर्ज कर ली है, मिलते ही बताएंगे",
      draft.language,
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function connect(personId: string) {
    try {
      const a = await announce(personId, draft.language);
      await speak(a.blocked ? "स्टाफ़ आपकी मदद करेगा" : "घोषणा कर दी गई है", draft.language);
    } catch {
      await speak("कुछ गड़बड़ हुई, स्टाफ़ से संपर्क करें", draft.language);
    }
  }

  return (
    <div className="screen">
      <SpeakHint
        text={found ? "हमें ये लोग मिले" : "हमने आपकी जानकारी दर्ज कर ली है"}
        lang={draft.language}
      />
      <h1 className="screen__title">
        {found ? "हमें ये लोग मिले" : "जानकारी दर्ज हो गई"}
        <small>{found ? "We found these people" : "We've registered your report"}</small>
      </h1>

      <div className="cards">
        {candidates.map((c) => (
          <div key={c.person_id} className="card">
            <div className="card__summary">{c.native_summary || c.explanation}</div>
            <div className="card__reason">क्यों match हुआ: {c.explanation}</div>
            {c.is_minor ? (
              <div className="card__minor">👶 स्टाफ़ मदद करेगा (verification required)</div>
            ) : (
              <BigButton icon="📞" label="Connect" labelHindi="इनसे मिलिए" onPress={() => connect(c.person_id)} />
            )}
          </div>
        ))}
      </div>

      <BigButton label="Start over" labelHindi="फिर से शुरू करें" variant="secondary" onPress={onRestart} />
    </div>
  );
}
