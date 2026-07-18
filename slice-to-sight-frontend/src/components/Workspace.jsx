// src/components/Workspace.jsx
//
// The main working screen, shown after upload + identification are done
// (Steps 3-5 all live here). This is where Dev B's real 3D component will
// eventually replace Placeholder3DViewer — everything else stays the same.

import { useState } from "react";
import SliceViewer from "./SliceViewer";
import Placeholder3DViewer from "./Placeholder3DViewer";
import MeasurementsPanel from "./MeasurementsPanel";
import TrustPanel from "./TrustPanel";
import AnatomyPanel from "./AnatomyPanel";

export default function Workspace({ jobId, organ }) {
  const [selectedStructure, setSelectedStructure] = useState(null);

  return (
    <div className="workspace">
      <div className="workspace-header">
        <h2>Identified organ: {organ}</h2>
        <span className="job-tag">Job: {jobId}</span>
      </div>

      <div className="workspace-grid">
        <SliceViewer jobId={jobId} />

        {/* Swap Placeholder3DViewer for Dev B's real component when ready —
            same props: meshUrl, onStructureClick */}
        <Placeholder3DViewer meshUrl={null} onStructureClick={setSelectedStructure} />

        <MeasurementsPanel jobId={jobId} structure={organ} />
        <TrustPanel jobId={jobId} structure={organ} />
      </div>

      <AnatomyPanel structure={selectedStructure} />
    </div>
  );
}
