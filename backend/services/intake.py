"""Intake orchestration: transcript -> Claude profile -> persist -> match -> (proactive notify).

Shared by the /report/lost and /report/found routers. Kept here (not in the router) so the
pipeline is unit-testable without HTTP.
"""
from __future__ import annotations

from config import settings
from db import repo
from models import MatchResult, Person, ReportResponse
from services import claude, matching


def resolve_transcript(text: str | None, audio_path: str | None,
                       language_hint: str | None) -> tuple[str, str]:
    """Return (transcript, detected_language). Prefers STT on audio, else the typed text."""
    from services import speech

    if audio_path and speech.available():
        transcript, lang = speech.transcribe(audio_path, language_hint)
        if transcript.strip():
            return transcript, lang
    # typed-text path (also the offline fallback when STT is down)
    return (text or "").strip(), (language_hint or "unknown")


def process_report(role: str, *, text: str | None = None, audio_path: str | None = None,
                   photo_path: str | None = None, language_hint: str | None = None,
                   centre_id: str, consent_given: bool = True,
                   reporter_mobile: str | None = None, reporter_name: str | None = None,
                   top_k: int = 5) -> ReportResponse:
    """Run the full intake pipeline and return the structured profile + ranked candidates."""
    from services import faces

    transcript, spoken_language = resolve_transcript(text, audio_path, language_hint)
    person = claude.extract_profile(transcript, role=role, centre_id=centre_id,
                                    spoken_language=spoken_language)
    person.consent_given = consent_given
    person.reporter_mobile = reporter_mobile
    person.reporter_name = reporter_name

    face_detected = False
    if photo_path:
        emb = faces.embed(photo_path)
        if emb:
            person.face_embedding = emb
            face_detected = True

    repo.insert_person(person)
    repo.write_audit(person.centre_id, "report_created", person_id=person.id,
                     meta={"role": role, "is_minor": person.is_minor})

    candidates = matching.rank_candidates(person, k=top_k)
    candidates = claude.rerank_candidates(person, candidates)
    if candidates:
        repo.write_audit("system", "match_found", person_id=person.id,
                         meta={"n": len(candidates), "top": candidates[0].final_score})

    # Proactive: a new FOUND record may resolve families already waiting (open LOST). A new LOST
    # record's own candidate list already covers the reverse direction.
    if role == "found":
        notify_high_confidence(person)

    # Never return sensitive media keys to the client.
    safe = person.model_copy(update={"face_embedding": None, "photo_storage_key": None})
    return ReportResponse(
        report_id=person.id,
        native_summary=person.native_summary,
        structured=safe,
        candidates=candidates,
        face_detected=face_detected,
        offline_mode=settings.offline_mode or not claude._get_client(),
    )


def notify_high_confidence(found: Person) -> int:
    """Score a new found record against all open lost records; notify staff on strong matches."""
    created = 0
    for lost in repo.open_persons("lost", limit=500):
        m = matching.compute_match_score(lost, found)
        if m.final_score >= settings.high_confidence_threshold:
            repo.create_notification(
                "high_confidence_match", lost_person_id=lost.id, found_person_id=found.id,
                score=m.final_score, explanation=claude._heuristic_explanation(m),
            )
            repo.write_audit("system", "match_found", person_id=lost.id,
                             related_person_id=found.id,
                             meta={"score": m.final_score, "trigger": "proactive"})
            created += 1
    return created


def rematch(report_id: str, top_k: int = 5, min_score: float | None = None
            ) -> list[MatchResult]:
    """Re-run matching for an existing report (dashboard refresh / new records arrived)."""
    person = repo.get_person(report_id)
    if person is None:
        return []
    candidates = matching.rank_candidates(person, k=top_k, min_score=min_score)
    return claude.rerank_candidates(person, candidates)
