import { defineConfig, devices } from "@playwright/test";

// SETU runs fully offline with no API keys (graceful degradation by design), so the whole
// stack — FastAPI backend + both Vite frontends — is booted by Playwright itself. The DB is
// seeded with deterministic FOUND people in global-setup before the suite runs.

const BACKEND = process.env.SETU_API ?? "http://localhost:8000";
const PILGRIM = process.env.SETU_PILGRIM ?? "http://localhost:5173";
const OPS = process.env.SETU_OPS ?? "http://localhost:5174";

export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  workers: 1, // one shared backend + SQLite DB — keep it serial
  retries: process.env.CI ? 1 : 0,
  timeout: 30_000,
  expect: { timeout: 10_000 },
  reporter: [["list"], ["html", { open: "never" }]],
  globalSetup: "./global-setup.ts",
  use: {
    actionTimeout: 10_000,
    trace: "retain-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        // Software WebGL so MapLibre initialises in headless CI without a GPU.
        launchOptions: {
          args: ["--enable-unsafe-swiftshader", "--ignore-gpu-blocklist", "--use-gl=angle"],
        },
      },
    },
  ],
  webServer: [
    {
      command: "uv run uvicorn main:app --port 8000",
      cwd: "../backend",
      // Keep the suite hermetic + free: force the backend keyless so it runs the deterministic
      // offline path regardless of real keys in backend/.env (empty env vars override .env).
      env: { ANTHROPIC_API_KEY: "", SARVAM_API_KEY: "" },
      url: `${BACKEND}/health`,
      reuseExistingServer: !process.env.CI,
      timeout: 90_000,
      stdout: "pipe",
      stderr: "pipe",
    },
    {
      command: "npm run dev -- --port 5173 --strictPort",
      cwd: "../frontend/pilgrim",
      url: PILGRIM,
      reuseExistingServer: !process.env.CI,
      timeout: 90_000,
    },
    {
      command: "npm run dev -- --port 5174 --strictPort",
      cwd: "../frontend/ops",
      url: OPS,
      reuseExistingServer: !process.env.CI,
      timeout: 90_000,
    },
  ],
  metadata: { backend: BACKEND, pilgrim: PILGRIM, ops: OPS },
});
