// src/components/StatusScreen.jsx
//
// STEP 2: Identify — the AI is segmenting/identifying the organ.
// Polls api.getStatus every couple seconds until status === "complete",
// then hands control (and the identified organ name) back up to App.jsx.

import { useEffect, useState, useRef } from "react";
import { getStatus } from "../api";

export default function StatusScreen({ jobId, onIdentified }) {
  const [statusText, setStatusText] = useState("Processing scan...");
  const [pollCount, setPollCount] = useState(0);
  const pollCountRef = useRef(0);

  useEffect(() => {
    let cancelled = false;

    const poll = async () => {
      try {
        const data = await getStatus(jobId);
        pollCountRef.current += 1;
        setPollCount(pollCountRef.current);

        // In mock mode getStatus always returns "complete" instantly.
        // Real backend: keep polling until status is "complete".
        if (data.status === "complete" && !cancelled) {
          onIdentified(data.organ_identified || "spleen");
          return; // stop polling
        }

        if (!cancelled) {
          setStatusText(`Status: ${data.status}...`);
          setTimeout(poll, 2000);
        }
      } catch (err) {
        if (!cancelled) setStatusText("Something went wrong while checking status.");
      }
    };

    poll();
    return () => {
      cancelled = true;
    };
  }, [jobId, onIdentified]);

  return (
    <div className="panel status-screen">
      <div className="spinner" />
      <h3>{statusText}</h3>
      <p className="subtitle">Job ID: {jobId}</p>
      {pollCount > 0 && <p className="subtitle">Checked {pollCount} time(s)</p>}
    </div>
  );
}
