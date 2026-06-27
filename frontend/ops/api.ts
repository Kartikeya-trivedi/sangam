export const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

// Optional basemap key (MapTiler / Mapbox). Without it the map uses free demo tiles.
// Set VITE_MAPS_API_KEY in frontend/ops/.env to use a real street basemap.
export const MAPS_API_KEY = import.meta.env.VITE_MAPS_API_KEY ?? "";

// Google Maps JS key -> real street map. Set VITE_GOOGLE_MAPS_API_KEY in frontend/ops/.env.
export const GOOGLE_MAPS_API_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY ?? "";

export interface CaseRow {
  id: string;
  role: string;
  status: string;
  is_minor: boolean;
  centre_id: string | null;
  age_band: string;
  gender: string;
  name: string | null;
  clothing: string[];
  languages_spoken: string[];
  last_seen_location: string | null;
  created_at: string | null;
  match_count: number;
  best_match_score: number;
  hours_open: number;
}

export interface CasesSummary {
  total_open: number;
  total_matched: number;
  total_reunited: number;
  total_minor_open: number;
}

export interface CasesResponse {
  cases: CaseRow[];
  total: number;
  page: number;
  per_page: number;
  summary: CasesSummary;
}

// One ranked candidate returned by GET /match/{id} — mirrors backend models.MatchResult.
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

export interface MatchResponse {
  report_id: string;
  candidates: MatchResult[];
}

export interface OpsStats {
  overall: {
    total_reports: number;
    by_status: Record<string, number>;
    total_reunited: number;
    total_open: number;
  };
  by_centre: { centre_id: string; total_cases: number; open: number; reunited: number }[];
  by_age_band: { age_band: string; total: number; pct_of_total: number }[];
  notifications: number;
}

export interface OpsNotification {
  lost_person_id?: string;
  found_person_id?: string;
  score?: number;
  explanation?: string;
  [k: string]: unknown;
}

export async function fetchCases(): Promise<CasesResponse> {
  const r = await fetch(`${API_BASE}/api/v1/ops/cases`);
  if (!r.ok) throw new Error("cases_failed");
  return r.json();
}

export async function fetchMatches(reportId: string): Promise<MatchResponse> {
  const r = await fetch(`${API_BASE}/api/v1/match/${reportId}?top_k=5&min_score=0.3`);
  if (!r.ok) throw new Error("match_failed");
  return r.json();
}

export async function fetchStats(): Promise<OpsStats> {
  const r = await fetch(`${API_BASE}/api/v1/ops/stats`);
  if (!r.ok) throw new Error("stats_failed");
  return r.json();
}

export async function fetchNotifications(): Promise<OpsNotification[]> {
  const r = await fetch(`${API_BASE}/api/v1/ops/notifications?status=new`);
  if (!r.ok) throw new Error("notifications_failed");
  const d = await r.json();
  return d.notifications ?? [];
}

export async function confirmMatch(lost_person_id: string, found_person_id: string, notes = "") {
  const r = await fetch(`${API_BASE}/api/v1/ops/confirm`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ lost_person_id, found_person_id, confirmed_by: "staff", notes }),
  });
  const body = await r.json().catch(() => ({}));
  return { ok: r.ok, status: r.status, body };
}

export async function rejectMatch(lost_person_id: string, found_person_id: string, reason = "") {
  const r = await fetch(`${API_BASE}/api/v1/ops/reject`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ lost_person_id, found_person_id, rejected_by: "staff", reason }),
  });
  const body = await r.json().catch(() => ({}));
  return { ok: r.ok, status: r.status, body };
}
