import { execSync } from "node:child_process";
import path from "node:path";

// Seed deterministic FOUND people (incl. one minor) directly into the SQLite DB before the
// suite runs. Idempotent — re-running only replaces the `e2e-*` rows. No server needed.
export default async function globalSetup() {
  const backend = path.resolve(__dirname, "../backend");
  // eslint-disable-next-line no-console
  console.log("[global-setup] seeding deterministic e2e data…");
  execSync("uv run python ../scripts/seed_e2e.py", {
    cwd: backend,
    stdio: "inherit",
  });
}
