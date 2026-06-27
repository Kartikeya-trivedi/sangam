// Pilgrim API client. Base URL from Vite env, defaults to local backend.
export const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export interface MatchResult {
  person_id: string;
  score: number;
  face_score?: number | null;
  attr_score?: number | null;
  geo_score?: number | null;
  explanation: string;
  is_minor: boolean;
  centre_id?: string | null;
  native_summary?: string;
  photo_ref?: string | null;
}

export interface ReportResponse {
  report_id: string;
  native_summary: string;
  structured: Record<string, unknown>;
  candidates: MatchResult[];
}

// Generic TTS (Bulbul). Returns a playable URL or null -> caller uses browser TTS (§2.2).
export async function speakViaApi(text: string, language: string): Promise<string | null> {
  const r = await fetch(`${API_BASE}/speak`, {
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
  // Tap-first structured attributes (mirror dataset columns) — boost matching.
  gender?: string;
  age_band?: string;
  last_seen_location?: string;
}): Promise<ReportResponse> {
  const fd = new FormData();
  if (params.audio) fd.append("audio", params.audio, "audio.webm");
  if (params.photo) fd.append("photo", params.photo, "photo.jpg");
  if (params.text) fd.append("text", params.text);
  if (params.language_hint) fd.append("language_hint", params.language_hint);
  if (params.gender) fd.append("gender", params.gender);
  if (params.age_band) fd.append("age_band", params.age_band);
  if (params.last_seen_location) fd.append("last_seen_location", params.last_seen_location);
  const r = await fetch(`${API_BASE}/report/lost`, { method: "POST", body: fd });
  if (!r.ok) throw new Error("report_failed");
  return r.json();
}

export async function announce(person_id: string, target_language: string) {
  const r = await fetch(`${API_BASE}/announce`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ person_id, target_language }),
  });
  if (!r.ok) throw new Error("announce_failed");
  return r.json() as Promise<{ announcement_text: string; audio_url?: string; blocked: boolean }>;
}
