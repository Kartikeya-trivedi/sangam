import type { Lang } from "../i18n";
import { ENINTENT, intent, t } from "../i18n";
import { NearbyDesks } from "../components/NearbyDesks";
import { SpeakHint } from "../components/SpeakHint";

// Screen 2 — Triage. After picking a language, ask the one question that splits the whole
// flow: is someone with you lost, or are YOU lost? Plus the nearest lost-and-found desks.
export function IntentScreen({
  lang,
  onChoose,
}: {
  lang: Lang;
  onChoose: (mode: "report" | "selflost") => void;
}) {
  const r = intent(lang);
  const s = t(lang);

  return (
    <div className="screen">
      <SpeakHint text={r.title} lang={lang} listenLabel={s.listenAgain} />
      <h1 className="screen__title">
        {r.title}
        <small>{ENINTENT.title}</small>
      </h1>

      <div className="intent-grid">
        <button className="intent-card intent-card--report" onClick={() => onChoose("report")}>
          <span className="intent-card__icon" aria-hidden>
            🔎
          </span>
          <span className="intent-card__text">
            <span className="intent-card__title">{r.someoneLost}</span>
            <span className="intent-card__sub">{r.someoneLostSub}</span>
          </span>
        </button>

        <button className="intent-card intent-card--self" onClick={() => onChoose("selflost")}>
          <span className="intent-card__icon" aria-hidden>
            🙋
          </span>
          <span className="intent-card__text">
            <span className="intent-card__title">{r.iAmLost}</span>
            <span className="intent-card__sub">{r.iAmLostSub}</span>
          </span>
        </button>
      </div>

      <NearbyDesks lang={lang} />
    </div>
  );
}
