"""
Generates a realistic-looking sample spleen_probability.npy +
confidence_summary.json WITHOUT needing TotalSegmentator installed or
a real scan on hand.

Purpose: hand this to Member 4 as the "real sample output" for the
integration check -- so they can confirm they can load and use it
with zero extra glue code, before the real model is fully wired up.

Usage:
    python make_sample_output.py --study-id test123 --storage-dir storage
"""

import argparse
import json
from pathlib import Path

import numpy as np

from run_segmentation import build_confidence_summary


def generate_fake_probability_map(shape=(64, 128, 128)) -> np.ndarray:
    """
    Builds a plausible-looking probability map: a confident blob in the
    middle (simulating a clearly-detected spleen), with a fuzzy,
    lower-confidence boundary region -- similar to what a real model's
    output looks like (models are rarely 100% or 0% at organ edges).
    """
    prob_map = np.zeros(shape, dtype=np.float32)

    z, y, x = shape
    core = np.zeros(shape, dtype=np.float32)
    core[
        z // 3 : 2 * z // 3,
        y // 3 : 2 * y // 3,
        x // 3 : 2 * x // 3,
    ] = 1.0

    # Blur the sharp block into a soft gradient so edges have
    # realistic mid-range confidence values instead of a hard cutoff.
    from scipy.ndimage import gaussian_filter
    prob_map = gaussian_filter(core, sigma=4)
    prob_map = np.clip(prob_map, 0.0, 1.0).astype(np.float32)

    return prob_map


def run(study_id: str, storage_dir: Path):
    study_dir = storage_dir / study_id
    study_dir.mkdir(parents=True, exist_ok=True)

    prob_map = generate_fake_probability_map()

    prob_output_path = study_dir / "spleen_probability.npy"
    np.save(prob_output_path, prob_map)

    summary = build_confidence_summary(prob_map)
    summary_path = study_dir / "confidence_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))

    print(f"Sample output written to: {study_dir}")
    print(f" - {prob_output_path.name}  (shape={prob_map.shape}, dtype={prob_map.dtype})")
    print(f" - {summary_path.name}")
    print(f"Summary contents: {summary}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--study-id", default="sample_test")
    parser.add_argument("--storage-dir", default="storage")
    args = parser.parse_args()

    run(args.study_id, Path(args.storage_dir))
