// src/App.jsx
//
// The top-level state machine for the whole pipeline:
//   upload -> (job_id) -> status/identify -> (organ) -> workspace (3D + measurements + interact)
//
// This file owns almost no UI itself — it just decides WHICH screen to show,
// and passes data down. Each screen is its own component in src/components/.

import { useState } from "react";
import UploadScreen from "./components/UploadScreen";
import StatusScreen from "./components/StatusScreen";
import Workspace from "./components/Workspace";
import "./index.css";

// The 3 stages of the app, in order
const STAGES = {
  UPLOAD: "upload",
  IDENTIFYING: "identifying",
  WORKSPACE: "workspace",
};

export default function App() {
  const [stage, setStage] = useState(STAGES.UPLOAD);
  const [jobId, setJobId] = useState(null);
  const [organ, setOrgan] = useState(null);

  const handleUploadComplete = (newJobId) => {
    setJobId(newJobId);
    setStage(STAGES.IDENTIFYING);
  };

  const handleIdentified = (identifiedOrgan) => {
    setOrgan(identifiedOrgan);
    setStage(STAGES.WORKSPACE);
  };

  return (
    <div className="app-shell">
      <header className="top-bar">
        <span className="logo">From Slice to Sight</span>
      </header>

      <main>
        {stage === STAGES.UPLOAD && <UploadScreen onUploadComplete={handleUploadComplete} />}

        {stage === STAGES.IDENTIFYING && (
          <StatusScreen jobId={jobId} onIdentified={handleIdentified} />
        )}

        {stage === STAGES.WORKSPACE && <Workspace jobId={jobId} organ={organ} />}
      </main>
    </div>
  );
}
