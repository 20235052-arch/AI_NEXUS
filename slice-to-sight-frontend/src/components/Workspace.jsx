// src/components/Workspace.jsx
//
// Main working screen (Steps 3-5). Now wired to Dev B's real SpleenViewer3D.
//
// meshUrl is fetched here (not hardcoded) via api.getMesh, same pattern as
// MeasurementsPanel/TrustPanel self-fetching their own data. Right now
// MOCK_FLAGS.mesh is still true (Dev D hasn't shipped a real mesh endpoint
// yet), so this resolves to null and SpleenViewer3D correctly shows its
// "waiting on the mesh" state. The moment Dev D's endpoint exists and that
// flag flips to false, this starts working with zero further edits here.

import { useState, useEffect } from "react";
import SliceViewer from "./SliceViewer";
import SpleenViewer3D from "./SpleenViewer3D";
import MeasurementsPanel from "./MeasurementsPanel";
import TrustPanel from "./TrustPanel";
import AnatomyPanel from "./AnatomyPanel";
import { getMesh } from "../api";

export default function Workspace({ studyId, organ, numSlices, modality }) {
  const [selectedStructure, setSelectedStructure] = useState(null);
  const [meshUrl, setMeshUrl] = useState(null);

  useEffect(() => {
    getMesh(studyId, organ).then((data) => setMeshUrl(data.mesh_url));
  }, [studyId, organ]);

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

        <SpleenViewer3D meshUrl={meshUrl} onStructureClick={setSelectedStructure} />

        <MeasurementsPanel studyId={studyId} structure={organ} />
        <TrustPanel studyId={studyId} structure={organ} />
      </div>

      <AnatomyPanel structure={selectedStructure} />
    </div>
  );
}
