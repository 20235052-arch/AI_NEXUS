"""
Computes clinical metrics (volume, voxel count, enlargement flag) from
a segmentation mask. Expects Dev D's AI/meshing pipeline to have already
saved a mask.npy file (same shape as the volume) into the study folder.
"""

from pathlib import Path

import numpy as np
from fastapi import APIRouter, HTTPException

router = APIRouter()

STORAGE = Path("storage")

# Rough adult splenomegaly threshold in cm^3, used only as a simple flag.
# Not a diagnostic claim -- just a placeholder for the demo/prototype.
SPLENOMEGALY_THRESHOLD_CM3 = 314


@router.get("/metrics/{study_id}")
def get_metrics(study_id: str):
    study_dir = STORAGE / study_id
    mask_path = study_dir / "mask.npy"
    spacing_path = study_dir / "spacing.npy"

    if not mask_path.exists():
        raise HTTPException(
            status_code=404,
            detail="No segmentation mask found yet for this study. "
                   "Run segmentation first (Dev D's pipeline).",
        )
    if not spacing_path.exists():
        raise HTTPException(status_code=404, detail="Study not found")

    mask = np.load(mask_path)
    spacing = np.load(spacing_path)

    voxel_volume_mm3 = float(spacing[0] * spacing[1] * spacing[2])
    spleen_voxels = int(np.sum(mask > 0))
    volume_mm3 = spleen_voxels * voxel_volume_mm3
    volume_cm3 = volume_mm3 / 1000

    return {
        "study_id": study_id,
        "volume_cm3": round(volume_cm3, 2),
        "voxel_count": spleen_voxels,
        "is_enlarged": volume_cm3 > SPLENOMEGALY_THRESHOLD_CM3,
    }
