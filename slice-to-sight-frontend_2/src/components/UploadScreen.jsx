// src/components/UploadScreen.jsx
//
// STEP 1: Upload a CT image.
// Upload is SYNCHRONOUS on the real backend -- the fetch itself may take
// a few seconds while the server parses the DICOM/NIfTI file, and the
// response already contains everything needed to move on (study_id,
// num_slices, modality). No separate polling step exists or is needed.

import { useState } from "react";
import { uploadCT } from "../api";

export default function UploadScreen({ onUploadComplete }) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [fileName, setFileName] = useState(null);

  const handleFileChange = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setFileName(file.name);
    setError(null);
    setUploading(true);

    try {
      const result = await uploadCT(file); // { study_id, shape, spacing, num_slices, modality }
      onUploadComplete(result);
    } catch (err) {
      setError(err.message || "Upload failed. Check that the backend is running.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="panel upload-screen">
      <h2>From Slice to Sight</h2>
      <p className="subtitle">Upload a CT scan (.nii, .nii.gz, .dcm, or a zipped DICOM series) to begin.</p>

      <label className="upload-dropzone">
        <input
          type="file"
          accept=".nii,.nii.gz,.zip,.dcm"
          onChange={handleFileChange}
          disabled={uploading}
          hidden
        />
        {uploading ? (
          <span>Uploading &amp; parsing{fileName ? ` "${fileName}"` : ""}... this can take a few seconds</span>
        ) : (
          <span>Click to select a CT scan file</span>
        )}
      </label>

      {error && <p className="error-text">{error}</p>}
    </div>
  );
}
