// src/components/UploadScreen.jsx
//
// STEP 1: Upload a CT image.
// Shows a file picker, sends the file via api.uploadCT, and hands the
// resulting job_id back up to App.jsx once the upload succeeds.

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
      const data = await uploadCT(file);
      onUploadComplete(data.job_id);
    } catch (err) {
      setError("Upload failed. Check that the backend is running.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="panel upload-screen">
      <h2>From Slice to Sight</h2>
      <p className="subtitle">Upload a CT scan (DICOM .zip or NIfTI .nii.gz) to begin.</p>

      <label className="upload-dropzone">
        <input
          type="file"
          accept=".nii,.nii.gz,.zip, .jpg, .jpeg, .png"
          onChange={handleFileChange}
          disabled={uploading}
          hidden
        />
        {uploading ? (
          <span>Uploading{fileName ? ` "${fileName}"` : ""}...</span>
        ) : (
          <span>Click to select a CT scan file</span>
        )}
      </label>

      {error && <p className="error-text">{error}</p>}
    </div>
  );
}
