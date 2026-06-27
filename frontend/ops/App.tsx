import { useState } from "react";

import { CaseQueue } from "./components/CaseQueue";
import { MapView } from "./components/MapView";
import { SahayakView } from "./components/SahayakView";

// Officials dashboard (spec §11) — a normal data-dense web app, exempt from the §2 UX laws.
export default function App() {
  const [tab, setTab] = useState<"sahayak" | "map" | "queue">("sahayak");

  return (
    <div className="ops">
      <header className="ops__header">
        <h1>SETU — Officials Dashboard</h1>
        <nav>
          <button className={tab === "sahayak" ? "active" : ""} onClick={() => setTab("sahayak")}>
            🤖 Sahayak
          </button>
          <button className={tab === "map" ? "active" : ""} onClick={() => setTab("map")}>
            🗺️ Map
          </button>
          <button className={tab === "queue" ? "active" : ""} onClick={() => setTab("queue")}>
            📋 Cases
          </button>
        </nav>
      </header>
      <main className="ops__main">
        {tab === "sahayak" ? <SahayakView /> : tab === "map" ? <MapView /> : <CaseQueue />}
      </main>
    </div>
  );
}
