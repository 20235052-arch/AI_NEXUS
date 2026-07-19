// src/App.jsx
//
// Top-level state machine:
//   upload -> workspace
//
// NOTE: there used to be a separate "identifying" polling stage here, but
// Dev C's real backend has no status/polling endpoint at all -- upload is
// synchronous and returns everything (study_id, num_slices, modality) in
// one response. So the moment upload resolves, we already have what we
// need and go straight to the workspace.

import { useState } from "react";
import UploadScreen from "./components/UploadScreen";
import Workspace from "./components/Workspace";
import "./index.css";

const STAGES = {
  UPLOAD: "upload",
  WORKSPACE: "workspace",
};

export default function App() {
  const [stage, setStage] = useState(STAGES.UPLOAD);
  const [studyId, setStudyId] = useState(null);
  const [numSlices, setNumSlices] = useState(null);
  const [modality, setModality] = useState(null);

  // This MVP only segments the spleen -- there is no organ-identification
  // step anywhere in the current backend (that would be Dev D's job, and
  // it isn't built). Hardcoded on purpose, not a placeholder oversight.
  const organ = "spleen";

  const handleUploadComplete = (uploadResult) => {
    setStudyId(uploadResult.study_id);
    setNumSlices(uploadResult.num_slices);
    setModality(uploadResult.modality);
    setStage(STAGES.WORKSPACE);
  };

  return (
    <div className="app-shell">
      <header className="top-bar">
        <span className="logo">From Slice to Sight</span>
      </header>

      <main>
        {stage === STAGES.UPLOAD && <UploadScreen onUploadComplete={handleUploadComplete} />}

        {stage === STAGES.WORKSPACE && (
          <Workspace studyId={studyId} organ={organ} numSlices={numSlices} modality={modality} />
        )}
      </main>
    </div>
  );
}
