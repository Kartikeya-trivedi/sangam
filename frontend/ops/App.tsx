import { useState } from "react";

import { CaseQueue } from "./components/CaseQueue";
import { MapView } from "./components/MapView";

// Officials dashboard (spec §11) — a normal data-dense web app, exempt from the §2 UX laws.
export default function App() {
  const [tab, setTab] = useState<"map" | "queue">("map");

  return (
    <div className="ops">
      <header className="ops__header">
        <h1>SETU — Officials Dashboard</h1>
        <nav>
          <button className={tab === "map" ? "active" : ""} onClick={() => setTab("map")}>
            🗺️ Map
          </button>
          <button className={tab === "queue" ? "active" : ""} onClick={() => setTab("queue")}>
            📋 Cases
          </button>
        </nav>
      </header>
      <main className="ops__main">{tab === "map" ? <MapView /> : <CaseQueue />}</main>
    </div>
  );
}
