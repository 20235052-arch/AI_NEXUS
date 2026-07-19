// src/components/TrustPanel.jsx
//
// AI Trust Panel — shows overall confidence, low-confidence regions, and
// a recommendation. Fetches via api.getConfidence.

import { useEffect, useState } from "react";
import { getConfidence } from "../api";

export default function TrustPanel({ studyId, structure }) {
  const [data, setData] = useState(null);

  useEffect(() => {
    getConfidence(studyId, structure).then(setData);
  }, [studyId, structure]);

  if (!data) return <div className="panel">Loading confidence data...</div>;

  const confidence = data.overall_confidence_pct;
  const confidenceClass = confidence == null ? "unknown" : confidence >= 85 ? "high" : confidence >= 60 ? "medium" : "low";

  return (
    <div className="panel trust-panel">
      <h4>AI Trust Panel</h4>

      <div className={`confidence-ring ${confidenceClass}`}>
        {confidence != null ? `${confidence}%` : "N/A"}
      </div>
      <p className="subtitle">
        {confidence != null ? "Overall Confidence" : "Confidence unavailable — not fabricated"}
      </p>

      {data.low_confidence_regions?.length > 0 && (
        <>
          <p className="label-small">Low-Confidence Regions</p>
          <ul>
            {data.low_confidence_regions.map((region) => (
              <li key={region}>{region}</li>
            ))}
          </ul>
        </>
      )}

      {data.recommendation && <p className="recommendation">{data.recommendation}</p>}
    </div>
  );
}
