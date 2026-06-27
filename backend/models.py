"""Pydantic data models — the canonical Person profile + API payloads.

This is the SHARED CONTRACT between the backend and both frontends. age_band values match
the synthetic dataset exactly (see constants.AGE_BANDS) so seeded records and live intake are
directly comparable by the matching engine.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

AgeBand = Literal["0-12", "13-17", "18-40", "41-60", "61-70", "71-80", "80+", "unknown"]
Gender = Literal["male", "female", "unknown"]
HeightBand = Literal["short", "medium", "tall", "unknown"]
Role = Literal["lost", "found"]
CaseStatus = Literal["open", "matched", "reunited", "expired"]


class Person(BaseModel):
    """Canonical profile Claude produces and the matching engine scores on.

    Both "lost" (family searching) and "found" (logged at a camp) reports produce this shape.
    """

    id: str
    role: Role

    # --- Structured attributes (canonical English for matching) ---
    age_band: AgeBand = "unknown"
    gender: Gender = "unknown"
    name: Optional[str] = None                                 # canonical transliteration; ~15% absent
    clothing: list[str] = Field(default_factory=list)          # ["blue kurta", "white dhoti"]
    distinguishing_features: list[str] = Field(default_factory=list)  # ["walking stick", "hearing aid"]
    height_band: HeightBand = "unknown"
    languages_spoken: list[str] = Field(default_factory=list)  # language the MISSING person speaks
    last_seen_location: Optional[str] = None
    last_seen_time: Optional[datetime] = None

    # --- Reporter-side context ---
    reporter_name: Optional[str] = None
    reporter_mobile: Optional[str] = None                      # ~20% absent

    # --- Raw + provenance ---
    spoken_language: str = "unknown"                           # language of the REPORT
    raw_transcript: str = ""                                   # native-script STT/text input
    native_summary: str = ""                                   # readback in reporter's language

    # --- Media (live-intake only; dataset has none) ---
    face_embedding: Optional[list[float]] = None               # 512-d InsightFace vector
    photo_storage_key: Optional[str] = None                    # never returned in API responses
    photo_location_hint: Optional[str] = None

    # --- Safety ---
    is_minor: bool = False
    consent_given: bool = False

    # --- Operational ---
    centre_id: str
    centre_zone: Optional[str] = None
    status: CaseStatus = "open"

    created_at: Optional[datetime] = None
    ttl_expires_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def summary(self) -> str:
        """Short human display string, e.g. 'Elderly male, 71-80, blue kurta, tamil'."""
        bits: list[str] = []
        if self.age_band != "unknown":
            bits.append(self.age_band)
        if self.gender != "unknown":
            bits.append(self.gender)
        if self.name:
            bits.append(self.name)
        if self.clothing:
            bits.append(", ".join(self.clothing[:2]))
        if self.languages_spoken:
            bits.append("/".join(self.languages_spoken[:2]))
        return ", ".join(bits) or "unidentified person"


class ScoreBreakdown(BaseModel):
    """Per-signal scores (0..1), None where a signal is not applicable."""
    face: Optional[float] = None
    name: Optional[float] = None
    age: Optional[float] = None
    gender: Optional[float] = None
    language: Optional[float] = None
    clothing: Optional[float] = None
    distinguishing: Optional[float] = None
    location: Optional[float] = None
    centre: Optional[float] = None
    time: Optional[float] = None


class MatchResult(BaseModel):
    """One ranked candidate with an explainable score breakdown."""
    candidate_id: str
    candidate_role: Role
    final_score: float
    breakdown: ScoreBreakdown = Field(default_factory=ScoreBreakdown)
    explanation: str = ""
    confidence: Literal["high", "medium", "low"] = "low"

    # Safety
    is_minor: bool = False
    requires_guardian_verification: bool = False

    # Display
    candidate_centre_id: str = ""
    candidate_summary: str = ""


class ReportResponse(BaseModel):
    report_id: str
    native_summary: str
    structured: Person
    candidates: list[MatchResult] = Field(default_factory=list)
    face_detected: bool = False
    photo_analyzed: bool = False  # Claude Vision extracted attributes from the photo (cross-modal)
    offline_mode: bool = False


class ConfirmRequest(BaseModel):
    lost_person_id: str
    found_person_id: str
    confirmed_by: str = "staff"
    notes: str = ""


class RejectRequest(BaseModel):
    lost_person_id: str
    found_person_id: str
    rejected_by: str = "staff"
    reason: str = ""


class AnnounceRequest(BaseModel):
    person_id: str
    target_language: str = "hi"
    triggered_by: str = "staff"


class AnnounceResponse(BaseModel):
    announcement_text: str = ""
    audio_url: Optional[str] = None
    blocked: bool = False
    staff_alert_created: bool = False


class SpeakRequest(BaseModel):
    text: str
    language: str = "hi"


class SpeakResponse(BaseModel):
    audio_url: Optional[str] = None
    expires_at: Optional[datetime] = None


class GuardianVerifyRequest(BaseModel):
    minor_person_id: str
    claimant_person_id: str
    verifier_name: str
    verification_method: Literal[
        "visual_id", "family_photo", "personal_questions", "police_escalation"
    ]
    notes: str = ""
    approved: bool = False
