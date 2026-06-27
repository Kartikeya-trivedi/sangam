export const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export interface CaseRow {
  id: string;
  role: string;
  status: string;
  is_minor: boolean;
  centre_id: string | null;
  native_summary: string;
  age_band: string;
  gender: string;
  clothing: string[];
}

export interface StaffAlert {
  id: string;
  person_id: string;
  centre_id: string | null;
  type: string;
  guardian_verified: boolean;
}

export async function fetchCases(): Promise<{ cases: CaseRow[]; staff_alerts: StaffAlert[] }> {
  const r = await fetch(`${API_BASE}/ops/cases`);
  if (!r.ok) throw new Error("cases_failed");
  return r.json();
}

export async function confirmMatch(report_id: string, matched_person_id: string) {
  const r = await fetch(`${API_BASE}/ops/confirm`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ report_id, matched_person_id, actor: "staff" }),
  });
  return r.json();
}
