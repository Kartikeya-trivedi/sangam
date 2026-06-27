// Pilgrim API client. Base URL from Vite env, defaults to local backend.
export const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";
// Which lost-and-found centre this kiosk reports into. The backend requires a valid centre slug
// (see backend/constants.py CENTRES); override per kiosk with VITE_CENTRE_ID.
export const CENTRE_ID = import.meta.env.VITE_CENTRE_ID ?? "central_control_room";

// Per-signal score breakdown (0..1 each, or null when a signal wasn't available).
// Mirrors backend models.py ScoreBreakdown exactly.
export interface ScoreBreakdown {
  face: number | null;
  name: number | null;
  age: number | null;
  gender: number | null;
  language: number | null;
  clothing: number | null;
  distinguishing: number | null;
  location: number | null;
  centre: number | null;
  time: number | null;
}

// Canonical match contract — mirrors backend models.py MatchResult.
// (The previous shape here was stale and never matched the wire format.)
export interface MatchResult {
  candidate_id: string;
  candidate_role: "lost" | "found";
  final_score: number; // 0..1
  breakdown: ScoreBreakdown;
  explanation: string;
  confidence: "high" | "medium" | "low";
  is_minor: boolean;
  requires_guardian_verification: boolean;
  candidate_centre_id: string;
  candidate_summary: string;
}

export interface ReportResponse {
  report_id: string;
  native_summary: string;
  structured: Record<string, unknown>;
  candidates: MatchResult[];
  face_detected?: boolean;
  offline_mode?: boolean;
}

// Result of an announce() call. On success the backend returns announcement_text
// (+ optional audio_url). For a MINOR it returns HTTP 403 with action_required —
// we surface that as a structured "blocked" result instead of throwing (see announce()).
export interface AnnounceResult {
  announcement_text?: string;
  audio_url?: string | null;
  blocked: boolean;
  staff_alert_created?: boolean;
  // Set when the backend blocked the announce (e.g. guardian_verification for a minor).
  action_required?: string;
  spoken?: string;
  error?: string;
}

// Generic TTS (Bulbul). Returns a playable URL or null -> caller uses browser TTS (§2.2).
export async function speakViaApi(text: string, language: string): Promise<string | null> {
  const r = await fetch(`${API_BASE}/api/v1/speak`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, language }),
  });
  if (!r.ok) return null;
  const j = await r.json();
  if (!j.audio_url) return null;
  // Backend returns either a data: URL (inline audio) or a relative path.
  return j.audio_url.startsWith("data:") ? j.audio_url : `${API_BASE}${j.audio_url}`;
}

export async function reportLost(params: {
  audio?: Blob;
  photo?: Blob;
  text?: string;
  language_hint?: string;
  reporter_mobile?: string;
  // Tap-first structured attributes (mirror dataset columns) — boost matching.
  gender?: string;
  age_band?: string;
  last_seen_location?: string;
}): Promise<ReportResponse> {
  const fd = new FormData();
  fd.append("centre_id", CENTRE_ID);
  if (params.audio) fd.append("audio", params.audio, "audio.webm");
  if (params.photo) fd.append("photo", params.photo, "photo.jpg");
  if (params.text) fd.append("text", params.text);
  if (params.language_hint) fd.append("language_hint", params.language_hint);
  if (params.reporter_mobile) fd.append("reporter_mobile", params.reporter_mobile);
  if (params.gender) fd.append("gender", params.gender);
  if (params.age_band) fd.append("age_band", params.age_band);
  if (params.last_seen_location) fd.append("last_seen_location", params.last_seen_location);
  const r = await fetch(`${API_BASE}/api/v1/report/lost`, { method: "POST", body: fd });
  if (!r.ok) throw new Error("report_failed");
  return r.json();
}

// Trigger a reunification announcement for a found person.
// - 200 -> { announcement_text, audio_url?, blocked, staff_alert_created }
// - 403 (MINOR) -> { error, spoken, action_required: "guardian_verification" } — we DON'T throw,
//   we return it as a structured blocked result so the UI can show the guardian-verification path.
// Throws only on genuine transport / unexpected errors.
export async function announce(person_id: string, target_language: string): Promise<AnnounceResult> {
  const r = await fetch(`${API_BASE}/api/v1/announce`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ person_id, target_language }),
  });
  const j = (await r.json().catch(() => ({}))) as AnnounceResult;
  if (r.status === 403) {
    // Guardian-verification gate (child safety §12) — surface, don't crash.
    return { ...j, blocked: true, action_required: j.action_required ?? "guardian_verification" };
  }
  if (!r.ok) throw new Error("announce_failed");
  // Resolve a relative audio path to an absolute URL (data: URLs pass through).
  if (j.audio_url && !j.audio_url.startsWith("data:") && !j.audio_url.startsWith("http")) {
    j.audio_url = `${API_BASE}${j.audio_url}`;
  }
  return j;
}
