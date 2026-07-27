// src/components/MeasurementsPanel.jsx
//
// STEP 4: Calculate volume and area.
//
// REAL BACKEND ONLY PROVIDES: volume_cm3, voxel_count, is_enlarged.
// Surface area, mean HU, and diameters (shown in the pitch deck mockup)
// are NOT part of this backend's actual contract -- don't display fields
// that aren't really being computed. Flag this gap to the team if the
// deck's full stat panel is a hard requirement; it's a Dev C/D scope
// question, not something to fake here.
//
// This endpoint also depends on Dev D having written mask.npy first, so
// it will show a "waiting on segmentation" state until that's done --
// this is expected behavior, not an error to hide or paper over.

import { useEffect, useState } from "react";
import { getMeasurements } from "../api";

export default function MeasurementsPanel({ studyId }) {
  const [data, setData] = useState(null);

  useEffect(() => {
    getMeasurements(studyId).then(setData);
  }, [studyId]);

  if (!data) return <div className="panel">Loading measurements...</div>;

  if (data.status === "pending_segmentation") {
    return (
      <div className="panel measurements-panel">
        <h4>Anatomical Measurements</h4>
        <p className="subtitle">Waiting on segmentation (Dev D's pipeline hasn't run for this study yet).</p>
      </div>
    );
  }

  if (data.status === "not_found") {
    return (
      <div className="panel measurements-panel">
        <h4>Anatomical Measurements</h4>
        <p className="error-text">{data.detail || "Study not found."}</p>
      </div>
    );
  }

  return (
    <div className="panel measurements-panel">
      <h4>Anatomical Measurements</h4>
      <div className="stat-grid">
        <Stat label="Volume" value={`${data.volume_cm3} cm³`} />
        <Stat label="Voxel Count" value={data.voxel_count.toLocaleString()} />
        <Stat label="Enlarged?" value={data.is_enlarged ? "Yes" : "No"} />
      </div>
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="stat">
      <span className="stat-label">{label}</span>
      <span className="stat-value">{value}</span>
    </div>
  );
}
