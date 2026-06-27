import { test, expect } from "@playwright/test";

// Direct backend-contract checks — no browser, no keys. These are the rock-solid core: they
// prove the offline pipeline, the tap-first structured override, matching against the seed,
// and the child-safety announce block, independent of any UI/WebGL flake.

const API = process.env.SETU_API ?? "http://localhost:8000";

test("health: boots offline with every external capability degraded", async ({ request }) => {
  const res = await request.get(`${API}/health`);
  expect(res.ok()).toBeTruthy();
  const body = await res.json();
  expect(body.status).toBe("ok");
  expect(body.capabilities).toMatchObject({
    claude: false,
    sarvam_speech: false,
    insightface: false,
  });
});

test("report/lost (text + taps) returns a structured profile and a ranked match", async ({ request }) => {
  const res = await request.post(`${API}/api/v1/report/lost`, {
    multipart: {
      centre_id: "ramkund_kho_ya_paya_kendra",
      text: "buzurg aadmi, neeli kurta, Tamil bolte hain",
      gender: "Male", // capitalised, like the pilgrim chip — backend normalises
      age_band: "71-80",
      last_seen_location: "Ramkund Ghat",
      language_hint: "hi",
    },
  });
  expect(res.ok()).toBeTruthy();
  const body = await res.json();
  expect(body.report_id).toBeTruthy();
  expect(body.offline_mode).toBe(true);
  expect(body.structured.gender).toBe("male");
  expect(body.structured.age_band).toBe("71-80");
  // Matches the seeded elderly Tamil-speaking found man (e2e-found-001).
  expect(body.candidates.length).toBeGreaterThan(0);
  expect(body.candidates[0].final_score).toBeGreaterThan(0.3);
});

test("report/lost with ONLY taps (no text, no audio) still succeeds", async ({ request }) => {
  // The redesigned pilgrim form can submit with chips alone — this must not 400 "no_input".
  const res = await request.post(`${API}/api/v1/report/lost`, {
    multipart: {
      centre_id: "central_control_room",
      gender: "Female",
      age_band: "18-40",
      last_seen_location: "Panchavati Circle",
      language_hint: "hi-IN",
    },
  });
  expect(res.ok()).toBeTruthy();
  const body = await res.json();
  expect(body.structured.gender).toBe("female");
  expect(body.structured.age_band).toBe("18-40");
});

test("report/lost rejects a missing centre / empty input", async ({ request }) => {
  const noCentre = await request.post(`${API}/api/v1/report/lost`, {
    multipart: { text: "kuch bhi" },
  });
  expect(noCentre.status()).toBe(422); // centre_id is a required form field
});

test("announce: a minor is never publicly announced (child-safety §12)", async ({ request }) => {
  const res = await request.post(`${API}/api/v1/announce`, {
    data: { person_id: "e2e-found-003", target_language: "hi" },
  });
  expect(res.status()).toBe(403);
  const body = await res.json();
  expect(body.action_required).toBe("guardian_verification");
});

test("ops endpoints the dashboard depends on are healthy", async ({ request }) => {
  const cases = await request.get(`${API}/api/v1/ops/cases`);
  expect(cases.ok()).toBeTruthy();
  const cj = await cases.json();
  expect(Array.isArray(cj.cases)).toBeTruthy();
  expect(cj.cases.length).toBeGreaterThan(0); // seeded found-persons
  expect(cj.summary).toBeTruthy();

  const map = await request.get(`${API}/api/v1/ops/map`);
  expect(map.ok()).toBeTruthy();
  const mj = await map.json();
  expect(mj.type).toBe("FeatureCollection");
  expect(Array.isArray(mj.features)).toBeTruthy();
});
