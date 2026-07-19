"""
Handles scan uploads: accepts a DICOM series or NIfTI file,
parses it into a numpy volume, and caches it to disk so other
endpoints (slices, metrics) can reuse it without re-parsing.
"""

import uuid
import shutil
import zipfile
from pathlib import Path

import numpy as np
from fastapi import APIRouter, UploadFile, File, HTTPException

from services.volume_loader import load_nifti, load_dicom_series

router = APIRouter()

STORAGE = Path("storage")
STORAGE.mkdir(exist_ok=True)


def _extract_dicom_zip(zip_path: Path, extract_to: Path) -> Path:
    """
    Extracts a zip file and returns the folder containing the .dcm files.
    Handles the common case where the zip has an extra nested folder
    (e.g. zip contains "study1/scan/*.dcm" instead of "*.dcm" at the root).
    """
    with zipfile.ZipFile(zip_path, "r") as zf:
        # Guard against zip-slip (malicious paths like "../../etc/passwd")
        for member in zf.namelist():
            member_path = (extract_to / member).resolve()
            if not str(member_path).startswith(str(extract_to.resolve())):
                raise HTTPException(status_code=400, detail="Invalid zip contents")
        zf.extractall(extract_to)

    # Find the folder that actually contains .dcm files (could be nested)
    dcm_files = list(extract_to.rglob("*.dcm"))
    if not dcm_files:
        raise HTTPException(
            status_code=422,
            detail="No .dcm files found inside the uploaded zip",
        )
    return dcm_files[0].parent


@router.post("/upload")
async def upload_scan(file: UploadFile = File(...)):
    """
    Accepts a single file upload, one of:
    - a .nii or .nii.gz NIfTI file
    - a single .dcm file (only valid if it's the entire series - rare)
    - a .zip file containing a full DICOM series (the normal case for DICOM)

    Returns a study_id that must be passed to every other endpoint.
    """
    study_id = str(uuid.uuid4())
    study_dir = STORAGE / study_id
    study_dir.mkdir(parents=True)

    filepath = study_dir / file.filename
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        if file.filename.endswith((".nii", ".nii.gz")):
            volume, spacing, modality = load_nifti(filepath)
        elif file.filename.endswith(".zip"):
            dicom_folder = _extract_dicom_zip(filepath, study_dir)
            volume, spacing, modality = load_dicom_series(dicom_folder)
        elif file.filename.endswith(".dcm"):
            volume, spacing, modality = load_dicom_series(study_dir)
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Use .nii, .nii.gz, .dcm, or .zip (DICOM series)",
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse scan: {e}")

    # Cache the parsed volume + spacing so later requests (slicing,
    # metrics) don't need to re-parse the original file. Modality is
    # saved as plain text so the slices endpoint can pick the right
    # windowing (CT uses Hounsfield-Unit windowing; MR needs a
    # percentile-based approach since MR has no fixed intensity scale).
    np.save(study_dir / "volume.npy", volume)
    np.save(study_dir / "spacing.npy", np.array(spacing, dtype=np.float64))
    (study_dir / "modality.txt").write_text(modality)

    return {
        "study_id": study_id,
        "shape": list(volume.shape),
        "spacing": list(spacing),
        "num_slices": int(volume.shape[0]),
        "modality": modality,
    }
