// src/components/MeasurementsPanel.jsx
//
// STEP 4: Calculate volume and area. Fetches measurements via
// api.getMeasurements and displays them as a clean stat grid.

import { useEffect, useState } from "react";
import { getMeasurements } from "../api";

export default function MeasurementsPanel({ jobId, structure }) {
  const [data, setData] = useState(null);

  useEffect(() => {
    getMeasurements(jobId, structure).then(setData);
  }, [jobId, structure]);

  if (!data) return <div className="panel">Loading measurements...</div>;

  const m = data.measurements;

  return (
    <div className="panel measurements-panel">
      <h4>Anatomical Measurements — {structure}</h4>
      <div className="stat-grid">
        <Stat label="Volume" value={`${m.volume_cm3} cm³`} />
        <Stat label="Surface Area" value={`${m.surface_area_cm2} cm²`} />
        <Stat label="Mean HU" value={m.mean_hu} />
        <Stat label="Max Diameter" value={`${m.max_diameter_cm} cm`} />
        <Stat label="Min Diameter" value={`${m.min_diameter_cm} cm`} />
        <Stat label="Thickness" value={`${m.thickness_cm} cm`} />
      </div>
      <p className="subtitle">Location: {data.location}</p>
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
