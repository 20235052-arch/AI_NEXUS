// src/components/SliceViewer.jsx
//
// Fetches slice metadata via api.getSlices and renders a slider + image.
// Each slice image_url points directly at a real backend endpoint that
// returns a raw PNG -- the browser just loads it like any other <img>.

import { useEffect, useState } from "react";
import { getSlices } from "../api";

export default function SliceViewer({ studyId }) {
  const [slicesData, setSlicesData] = useState(null);
  const [currentSlice, setCurrentSlice] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getSlices(studyId).then((data) => {
      setSlicesData(data);
      setCurrentSlice(Math.floor(data.total_slices / 2));
      setLoading(false);
    });
  }, [studyId]);

  if (loading) return <div className="panel">Loading slices...</div>;
  if (!slicesData) return null;

  const slice = slicesData.slices[currentSlice];

  return (
    <div className="panel slice-viewer">
      <h4>CT Slice View</h4>
      <img src={slice.image_url} alt={`Slice ${currentSlice}`} className="slice-image" />
      <div className="slider-row">
        <span className="slice-count">
          Slice {currentSlice + 1} / {slicesData.total_slices}
        </span>
        <input
          type="range"
          min={0}
          max={slicesData.total_slices - 1}
          value={currentSlice}
          onChange={(e) => setCurrentSlice(Number(e.target.value))}
        />
      </div>
    </div>
  );
}
