"""
Member 3 -- Segmentation with per-voxel probabilities.

Runs TotalSegmentator on a CT/MR volume, keeping the raw per-voxel
confidence instead of collapsing straight to a binary yes/no mask.

OUTPUT FORMAT (agreed with Member 4 before writing this):
    storage/{study_id}/spleen_probability.npy
        - numpy array, dtype float32
        - same shape as storage/{study_id}/volume.npy
        - values 0.0-1.0 = probability that voxel is spleen

    storage/{study_id}/confidence_summary.json
        - small JSON with headline stats (see build_confidence_summary)

Usage:
    python run_segmentation.py --study-id <id> --storage-dir storage
"""

import argparse
import json
import subprocess
from pathlib import Path

import numpy as np


def run_totalsegmentator(input_nifti: Path, output_dir: Path) -> Path:
    """
    Runs TotalSegmentator restricted to the spleen ROI, with probability
    output enabled. Restricting to a single ROI keeps runtime reasonable
    on CPU (confirmed via real testing: ~90 seconds per scan on an
    8-core/16-thread CPU, after the one-time model download).

    Note: --roi_subset only filters which mask gets SAVED as the final
    output -- the underlying model still predicts all classes
    internally, so the probability array will have one layer per class
    (118 total: background + 117 structures), not just 2. See
    extract_spleen_probability_map() for how the spleen layer is
    selected from that full array.

    Returns the path to the saved probabilities .npz file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    probs_path = output_dir / "raw_probabilities.npz"
    # TotalSegmentator's --save_probabilities writes to this path via a
    # plain file copy -- it does NOT create the destination folder
    # itself, so it must already exist or the run fails partway through.
    probs_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "TotalSegmentator",
        "-i", str(input_nifti),
        "-o", str(output_dir),
        "--roi_subset", "spleen",
        "--fast",
        "--save_probabilities", str(probs_path),
    ]
    subprocess.run(cmd, check=True)

    if not probs_path.exists():
        raise RuntimeError(
            f"TotalSegmentator did not produce {probs_path} -- "
            "check the command above ran correctly."
        )
    return probs_path


def extract_spleen_probability_map(probs_npz_path: Path) -> np.ndarray:
    """
    Loads the raw softmax output and pulls out just the spleen class's
    per-voxel probability as a plain float32 array.
    """
    data = np.load(probs_npz_path)
    # nnU-Net/TotalSegmentator typically stores this under a single key;
    # fall back to the first array in the file if the key name differs.
    key = "probabilities" if "probabilities" in data else data.files[0]
    probs = data[key]

    # Expected shape: (num_classes, Z, Y, X). Even with --roi_subset,
    # TotalSegmentator's underlying model still internally predicts all
    # 117 structures + background (confirmed via real testing: shape
    # was (118, Z, Y, X), not (2, Z, Y, X) as originally assumed).
    # --roi_subset only filters which mask gets SAVED, not what the
    # model computes. Class ID 1 = spleen in TotalSegmentator's
    # official "total" task label map (confirmed against their
    # map_to_binary.py source), regardless of how many other classes
    # are present in the array.
    if probs.ndim != 4:
        raise ValueError(
            f"Expected a 4D array (classes, Z, Y, X), got shape {probs.shape}"
        )
    SPLEEN_CLASS_INDEX = 1
    spleen_prob_map = probs[SPLEEN_CLASS_INDEX].astype(np.float32)
    return spleen_prob_map


def build_confidence_summary(spleen_prob_map: np.ndarray, threshold: float = 0.5) -> dict:
    """
    Computes the headline stats Member 4 (and the frontend Trust Panel)
    need, so they don't have to re-derive everything from the raw array
    themselves. Kept intentionally small and flat.
    """
    predicted_mask = spleen_prob_map > threshold
    predicted_voxels = spleen_prob_map[predicted_mask]

    if predicted_voxels.size == 0:
        return {
            "overall_score": 0.0,
            "overall_score_percent": 0,
            "threshold_used": threshold,
            "predicted_voxel_count": 0,
            "low_confidence_voxel_count": 0,
        }

    overall_score = float(np.mean(predicted_voxels))
    low_confidence_voxel_count = int(np.sum(predicted_mask & (spleen_prob_map < 0.7)))

    return {
        "overall_score": round(overall_score, 4),
        "overall_score_percent": round(overall_score * 100),
        "threshold_used": threshold,
        "predicted_voxel_count": int(np.sum(predicted_mask)),
        "low_confidence_voxel_count": low_confidence_voxel_count,
    }


def run(study_id: str, storage_dir: Path):
    study_dir = storage_dir / study_id
    input_nifti = study_dir / "input_for_segmentation.nii.gz"

    if not input_nifti.exists():
        raise FileNotFoundError(
            f"Expected input volume at {input_nifti}. "
            "Convert storage/{study_id}/volume.npy to NIfTI first if needed."
        )

    seg_output_dir = study_dir / "segmentation_raw"
    probs_npz = run_totalsegmentator(input_nifti, seg_output_dir)

    spleen_prob_map = extract_spleen_probability_map(probs_npz)

    # --- Write the agreed output format ---
    prob_output_path = study_dir / "spleen_probability.npy"
    np.save(prob_output_path, spleen_prob_map)

    summary = build_confidence_summary(spleen_prob_map)
    summary_path = study_dir / "confidence_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))

    print(f"Saved: {prob_output_path}")
    print(f"Saved: {summary_path}")
    print(f"Summary: {summary}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--study-id", required=True)
    parser.add_argument("--storage-dir", default="storage")
    args = parser.parse_args()

    run(args.study_id, Path(args.storage_dir))
