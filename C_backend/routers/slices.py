"""
Serves individual 2D slices from an uploaded volume as PNG images,
so the frontend's slice-viewer slider can page through the scan.
"""

import io
from pathlib import Path

import numpy as np
from PIL import Image
from fastapi import APIRouter, HTTPException, Response

router = APIRouter()

STORAGE = Path("storage")


def window_image_ct(slice_2d, window_center=40, window_width=400):
    """
    Applies standard abdominal soft-tissue windowing to a raw HU slice
    so it displays with visible contrast instead of looking all gray/black.
    Default values (40, 400) are a common soft-tissue window; adjust if
    the spleen doesn't show up clearly. Only valid for CT, since it
    relies on the fixed Hounsfield Unit scale.
    """
    lo = window_center - window_width // 2
    hi = window_center + window_width // 2
    clipped = np.clip(slice_2d, lo, hi)
    normalized = ((clipped - lo) / (hi - lo) * 255).astype(np.uint8)
    return normalized


def window_image_mr(slice_2d, low_percentile=1, high_percentile=99):
    """
    MR has no fixed intensity scale (unlike CT's Hounsfield Units) --
    values vary by scanner, sequence, and patient. Percentile-based
    normalization adapts to whatever range this particular slice
    actually contains, which gives reasonable contrast for any MR series.
    """
    lo = np.percentile(slice_2d, low_percentile)
    hi = np.percentile(slice_2d, high_percentile)
    if hi <= lo:  # flat/empty slice edge case
        return np.zeros_like(slice_2d, dtype=np.uint8)
    clipped = np.clip(slice_2d, lo, hi)
    normalized = ((clipped - lo) / (hi - lo) * 255).astype(np.uint8)
    return normalized


def _load_volume(study_id: str):
    volume_path = STORAGE / study_id / "volume.npy"
    if not volume_path.exists():
        raise HTTPException(status_code=404, detail="Study not found")
    return np.load(volume_path)


def _load_modality(study_id: str) -> str:
    modality_path = STORAGE / study_id / "modality.txt"
    if not modality_path.exists():
        return "UNKNOWN"
    return modality_path.read_text().strip()


@router.get("/slices/{study_id}/count")
def get_slice_count(study_id: str):
    """Returns how many slices exist, so the frontend slider knows its range."""
    volume = _load_volume(study_id)
    return {"num_slices": int(volume.shape[0])}


@router.get("/slices/{study_id}/{index}")
def get_slice(study_id: str, index: int):
    """Returns a single slice, windowed and encoded as a PNG image."""
    volume = _load_volume(study_id)

    if index < 0 or index >= volume.shape[0]:
        raise HTTPException(
            status_code=400,
            detail=f"Index out of range. Must be 0-{volume.shape[0] - 1}",
        )

    slice_2d = volume[index]
    modality = _load_modality(study_id)

    # CT has a fixed intensity scale (Hounsfield Units) so a fixed
    # window works well. MR (and anything unrecognized) gets adaptive
    # percentile-based windowing instead, since MR intensities aren't
    # standardized across scanners/sequences.
    if modality == "CT":
        img_array = window_image_ct(slice_2d)
    else:
        img_array = window_image_mr(slice_2d)

    img = Image.fromarray(img_array)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")
