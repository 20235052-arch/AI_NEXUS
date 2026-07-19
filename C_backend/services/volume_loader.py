"""
Handles loading medical imaging files (DICOM series or NIfTI files)
into a plain 3D numpy array, along with voxel spacing information.
"""

import pydicom
import nibabel as nib
import numpy as np
from pathlib import Path


def load_dicom_series(folder: Path):
    """
    Loads a folder of .dcm files into a single 3D numpy volume.
    Slices are sorted by their physical position so the volume
    is in correct anatomical order (not just filename order).
    """
    files = sorted(folder.glob("*.dcm"))
    if not files:
        raise ValueError(f"No .dcm files found in {folder}")

    slices = [pydicom.dcmread(f) for f in files]

    # Sort by physical Z position, not filename, since filenames
    # don't always match slice order.
    slices.sort(key=lambda s: float(s.ImagePositionPatient[2]))

    volume = np.stack([s.pixel_array for s in slices]).astype(np.float32)

    # CT scans store raw pixel values that need to be converted to
    # Hounsfield Units (HU) via RescaleSlope/RescaleIntercept tags.
    # MR scans have no standardized intensity scale and usually don't
    # have these tags at all -- default to a no-op (slope=1, intercept=0)
    # so MR volumes load as-is instead of crashing.
    intercept = float(getattr(slices[0], "RescaleIntercept", 0))
    slope = float(getattr(slices[0], "RescaleSlope", 1))
    volume = volume * slope + intercept

    # Modality tells us whether this is CT, MR, etc. -- useful for the
    # slice-windowing step downstream (MR needs different window values
    # than CT's Hounsfield-Unit-based windowing).
    modality = getattr(slices[0], "Modality", "UNKNOWN")

    # SliceThickness can be missing on some MR series; fall back to the
    # spacing between two consecutive slices if so.
    if hasattr(slices[0], "SliceThickness") and slices[0].SliceThickness:
        slice_thickness = float(slices[0].SliceThickness)
    elif len(slices) > 1:
        z0 = float(slices[0].ImagePositionPatient[2])
        z1 = float(slices[1].ImagePositionPatient[2])
        slice_thickness = abs(z1 - z0) or 1.0
    else:
        slice_thickness = 1.0

    spacing = (
        slice_thickness,
        float(slices[0].PixelSpacing[0]),
        float(slices[0].PixelSpacing[1]),
    )
    return volume, spacing, modality


def load_nifti(filepath: Path):
    """
    Loads a single .nii or .nii.gz file into a 3D numpy volume.
    NIfTI headers don't reliably store modality (CT vs MR), so we
    return "UNKNOWN" -- the frontend/slice windowing should fall back
    to a sensible default in that case.
    """
    img = nib.load(str(filepath))
    volume = img.get_fdata()
    # nibabel returns numpy.float32 here, which FastAPI's JSON encoder
    # cannot serialize directly -- cast to native Python float.
    spacing = tuple(float(v) for v in img.header.get_zooms())
    return volume, spacing, "UNKNOWN"