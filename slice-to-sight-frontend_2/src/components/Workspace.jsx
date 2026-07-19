// src/components/Workspace.jsx
//
// Main working screen (Steps 3-5). Dev B's real 3D component will replace
// Placeholder3DViewer here later -- same two props, nothing else changes.

import { useState } from "react";
import SliceViewer from "./SliceViewer";
import Placeholder3DViewer from "./Placeholder3DViewer";
import MeasurementsPanel from "./MeasurementsPanel";
import TrustPanel from "./TrustPanel";
import AnatomyPanel from "./AnatomyPanel";

export default function Workspace({ studyId, organ, numSlices, modality }) {
  const [selectedStructure, setSelectedStructure] = useState(null);

  return (
    <div className="workspace">
      <div className="workspace-header">
        <h2>Identified organ: {organ}</h2>
        <span className="job-tag">
          Study: {studyId} · {numSlices} slices · {modality}
        </span>
      </div>

      <div className="workspace-grid">
        <SliceViewer studyId={studyId} />

        <Placeholder3DViewer meshUrl={null} onStructureClick={setSelectedStructure} />

        <MeasurementsPanel studyId={studyId} structure={organ} />
        <TrustPanel studyId={studyId} structure={organ} />
      </div>

      <AnatomyPanel structure={selectedStructure} />
    </div>
  );
}
