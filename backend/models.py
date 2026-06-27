"""Pydantic data models — canonical Person profile + API payloads (spec §6, §7)."""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

AgeBand = Literal["child", "teen", "adult", "elderly", "unknown"]
Gender = Literal["male", "female", "other", "unknown"]
HeightBand = Literal["short", "medium", "tall", "unknown"]
Role = Literal["lost", "found"]
CaseStatus = Literal["open", "matched", "reunited", "expired"]


class Person(BaseModel):
    """Canonical profile Claude produces and the matching engine scores on (spec §6)."""

    id: str
    role: Role  # who's being searched for vs logged at a camp

    # --- Structured attributes (Claude extracts; English canonical for matching) ---
    age_band: AgeBand = "unknown"
    gender: Gender = "unknown"
    clothing: list[str] = Field(default_factory=list)          # ["blue kurta", "white dhoti"]
    distinguishing: list[str] = Field(default_factory=list)    # ["walking stick", "scar on left cheek"]
    height_band: HeightBand = "unknown"
    languages_spoken: list[str] = Field(default_factory=list)  # ["tamil"]
    last_seen_location: Optional[str] = None                   # free text or ghat name
    last_seen_time: Optional[str] = None

    # --- Raw + provenance ---
    spoken_language: str = "unknown"   # detected language of the report
    raw_transcript: str = ""           # original Saaras transcript (native script)
    native_summary: str = ""           # short summary in reporter's language (for readback)

    # --- Media ---
    face_embedding: Optional[list[float]] = None  # 512-d InsightFace vector
    photo_ref: Optional[str] = None               # storage key (privacy §12)
    location_hint: Optional[str] = None           # Claude vision guess from photo background

    # --- Safety ---
    is_minor: bool = False
    contact_phone: Optional[str] = None
    consent_given: bool = False

    created_at: Optional[datetime] = None
    ttl_expires_at: Optional[datetime] = None      # auto-purge after Mela

    # --- Operational (complements the persons.centre_id column in schema.sql) ---
    centre_id: Optional[str] = None
    status: CaseStatus = "open"


class MatchResult(BaseModel):
    """One ranked candidate with an explainable score breakdown (spec §7, §9)."""

    person_id: str
    score: float
    face_score: Optional[float] = None
    attr_score: Optional[float] = None
    geo_score: Optional[float] = None
    explanation: str = ""              # one-line "why it matched" (Claude re-rank)
    is_minor: bool = False
    centre_id: Optional[str] = None
    # Convenience fields for the result cards (full record fetched on demand)
    native_summary: str = ""
    photo_ref: Optional[str] = None


class ReportResponse(BaseModel):
    report_id: str
    native_summary: str
    structured: Person
    candidates: list[MatchResult] = Field(default_factory=list)


class AnnounceRequest(BaseModel):
    person_id: str
    target_language: str


class AnnounceResponse(BaseModel):
    announcement_text: str
    audio_url: Optional[str] = None
    blocked: bool = False             # True when minor-safety blocks a public announce (§12)
    staff_alert_created: bool = False


class SpeakRequest(BaseModel):
    text: str
    language: str


class SpeakResponse(BaseModel):
    audio_url: Optional[str] = None


class ConfirmRequest(BaseModel):
    report_id: str
    matched_person_id: str
    actor: str = "staff"
